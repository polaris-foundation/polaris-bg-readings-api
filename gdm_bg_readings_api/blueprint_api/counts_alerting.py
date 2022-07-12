from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask_batteries_included.sqldb import generate_uuid
from she_logging import logger
from sqlalchemy.sql.expression import false

from gdm_bg_readings_api.blueprint_api.publish import publish_patient_alert
from gdm_bg_readings_api.models.amber_alert import AmberAlert
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.patient_alert import PatientAlert
from gdm_bg_readings_api.models.reading import Reading
from gdm_bg_readings_api.models.red_alert import RedAlert
from gdm_bg_readings_api.utils.datetime_utils import (
    calculate_last_midnight,
    calculate_midnight_plus_days,
)

MIN_ABNORMAL_READINGS_FOR_COUNTS_ALERT: int = 3
OFFSET: int = MIN_ABNORMAL_READINGS_FOR_COUNTS_ALERT - 1


def is_reading_in_snooze_period(reading: Reading, patient: Patient) -> bool:
    logger.debug("Checking if reading is in snooze period")

    if not patient.suppress_reading_alerts_from:
        return False
    logger.debug("suppress_reading_alerts_from is set")

    if not patient.suppress_reading_alerts_until:
        return False
    logger.debug("suppress_reading_alerts_until is set")

    if (
        patient.suppress_reading_alerts_from
        <= reading.measured_timestamp
        <= patient.suppress_reading_alerts_until
    ):
        return True
    return False


def reading_could_trigger_red_alert(reading: Reading) -> bool:
    if not reading_could_trigger_alert(reading):
        return False
    if reading.red_alert and reading.red_alert.dismissed:
        return False
    return True


def reading_could_trigger_alert(reading: Reading) -> bool:
    if reading.snoozed:
        return False
    if reading.reading_banding_id == "BG-READING-BANDING-NORMAL":
        return False
    return True


def get_alertable_readings(reading: Reading) -> Dict:
    logger.debug("Getting alertable readings")
    past_readings, future_readings = _get_surrounding_readings(reading)
    readings_to_check = past_readings + [reading] + future_readings
    return _get_sequential_abnormal_readings(readings_to_check)


def process_amber_alertable_readings(reading: Reading) -> Reading:
    # get readings for last 2 calendar days with readings
    start_date, end_date = _get_last_two_reading_calendar_days(reading)
    logger.debug(
        "Processing readings for possible amber alerts",
        extra={"start_date": str(start_date), "end_date": str(end_date)},
    )

    # is the current reading within the last two readings days
    current_time: datetime = reading.get_measured_timestamp()
    if start_date > current_time or end_date < current_time:
        logger.debug("Current reading is not in last two days")
        return reading

    # check for 2 or more readings
    readings: List[Reading] = (
        Reading.query.filter(
            (Reading.measured_timestamp > start_date)
            & (Reading.measured_timestamp < end_date)
            & (Reading.patient_id == reading.patient_id)
        )
        .order_by(Reading.measured_timestamp.desc())
        .all()
    )
    triggering_readings = [r for r in readings if reading_could_trigger_alert(r)]

    # if two or more readings have abnormal values mark all abnormal readings
    # as amber alerts
    if len(triggering_readings) > 1:
        for tr in triggering_readings:
            logger.debug("Adding amber alert to reading %s", tr.uuid)
            add_amber_alert_to_reading(tr)

        logger.debug("Setting amber alert for patient %s", reading.patient.uuid)
        reading.patient.current_amber_alert = True

        logger.debug("Publishing amber alert message for reading %s", reading.uuid)
        publish_patient_alert(
            patient_uuid=reading.patient_id,
            alert_type=PatientAlert.AlertType.COUNTS_AMBER,
        )

    return reading


def _get_last_two_reading_calendar_days(reading: Reading) -> Tuple[datetime, datetime]:
    latest_reading = (
        Reading.query.filter_by(patient_id=reading.patient_id)
        .order_by(Reading.measured_timestamp.desc())
        .first()
    )

    midnight = calculate_last_midnight(base=latest_reading.get_measured_timestamp())
    end_date = calculate_midnight_plus_days(
        base=latest_reading.get_measured_timestamp(), offset=1
    )

    previous_day_reading: Optional[Reading] = (
        Reading.query.filter(
            (Reading.patient_id == latest_reading.patient_id)
            & (Reading.measured_timestamp < midnight)
        )
        .order_by(Reading.measured_timestamp.desc())
        .first()
    )
    if previous_day_reading is None:
        start_date = midnight
    else:
        start_date = calculate_last_midnight(
            base=previous_day_reading.get_measured_timestamp()
        )

    return start_date, end_date


def _get_sequential_abnormal_readings(readings_to_check: List[Reading]) -> Dict:
    """Returns the list of readings which trigger an alert because they are in a sequence"""
    alertable: List[bool] = [
        reading_could_trigger_red_alert(r) for r in readings_to_check
    ]
    to_alert = {}
    num_readings_to_check = len(readings_to_check)
    if num_readings_to_check >= MIN_ABNORMAL_READINGS_FOR_COUNTS_ALERT:
        adj_num_readings_to_check = len(readings_to_check) - OFFSET
        for i in range(0, adj_num_readings_to_check):
            if not _is_sequential_block_true(i, num_readings_to_check, alertable):
                break
            for j in range(i, num_readings_to_check):
                to_alert[j] = readings_to_check[j]
    return to_alert


def _is_sequential_block_true(
    inital_point: int, num_readings: int, block: List[bool]
) -> bool:
    for j in range(inital_point, inital_point + OFFSET + 1):
        if not block[j]:
            return False

    return True


def _get_surrounding_readings(reading: Reading) -> Tuple[List[Reading], List[Reading]]:
    future_readings = (
        Reading.query.filter(
            (Reading.prandial_tag_id == reading.prandial_tag_id)
            & (Reading.measured_timestamp > reading.measured_timestamp)
            & (Reading.patient_id == reading.patient_id)
        )
        .order_by(Reading.measured_timestamp.asc())
        .limit(OFFSET)
        .all()
    )

    past_readings = (
        Reading.query.filter(
            (Reading.prandial_tag_id == reading.prandial_tag_id)
            & (Reading.measured_timestamp < reading.measured_timestamp)
            & (Reading.patient_id == reading.patient_id)
        )
        .order_by(Reading.measured_timestamp.desc())
        .limit(OFFSET)
        .all()
    )

    return future_readings, past_readings


def add_red_alert_to_reading(reading: Reading) -> Reading:
    reading.red_alert = RedAlert(uuid=generate_uuid(), dismissed=False)
    return reading


def add_amber_alert_to_reading(reading: Reading) -> Reading:
    reading.amber_alert = AmberAlert(uuid=generate_uuid(), dismissed=False)
    return reading


def dismiss_active_alerts_for_patient(patient_id: str) -> None:
    readings_with_alerts: List[Reading] = Reading.query.filter(
        (
            (Reading.red_alert_id.isnot(None))
            & (Reading.red_alert.has(dismissed=false()))
            & (Reading.patient_id == patient_id)
        )
        | (
            (Reading.amber_alert_id.isnot(None))
            & (Reading.amber_alert.has(dismissed=false()))
            & (Reading.patient_id == patient_id)
        )
    ).all()
    for reading in readings_with_alerts:
        logger.debug("Clearing counts alerts for reading with UUID %s", reading.uuid)
        if reading.red_alert_id:
            reading.red_alert.dismissed = True
        if reading.amber_alert_id:
            reading.amber_alert.dismissed = True
