from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from flask_batteries_included.config import is_production_environment
from flask_batteries_included.helpers import schema
from flask_batteries_included.helpers.error_handler import EntityNotFoundException
from flask_batteries_included.helpers.timestamp import (
    parse_datetime_to_iso8601,
    parse_iso8601_to_datetime,
    parse_iso8601_to_datetime_typesafe,
    split_timestamp,
)
from flask_batteries_included.sqldb import (
    db,
    generate_uuid,
    validate_model,
    validate_models,
)
from she_logging import logger
from sqlalchemy.engine import Result, Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import text

from gdm_bg_readings_api import trustomer
from gdm_bg_readings_api.blueprint_api import counts_alerting, percentages_alerting
from gdm_bg_readings_api.blueprint_api.exceptions import DuplicateReadingException
from gdm_bg_readings_api.blueprint_api.publish import (
    publish_abnormal_reading,
    publish_audit_message,
    publish_patient_alert,
)
from gdm_bg_readings_api.models.dose import Dose
from gdm_bg_readings_api.models.hba1c_reading import Hba1cReading
from gdm_bg_readings_api.models.hba1c_target import Hba1cTarget
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.patient_alert import PatientAlert
from gdm_bg_readings_api.models.prandial_tag import PrandialTag
from gdm_bg_readings_api.models.reading import Reading
from gdm_bg_readings_api.models.reading_banding import ReadingBanding  # noqa
from gdm_bg_readings_api.models.reading_metadata import ReadingMetadata
from gdm_bg_readings_api.trustomer import AlertsSystem
from gdm_bg_readings_api.utils.datetime_utils import (
    calculate_last_midnight,
    calculate_midnight_plus_days,
)

UPDATING_READING_WITH_UUID_MESSAGE = "Updating reading with UUID %s"


def create_reading(
    patient_id: str,
    reading_data: Dict,
    compact: bool = False,
) -> Dict:
    doses, comment, reading_metadata, reading, banding_id = _validate_reading(
        reading_data=reading_data
    )

    prandial_tag = _prandial_tag_or_default(reading_data.pop("prandial_tag"))
    measured_timestamp, measured_timezone = split_timestamp(
        reading_data.pop("measured_timestamp")
    )
    blood_glucose_value = reading_data.pop("blood_glucose_value")
    units = reading_data.pop("units")

    patient = Patient.query.get(patient_id)
    if not patient:
        logger.debug("Creating a new patient with UUID %s", patient_id)
        patient = Patient(uuid=patient_id)
        db.session.add(patient)
        db.session.flush()

    reading = Reading(
        uuid=generate_uuid(),
        patient_id=patient_id,
        doses=doses,
        comment=comment,
        prandial_tag=prandial_tag,
        reading_metadata=reading_metadata,
        measured_timestamp=measured_timestamp,
        measured_timezone=measured_timezone,
        blood_glucose_value=blood_glucose_value,
        units=units,
        reading_banding_id=banding_id,
    )
    db.session.add(reading)

    if counts_alerting.is_reading_in_snooze_period(reading, patient):
        reading.snoozed = True

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        reading = Reading.query.filter_by(
            blood_glucose_value=blood_glucose_value,
            units=units,
            measured_timestamp=measured_timestamp,
            measured_timezone=measured_timezone,
            patient_id=patient_id,
        ).first()

        publish_audit_message(
            event_type="duplicate_reading",
            event_data={
                "patient_id": patient_id,
                "duplicate_reading_id": reading.uuid,
            },
        )

        headers = {"Location": f"/gdm/v1/patient/{patient_id}/reading/{reading.uuid}"}
        raise DuplicateReadingException(
            message="Duplicate reading found",
            extra={"reading_id": reading.uuid},
            headers=headers,
        )

    if counts_alerting.reading_could_trigger_alert(reading):
        publish_abnormal_reading(reading=reading)

    logger.debug("Reading created with UUID %s", reading.uuid)
    return reading.to_dict(compact=compact)


