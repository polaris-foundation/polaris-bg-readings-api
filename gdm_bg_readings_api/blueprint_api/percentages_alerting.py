from datetime import datetime
from typing import Dict, List, Optional

from flask_batteries_included.helpers.timestamp import parse_iso8601_to_datetime
from flask_batteries_included.sqldb import db, generate_uuid
from she_logging import logger

from gdm_bg_readings_api.blueprint_api.publish import publish_patient_alert
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.patient_alert import PatientAlert


def is_patient_in_snooze_period(patient: Patient) -> bool:
    logger.debug("Checking if patient is in snooze period")
    return (
        patient.suppress_reading_alerts_from is not None
        and patient.suppress_reading_alerts_until is not None
        and patient.suppress_reading_alerts_from
        <= datetime.now()
        <= patient.suppress_reading_alerts_until
    )


def update_alerts_for_patient(
    patient: Patient, alert_type: PatientAlert.AlertType, alert_now: bool
) -> None:
    """
    Updates the alert records for a patient, given an alert type and status. If the alert is
    active right now, creates a PatientAlert if there isn't already an active one. If the
    alert is not active right now, ends any active PatientAlerts.
    :param patient: The patient for which to update alerts
    :param alert_type: A type of alert, e.g. PERCENTAGES_RED, ACTIVITY_GREY
    :param alert_now: Whether the alert is active as of now
    """
    logger.debug(
        "Updating patient alert status",
        extra={
            "patient_uuid": patient.uuid,
            "alert_type": alert_type.value,
            "alert_now": alert_now,
        },
    )
    time_now: datetime = datetime.now()
    existing_alerts: List[PatientAlert] = PatientAlert.query.filter_by(
        patient_id=patient.uuid, ended_at=None, alert_type=alert_type
    ).all()
    logger.debug(
        "Patient %s has %d pre-existing active %s alert(s)",
        patient.uuid,
        len(existing_alerts),
        alert_type.value,
    )
    if alert_now:
        # Create alert if there isn't already one.
        if not existing_alerts:
            logger.debug("No existing alerts, creating a new one")
            new_alert = PatientAlert(
                uuid=generate_uuid(),
                started_at=time_now,
                alert_type=alert_type,
                patient_id=patient.uuid,
            )
            db.session.add(new_alert)
            publish_patient_alert(patient_uuid=patient.uuid, alert_type=alert_type)
    else:
        # Clear any existing alerts.
        for existing_alert in existing_alerts:
            logger.debug("Clearing existing alert with UUID %s", existing_alert.uuid)
            existing_alert.ended_at = time_now


def dismiss_active_alerts_for_patient(patient_id: str) -> None:
    # We only dismiss red/amber percentages alerts, not activity alerts.
    logger.debug("Dismissing active percentages alerts for patient %s", patient_id)
    time_now: datetime = datetime.now()
    existing_active_alerts: List[PatientAlert] = PatientAlert.query.filter_by(
        patient_id=patient_id, ended_at=None
    ).all()
    for a in existing_active_alerts:
        if (
            a.alert_type == PatientAlert.AlertType.PERCENTAGES_RED
            or a.alert_type == PatientAlert.AlertType.PERCENTAGES_AMBER
        ):
            logger.debug("Marking alert %s as dismissed", a.uuid)
            a.dismissed_at = time_now


def calculate_expected_reading_count(
    plans: List[Dict], start_date: datetime, end_date: datetime
) -> float:
    """
    Preconditions:
        - Only the first reading in the list can have a created date that is
        before the start date.
        - The first reading must have a created date that is before or exactly
        equal to the start date

    takes a list of readings plans, a start date (datetime) and an end date
    (datetime).
    weights each plans total readings per week
    (days_per_week_to_take_readings * readings_per_day)
    by the number of seconds the plan was in effect. (clamped between start_date
    and end_date)
    """

    # If there are no plans, return 0, to avoid any division by zero
    if len(plans) == 0:
        return 0

    # define empty values, these will be set later
    total_value = 0
    total_weight = 0

    # sort the plans by created date, so we can iterate forwards through time
    all_plans: List[Dict] = sorted(plans, key=lambda x: x["created"])

    # Filter plans to only the ones that will affect this week
    plans_in_force: List[Dict] = _filter_unnecessary_plans(all_plans, start_date)

    for i in range(len(plans_in_force)):
        # Get current plan (using for i in range instead of a for x in xs construction
        # because we need access to next_plan at index (i+1))
        this_plan = plans_in_force[i]
        next_plan: Optional[Dict] = None
        if i < len(plans_in_force) - 1:
            next_plan = plans_in_force[i + 1]

        current_reading_days_per_week = this_plan["days_per_week_to_take_readings"]
        current_readings_per_day = this_plan["readings_per_day"]
        readings_per_week = current_reading_days_per_week * current_readings_per_day

        plan_start = (
            parse_iso8601_to_datetime(this_plan["created"]) if i > 0 else start_date
        )
        if plan_start is None:
            plan_start = start_date

        # Calculate the current plan's end date based on the next's start
        plan_end = (
            parse_iso8601_to_datetime(next_plan["created"])
            if next_plan is not None
            else end_date
        )
        if plan_end is None:
            plan_end = end_date

        # Weight the values based on the amount of time in the week the plan applies to
        plan_duration = (plan_end - plan_start).total_seconds()
        weighted_value = readings_per_week * plan_duration

        # Update totals
        total_value += weighted_value
        total_weight += int(plan_duration)

        logger.debug(
            "Finished processing plan",
            extra={
                "readings_per_week": readings_per_week,
                "plan_duration": plan_duration,
                "weighted_value": weighted_value,
                "total_value": total_value,
                "total_weight": total_weight,
            },
        )

    expected_number_of_readings: float = total_value / total_weight
    logger.info("Expected readings calculated: %.2f", expected_number_of_readings)

    return expected_number_of_readings


def _filter_unnecessary_plans(plans: List[Dict], start_date: datetime) -> List[Dict]:
    filtered_plans: List[Dict] = []

    # Strip out all plans that do not overlap the start date or fall after the
    # start date
    for i in range(len(plans)):

        this_plan = plans[i]

        # Assign next_plan to be the next in the list, or None if we're on the last one
        next_plan = None
        if i + 1 < len(plans):
            next_plan = plans[i + 1]

        if next_plan is None:
            filtered_plans.append(this_plan)
            continue

        # Append the plan if it's the last one made before the current week starts,
        # or was made in this current week
        this_plan_created: Optional[datetime] = parse_iso8601_to_datetime(
            this_plan["created"]
        )
        next_plan_created: Optional[datetime] = parse_iso8601_to_datetime(
            next_plan["created"]
        )
        if this_plan_created is None or next_plan_created is None:
            logger.error("Plan has no created date")
            raise ValueError
        if this_plan_created >= start_date or next_plan_created >= start_date:
            filtered_plans.append(this_plan)

    return filtered_plans
