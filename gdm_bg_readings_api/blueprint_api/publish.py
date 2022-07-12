from typing import Any, Dict

import kombu_batteries_included
from she_logging import logger

from gdm_bg_readings_api.models.patient_alert import PatientAlert
from gdm_bg_readings_api.models.reading import Reading


# SCTID: 166922008 Blood glucose abnormal (finding)
def publish_abnormal_reading(reading: Reading) -> None:
    reading_data: Dict = reading.to_dict()
    logger.debug("Publishing gdm.166922008 abnormal reading")
    kombu_batteries_included.publish_message(
        routing_key="gdm.166922008", body=reading_data
    )


# SCTID: 424167000 At risk for unstable blood glucose level (finding)
def publish_patient_alert(
    patient_uuid: str, alert_type: PatientAlert.AlertType
) -> None:
    logger.debug(
        "Publishing gdm.424167000 patient alert for patient with UUID %s", patient_uuid
    )
    kombu_batteries_included.publish_message(
        routing_key="gdm.424167000",
        body={"patient_uuid": patient_uuid, "alert_type": alert_type.value},
    )


def publish_audit_message(event_type: str, event_data: Dict[str, Any]) -> None:
    logger.debug(f"Publishing dhos.34837004 audit message of type '{event_type}'")
    kombu_batteries_included.publish_message(
        routing_key="dhos.34837004",
        body={"event_type": event_type, "event_data": event_data},
    )