def create_reading_v1(
    patient_id: str,
    reading_data: Dict,
    compact: bool = False,
) -> Dict:
    # fixme: https://sensynehealth.atlassian.net/browse/PLAT-872
    logger.debug("Creating a reading for patient with UUID %s", patient_id)
    doses, comment, reading_metadata, reading, banding_id = _validate_reading(
        reading_data=reading_data
    )
    return _create_reading_from_parts(
        patient_id=patient_id,
        doses=doses,
        comment=comment,
        reading_metadata=reading_metadata,
        reading_data=reading,
        banding_id=banding_id,
        compact=compact,
    )


def get_reading_by_uuid(patient_uuid: str, reading_uuid: str) -> Dict:
    logger.debug("Getting reading by UUID %s", reading_uuid)
    reading: Reading = (
        Reading.query.options(
            joinedload(Reading.prandial_tag),
            joinedload(Reading.doses),
            joinedload(Reading.reading_metadata),
            joinedload(Reading.reading_banding),
            joinedload(Reading.amber_alert),
            joinedload(Reading.red_alert),
        )
        .filter_by(patient_id=patient_uuid, uuid=reading_uuid)
        .first_or_404()
    )
    return reading.to_dict()


def retrieve_readings_for_patient_with_tag(
    patient_id: str,
    prandial_tag_value: Optional[str] = None,
    lazy: bool = False,
) -> Iterable[Dict]:
    logger.debug("Retrieving readings for patient with UUID %s", patient_id)

    q = Reading.query.options(
        joinedload(Reading.prandial_tag),
        joinedload(Reading.doses),
        joinedload(Reading.reading_metadata),
        joinedload(Reading.reading_banding),
        joinedload(Reading.amber_alert),
        joinedload(Reading.red_alert),
    )

    if prandial_tag_value is None:
        readings = (
            q.filter_by(patient_id=patient_id)
            .order_by(Reading.measured_timestamp.desc())
            .all()
        )
    else:
        # int() will throw a ValueError (HTTP 400) if the prandial tag isn't an int.
        prandial_tag_int: int = int(prandial_tag_value)
        prandial_tag = PrandialTag.query.filter_by(value=prandial_tag_int).first()

        if prandial_tag is None:
            raise EntityNotFoundException("Invalid prandial tag value supplied")
        else:
            readings = (
                q.filter_by(patient_id=patient_id, prandial_tag_id=prandial_tag.uuid)
                .order_by(Reading.measured_timestamp.desc())
                .all()
            )

    logger.debug(
        "Found %d readings for patient with UUID %s", len(readings), patient_id
    )

    if lazy:
        return (reading.to_dict() for reading in readings)
    else:
        return [reading.to_dict() for reading in readings]


def retrieve_readings_for_period(
    days: int, compact: bool = True
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves all readings for a given period of days from the database. Returns a map of
    patient UUID to list of readings.
    """
    readings: List[Reading] = _get_recent_readings(days=days)
    patient_readings_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for reading in readings:
        patient_readings_map[reading.patient_id].append(
            reading.to_dict(compact=compact)
        )
    return dict(patient_readings_map)


def _get_recent_readings(days: int) -> List[Reading]:
    """
    Ideally we would just query the readings table, filtering using the earliest allowed
    measured timestamp. However, the database splits the timestamp into raw and timezone
    offset, so we must instead:
      - Get all readings filtered by earliest allowed measured timestamp, including a buffer
        of one day to allow for timezone offset
      - Order readings by measured timestamp
      - Remove all readings whose timezone-aware timestamp is earlier than the original
        earliest allowed timestamp
    """
    earliest_allowed: datetime = datetime.now(tz=timezone.utc) - timedelta(days=days)
    earliest_selected: datetime = earliest_allowed - timedelta(days=1)
    readings: List[Reading] = (
        Reading.query.options(
            joinedload(Reading.doses),
            joinedload(Reading.reading_banding),
            joinedload(Reading.amber_alert),
            joinedload(Reading.red_alert),
        )
        .filter(Reading.measured_timestamp > earliest_selected)
        .order_by(Reading.measured_timestamp.desc())
        .all()
    )
    return [r for r in readings if r.get_measured_timestamp() > earliest_allowed]


def retrieve_statistics_for_period(
    days: int, compact: bool = True
) -> Dict[str, Dict[str, Dict]]:
    """
    Retrieves the minimum and maximum readings recorded by each patient for a
    given period of days.
    """
    readings: List[Reading] = _get_recent_readings(days=days)
    patient_readings_map: Dict[str, List[Reading]] = defaultdict(list)
    for reading in readings:
        patient_readings_map[reading.patient_id].append(reading)
    stats_map: Dict[str, Dict] = {}
    for patient_uuid, readings in patient_readings_map.items():
        readings.sort(key=lambda r: r.blood_glucose_value)
        stats_map[patient_uuid] = {
            "min_reading": readings[0].to_dict(compact=compact),
            "max_reading": readings[-1].to_dict(compact=compact),
            "readings_count": len(readings),
            "readings_count_banding_normal": sum(
                1
                for r in readings
                if r.reading_banding_id == "BG-READING-BANDING-NORMAL"
            ),
        }
    return stats_map


def retrieve_latest_reading_for_patient(patient_id: str) -> Optional[Dict]:
    logger.debug("Retrieving latest reading for patient with UUID %s", patient_id)

    reading: Reading = (
        Reading.query.filter_by(patient_id=patient_id)
        .order_by(Reading.measured_timestamp.desc())
        .first_or_404()
    )

    return reading.to_dict() if reading else None


def retrieve_first_reading_for_patient(patient_id: str) -> Optional[Dict]:
    logger.debug("Retrieving first reading for patient with UUID %s", patient_id)

    reading: Reading = (
        Reading.query.filter_by(patient_id=patient_id)
        .order_by(Reading.measured_timestamp.asc())
        .first_or_404()
    )

    return reading.to_dict() if reading else None


def retrieve_patient_summaries(patient_ids: List[str]) -> Dict[str, Dict]:
    """Returns some per-patient summary information"""
    logger.debug("Retrieving patient summaries")

    if len(patient_ids) == 0:
        logger.debug("Client asked for 0 summaries - bailing out")
        return {}

    logger.debug("Getting %d patient summaries", len(patient_ids))

    resp = _query_patient_summaries_from_db(patient_ids)

    # Adding in any patient IDs that didn't come back from the DB as empty results
    for missing_id in set(patient_ids) - set(resp.keys()):
        resp[str(missing_id)] = {}

    logger.debug("Returning patient summaries")

    return resp


def update_reading(patient_id: str, reading_id: str, reading_data: Dict) -> Dict:
    logger.debug(UPDATING_READING_WITH_UUID_MESSAGE, reading_id)
    reading = Reading.query.filter_by(
        patient_id=patient_id, uuid=reading_id
    ).first_or_404()

    # Update comment
    comment = reading_data.get("comment", None)
    if comment is not None:
        reading.comment = comment

    # Update prandial tag
    prandial_tag = reading_data.get("prandial_tag", None)
    if prandial_tag is not None:
        prandial_tag_value = prandial_tag.get("value", None)

        if prandial_tag_value is None:
            raise KeyError("Prandial tag patch did not contain a value")
        elif not isinstance(prandial_tag_value, int):
            raise TypeError("Prandial tag must contain a 'value' field of type integer")

        selected_prandial_tag = (
            PrandialTag.query.filter_by(value=prandial_tag_value).first() or None
        )
        if selected_prandial_tag is None:
            raise ValueError("Prandial tag supplied with invalid value")

        reading.prandial_tag = selected_prandial_tag

    # Update banding
    updated_banding_id: Optional[str] = reading_data.get("banding_id", None)
    if updated_banding_id is not None:
        reading.reading_banding_id = reading_data["banding_id"]
        if reading.reading_banding_id == "BG-READING-BANDING-NORMAL":
            reading.red_alert = None

    # Update doses
    doses = reading_data.get("doses", None)
    if doses is not None:
        existing_dose_ids = [d.uuid for d in reading.doses]
        # Loop through doses to add or update
        for dose in doses:

            # Update
            if "uuid" in dose:
                if dose["uuid"] in existing_dose_ids:
                    existing_dose_ids.remove(dose["uuid"])

                    existing_dose = Dose.query.filter_by(uuid=dose["uuid"]).first()

                    if "medication_id" in dose:
                        existing_dose.medication_id = dose["medication_id"]
                    if "amount" in dose:
                        existing_dose.amount = dose["amount"]

                    db.session.add(existing_dose)
                else:
                    raise EntityNotFoundException(
                        "Dose UUID '{}' does not relate to patient '{}' and reading '{}'".format(
                            dose["uuid"], patient_id, reading_id
                        )
                    )

            # Insert any that have no UUID
            else:
                new_dose = Dose(
                    uuid=generate_uuid(),
                    reading_id=reading.uuid,
                    medication_id=dose["medication_id"],
                    amount=dose["amount"],
                )
                db.session.add(new_dose)

        # Remove any from the reading object's doses list
        reading.doses = [d for d in reading.doses if d.uuid not in existing_dose_ids]

        # Delete any in the database that weren't supplied in the patch call
        for unneeded_dose_id in existing_dose_ids:
            dose_to_delete = Dose.query.filter_by(uuid=unneeded_dose_id).first()

            # Add it to the session to be deleted from the database
            db.session.delete(dose_to_delete)
    db.session.commit()

    updated_reading: Reading = Reading.query.filter_by(
        patient_id=patient_id, uuid=reading_id
    ).first()

    if counts_alerting.reading_could_trigger_alert(reading) and (
        prandial_tag is not None or updated_banding_id is not None
    ):
        publish_abnormal_reading(reading=updated_reading)

    return updated_reading.to_dict()


def add_dose_to_reading(patient_id: str, reading_id: str, dose_data: Dict) -> Dict:
    logger.debug(UPDATING_READING_WITH_UUID_MESSAGE, reading_id)
    reading = Reading.query.filter_by(
        patient_id=patient_id, uuid=reading_id
    ).first_or_404()

    medication_id = dose_data.pop("medication_id")
    amount = dose_data.pop("amount")

    dose = Dose(
        uuid=generate_uuid(),
        reading_id=reading.uuid,
        medication_id=medication_id,
        amount=amount,
    )

    db.session.add(dose)
    db.session.commit()

    return dose.to_dict()


# TODO: this MUST filter on patient ID as well
def update_dose_on_reading(
    patient_id: str, reading_id: str, dose_id: str, dose_data: Dict
) -> Dict:

    Dose.query.filter_by(uuid=dose_id, reading_id=reading_id).update(dose_data)

    db.session.commit()

    return (
        Dose.query.filter_by(uuid=dose_id, reading_id=reading_id)
        .first_or_404()
        .to_dict()
    )


def _validate_reading(reading_data: Optional[Dict] = None) -> Tuple:
    # This is shared logic for create_reading and create_bulk_readings endpoints.
    reading: Dict = schema.post(json_in=reading_data, **Reading.schema())
    doses: Optional[List[Dict]] = validate_models(reading.pop("doses"), Dose)
    comment: Optional[str] = reading.pop("comment", None)
    reading_metadata: Optional[Dict] = reading.pop("reading_metadata", None)
    banding_id: str = reading.pop("banding_id")

    if reading_metadata != {}:
        reading_metadata = validate_model(
            schema.post(json_in=reading_metadata, **ReadingMetadata.schema()),
            ReadingMetadata,
        )
    else:
        reading_metadata = None
    return doses, comment, reading_metadata, reading, banding_id


def _create_reading_from_parts(
    patient_id: str,
    doses: Optional[List[Dict]],
    comment: Optional[str],
    reading_metadata: Optional[Dict],
    reading_data: Dict,
    banding_id: str,
    publish: bool = True,
    compact: bool = False,
) -> Dict:
    # fixme: https://sensynehealth.atlassian.net/browse/PLAT-872
    logger.debug(
        "Creating reading from parts",
        extra={"patient_id": patient_id},
    )
    prandial_tag = _prandial_tag_or_default(reading_data.pop("prandial_tag"))
    measured_timestamp, measured_timezone = split_timestamp(
        reading_data.pop("measured_timestamp")
    )

    blood_glucose_value = reading_data.pop("blood_glucose_value")
    units = reading_data.pop("units")

    # Create associated Patient, if not there
    patient = Patient.query.get(patient_id)
    if not patient:
        patient = Patient(uuid=patient_id)
        db.session.add(patient)
        db.session.flush()
    logger.debug("Preparing to create a new reading record")

    reading = Reading(
        uuid=generate_uuid(),
        patient_id=patient_id,
        doses=doses,
        comment=comment,
        prandial_tag=prandial_tag,
        reading_metadata=reading_metadata,
        measured_timestamp=measured_timestamp,
        measured_timezone=measured_timezone,
        blood_glucose_value=blood_glucose_value,
        units=units,
        reading_banding_id=banding_id,
    )
    db.session.add(reading)

    if counts_alerting.is_reading_in_snooze_period(reading, patient):
        reading.snoozed = True
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        reading = Reading.query.filter_by(
            blood_glucose_value=blood_glucose_value,
            units=units,
            measured_timestamp=measured_timestamp,
            measured_timezone=measured_timezone,
            patient_id=patient_id,
        ).first()
        publish_audit_message(
            event_type="duplicate_reading",
            event_data={
                "patient_id": patient_id,
                "duplicate_reading_id": reading.uuid,
            },
        )
    else:
        # If we are in a prod environment, always publish.
        publish = publish or is_production_environment()
        if publish and counts_alerting.reading_could_trigger_alert(reading):
            publish_abnormal_reading(reading=reading)

        logger.debug("Finished creating reading")

    return reading.to_dict(compact=compact)


def _create_summary_orm_from_row(row: Row) -> Tuple[Reading, Patient]:
    """Takes a SQLAlchemy Result containing reading+patient rows and returns ORM objects of same."""
    reading = Reading()
    patient = Patient()

    for k in row.keys():
        if hasattr(reading, k):
            setattr(reading, k, getattr(row, k))
        elif hasattr(patient, k):
            setattr(patient, k, getattr(row, k))

    return reading, patient


def _query_patient_summaries_from_db(patient_ids: List[str]) -> Dict[str, Dict]:
    s = db.session

    # Due to the performance concerns,
    # this uses a hand-crafted a SQL query rather than the ORM
    # The DISTINCT works because we need only the top result
    # from the readings table per-patient
    sql_query = text(
        """
        SELECT patient.*, reading.*
        FROM patient
        INNER JOIN (
        SELECT DISTINCT ON (patient_id) *
        FROM reading
        WHERE reading.patient_id IN :patient_ids
        ORDER BY reading.patient_id, reading.measured_timestamp DESC
        ) AS reading ON patient.uuid = reading.patient_id
        WHERE patient.uuid IN :patient_ids
        """
    )

    # Run the SQL query
    result: Result = s.execute(sql_query, {"patient_ids": tuple(patient_ids)})

    resp = {}

    # Unpack the results into dictionaries via standard to_dict() methods
    for row in result:
        reading, patient = _create_summary_orm_from_row(row)

        reading_dict = reading.to_dict(compact=True)
        patient_dict = patient.to_dict()
        patient_dict["latest_reading"] = reading_dict

        resp[reading_dict["patient_id"]] = patient_dict

    return resp


def _prandial_tag_or_default(prandial_tag_data: Optional[Dict]) -> PrandialTag:
    # Retrieve prandial tag given UUID or value.
    if prandial_tag_data is not None and prandial_tag_data != {}:
        return _get_prandial_tag(prandial_tag_data)

    # Fall back to default.
    prandial_tag = PrandialTag.query.filter_by(value=0).first()
    if prandial_tag is None:
        raise RuntimeError("Prandial tag table is not populated")
    return prandial_tag


def _get_prandial_tag(prandial_tag_data: Dict) -> PrandialTag:
    # Retrieves a prandial tag given a UUID or a value.
    if "uuid" in prandial_tag_data and isinstance(prandial_tag_data["uuid"], str):
        return PrandialTag.query.filter_by(
            uuid=prandial_tag_data["uuid"]
        ).first_or_404()
    if "value" in prandial_tag_data and isinstance(prandial_tag_data["value"], int):
        return PrandialTag.query.filter_by(
            value=prandial_tag_data["value"]
        ).first_or_404()
    raise KeyError("Prandial tag must contain a valid 'value' or 'uuid' field")


def process_counts_alerts_for_reading(reading_id: str) -> Dict:
    reading = Reading.query.filter_by(uuid=reading_id).first_or_404()

    # Abort if the alerts system is "percentages".
    alerts_system: AlertsSystem = trustomer.get_alerts_system()
    if alerts_system == AlertsSystem.PERCENTAGES:
        logger.info(
            "Process alerts for reading ignored: alerts system is '%s'",
            alerts_system.value,
        )
        return reading.to_dict()

    logger.debug("Adding alerts to reading with UUID %s", reading_id)
    # alerts cannot be triggered during a "snooze" period
    if reading.snoozed:
        return reading.to_dict()
    logger.debug("Reading not in snooze period")

    # amber alerts are only generated if the reading is in the most recent 2
    # days of readings, it is abnormal and there are 1 or more other abnormal
    # readings
    reading = counts_alerting.process_amber_alertable_readings(reading)

    # red alerts are only generated on readings that are three in a row
    red_alertable_readings = counts_alerting.get_alertable_readings(reading)
    if not red_alertable_readings:
        logger.debug("No red alertable readings found")
        # Commit to database and early return
        db.session.commit()
        return reading.to_dict()

    # alerts needed!
    logger.debug("Red alertable readings found")
    for alertable_reading in red_alertable_readings:
        logger.debug("Creating red alert for reading")
        counts_alerting.add_red_alert_to_reading(
            red_alertable_readings[alertable_reading]
        )

    logger.debug("Setting red alert for patient %s", reading.patient.uuid)
    reading.patient.current_red_alert = True

    logger.debug("Publishing reading red alert message for reading %s", reading.uuid)
    publish_patient_alert(
        patient_uuid=reading.patient_id, alert_type=PatientAlert.AlertType.COUNTS_RED
    )

    db.session.commit()

    return reading.to_dict()


def clear_alerts_for_patient(patient_id: str) -> Dict:
    patient = Patient.query.filter(Patient.uuid == patient_id).first()
    if not patient:
        raise EntityNotFoundException("No patient found with UUID " + patient_id)

    # Clear alert flags on patient.
    logger.info("Clearing alerts for patient with UUID %s", patient_id)
    patient.current_red_alert = False
    patient.current_amber_alert = False

    # Activate alerts snooze on patient.
    logger.debug("Activating snooze for patient with UUID %s", patient_id)
    time_now: datetime = datetime.utcnow().replace(tzinfo=timezone.utc)
    snooze_duration_interval_days: int = trustomer.get_alerts_snooze_duration_days()
    snooze_start_iso8601: Optional[str] = parse_datetime_to_iso8601(time_now)
    snooze_end_iso8601: Optional[str] = parse_datetime_to_iso8601(
        calculate_midnight_plus_days(
            base=time_now, offset=snooze_duration_interval_days
        )
    )
    patient.set_suppress_reading_alerts_from(snooze_start_iso8601)
    patient.set_suppress_reading_alerts_until(snooze_end_iso8601)
    logger.debug("Snoozed from %s until %s", snooze_start_iso8601, snooze_end_iso8601)

    # Mark active percentages alerts as dismissed.
    percentages_alerting.dismiss_active_alerts_for_patient(patient_id=patient.uuid)

    # Mark active counts alerts as dismissed.
    counts_alerting.dismiss_active_alerts_for_patient(patient_id=patient.uuid)

    db.session.commit()

    return {
        "completed": True,
        "suppress_reading_alerts_from": patient.suppress_reading_alerts_from,
        "suppress_reading_alerts_until": patient.suppress_reading_alerts_until,
    }


def get_patient(patient_id: str) -> Dict:
    p: Patient = Patient.query.filter_by(uuid=patient_id).first_or_404()
    return p.to_dict()


def process_activity_alerts_for_patient(patient_id: str, readings_plans: List) -> Dict:
    """
    Given a patient UUID and a set of reading plans for that patient:
    - Checks that the patient exists
    - Counts the readings during the past 7 calendar days
    - Calculates the number of expected readings, given the reading plans
    - Checks whether at least two thirds of the expected number of readings are present
    - Updates the patient alert flag accordingly
    - Updates the activity alert records for that patient
    - If there is an activity alert, publishes it to RabbitMQ
    """
    logger.info("Processing activity alert for patient with UUID %s", patient_id)
    patient: Patient = Patient.query.filter(Patient.uuid == patient_id).first()
    if not patient:
        raise EntityNotFoundException("No patient found with UUID " + patient_id)
    # Count readings from previous 7 days
    to_datetime: datetime = calculate_last_midnight()
    from_datetime: datetime = to_datetime - timedelta(days=7)
    recent_readings_count: int = patient.readings.filter(
        Reading.measured_timestamp >= from_datetime
    ).count()

    # Calculate expected readings
    total_expected_readings: float = (
        percentages_alerting.calculate_expected_reading_count(
            plans=readings_plans, start_date=from_datetime, end_date=to_datetime
        )
    )

    # Alert if number of taken readings is less than 2/3s of expected
    alert_now: bool = recent_readings_count < (2 / 3 * total_expected_readings)
    logger.debug(
        "Patient %s activity alert processing result: %s",
        patient.uuid,
        alert_now,
        extra={
            "actual_readings": recent_readings_count,
            "expected_readings": total_expected_readings,
        },
    )
    patient.current_activity_alert = alert_now
    percentages_alerting.update_alerts_for_patient(
        patient=patient,
        alert_type=PatientAlert.AlertType.ACTIVITY_GREY,
        alert_now=alert_now,
    )

    db.session.commit()
    return {"alert_now": alert_now, **patient.to_dict()}


def process_percentages_alerts(alerts_data: Dict) -> None:
    """
    Given a map of alerts (where keys are patient UUIDs, and values are alert statuses):
    - Checks that all of the patients exist
    - Checks whether alerts have been snoozed for each patient
    - Updates the red/amber alert status for each patient accordingly
    - Updates the red/amber alert records for each patient
    """
    logger.info("Processing percentages alerts for %d patients", len(alerts_data))
    requested_uuids: Set[str] = set(alerts_data.keys())
    patients: List[Patient] = Patient.query.filter(
        Patient.uuid.in_(requested_uuids)
    ).all()
    retrieved_uuids: Set[str] = {p.uuid for p in patients}

    if len(retrieved_uuids) < len(requested_uuids):
        missing_uuids: Set[str] = requested_uuids - retrieved_uuids
        raise EntityNotFoundException(
            "Patient not found with UUID(s): %s", missing_uuids
        )

    # At this point, we know that every patient UUID in alerts_data is unique, and
    # has a corresponding entry in the database.

    for patient_uuid, alerts_status in alerts_data.items():
        logger.info("Processing percentages alerts for patient %s", patient_uuid)
        patient = next(p for p in patients if p.uuid == patient_uuid)
        current_red_alert: bool = alerts_status["red_alert"]
        current_amber_alert: bool = alerts_status["amber_alert"]
        if percentages_alerting.is_patient_in_snooze_period(patient):
            # If alerts are snoozed, patient should not have alerts.
            logger.debug("Alerts are snoozed for patient %s", patient_uuid)
            patient.current_red_alert = False
            patient.current_amber_alert = False
        else:
            # Otherwise, update the alerts on the patient.
            logger.debug("Alert status set for patient %s", patient_uuid)
            patient.current_red_alert = current_red_alert
            patient.current_amber_alert = current_amber_alert

        # Update alert records for this patient (regardless of snooze status).
        percentages_alerting.update_alerts_for_patient(
            patient=patient,
            alert_type=PatientAlert.AlertType.PERCENTAGES_RED,
            alert_now=current_red_alert,
        )
        percentages_alerting.update_alerts_for_patient(
            patient=patient,
            alert_type=PatientAlert.AlertType.PERCENTAGES_AMBER,
            alert_now=current_amber_alert,
        )

    db.session.commit()
    logger.debug(
        "Finished processing percentages alerts for %d patients", len(alerts_data)
    )


def create_hba1c_reading(patient_uuid: str, reading_data: Dict) -> Dict:
    logger.debug("Creating a Hba1c reading for patient with UUID %s", patient_uuid)
    hba1c_reading: Dict = schema.post(json_in=reading_data, **Hba1cReading.schema())

    # Create associated Patient, if not there
    patient = Patient.query.get(patient_uuid)
    if not patient:
        patient = Patient(uuid=patient_uuid)
        db.session.add(patient)
        db.session.flush()
    logger.debug("Preparing to create a new Hba1c reading record")

    measured_timestamp = parse_iso8601_to_datetime(reading_data["measured_timestamp"])

    # Create Reading
    hba1c_reading = Hba1cReading(
        uuid=generate_uuid(),
        patient_id=patient_uuid,
        measured_timestamp=measured_timestamp,
        value=reading_data["value"],
        units=reading_data["units"],
    )

    db.session.add(hba1c_reading)
    db.session.commit()

    logger.debug("Finished creating Hba1c reading")
    return hba1c_reading.to_dict()


def retrieve_hba1c_readings_for_patient(
    patient_uuid: str,
) -> Iterable[Dict]:
    logger.debug("Retrieving Hba1c readings for patient with UUID %s", patient_uuid)

    hba1c_readings = (
        Hba1cReading.query.filter_by(patient_id=patient_uuid)
        .order_by(Hba1cReading.measured_timestamp.desc())
        .all()
    )

    logger.debug(
        "Found %d Hba1c readings for patient with UUID %s",
        len(hba1c_readings),
        patient_uuid,
    )

    return [reading.to_dict() for reading in hba1c_readings]


def get_hba1c_reading_by_uuid(patient_uuid: str, hba1c_reading_uuid: str) -> Dict:
    logger.debug("Getting Hba1c reading with UUID %s", hba1c_reading_uuid)
    reading: Hba1cReading = Hba1cReading.query.filter_by(
        patient_id=patient_uuid, uuid=hba1c_reading_uuid
    ).first_or_404()
    return reading.to_dict()


def update_hba1c_reading(
    patient_uuid: str, hba1c_reading_uuid: str, reading_data: Dict
) -> Dict:
    logger.debug("Updating Hba1c reading with UUID %s", hba1c_reading_uuid)

    reading_db: Hba1cReading = Hba1cReading.query.filter_by(
        patient_id=patient_uuid, uuid=hba1c_reading_uuid
    ).first_or_404()

    for property_to_update in reading_data:
        reading_db.set_property(property_to_update, reading_data[property_to_update])

    db.session.commit()
    return reading_db.to_dict()


def delete_hba1c_reading(patient_uuid: str, hba1c_reading_uuid: str) -> Dict:
    logger.debug("Deleting Hba1c reading with UUID %s", hba1c_reading_uuid)
    reading: Hba1cReading = Hba1cReading.query.filter_by(
        patient_id=patient_uuid, uuid=hba1c_reading_uuid
    ).first_or_404()
    reading.delete()
    db.session.commit()
    return reading.to_dict()


def create_hba1c_target(patient_uuid: str, target_data: Dict) -> Dict:
    logger.debug("Creating a Hba1c target for patient with UUID %s", patient_uuid)
    # Create associated Patient, if not there
    patient = Patient.query.get(patient_uuid)
    if not patient:
        patient = Patient(uuid=patient_uuid)
        db.session.add(patient)
        db.session.flush()
    target_timestamp: datetime = parse_iso8601_to_datetime_typesafe(
        target_data["target_timestamp"]
    )
    hba1c_target = Hba1cTarget(
        uuid=generate_uuid(),
        patient_id=patient_uuid,
        value=target_data["value"],
        units=target_data["units"],
        target_timestamp=target_timestamp,
    )
    db.session.add(hba1c_target)
    db.session.commit()
    return hba1c_target.to_dict()


def retrieve_hba1c_targets_for_patient(
    patient_uuid: str,
) -> List[Dict]:
    logger.debug("Retrieving Hba1c targets for patient with UUID %s", patient_uuid)
    hba1c_targets = (
        Hba1cTarget.query.filter_by(patient_id=patient_uuid)
        .order_by(Hba1cTarget.created.desc())
        .all()
    )
    logger.debug(
        "Found %d Hba1c targets for patient with UUID %s",
        len(hba1c_targets),
        patient_uuid,
    )
    return [reading.to_dict() for reading in hba1c_targets]


def update_hba1c_target(
    patient_uuid: str, hba1c_target_uuid: str, target_data: Dict
) -> Dict:
    logger.debug("Updating Hba1c target with UUID %s", hba1c_target_uuid)
    target_db: Hba1cTarget = Hba1cTarget.query.filter_by(
        patient_id=patient_uuid, uuid=hba1c_target_uuid
    ).first_or_404()
    if "value" in target_data:
        target_db.value = target_data["value"]
    if "units" in target_data:
        target_db.units = target_data["units"]
    if "target_timestamp" in target_data:
        target_db.target_timestamp = parse_iso8601_to_datetime_typesafe(
            target_data["target_timestamp"]
        )
    db.session.commit()
    return target_db.to_dict()
