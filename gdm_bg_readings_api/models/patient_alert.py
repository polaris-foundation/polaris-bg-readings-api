from enum import Enum
from typing import Any, Dict

from flask_batteries_included.helpers.timestamp import parse_datetime_to_iso8601
from flask_batteries_included.sqldb import ModelIdentifier, db


class PatientAlert(ModelIdentifier, db.Model):
    """
    There are two systems of alerting used in GDM: "counts" alerts, which are triggered
    when a patient records successive or frequent out-of-threshold (high/low) readings;
    and "percentages" alerts, which are triggered when a patient has a high percentage
    of recent out-of-threshold readings.

    This model is distinct from RedAlert and AmberAlert. These latter models are the
    "counts" alerts that are associated with individual readings. The PatientAlert,
    however, is associated with patients rather than readings, and correspond to the
    new "percentages" alert
    """

    class AlertType(Enum):
        COUNTS_RED = "COUNTS_RED"
        COUNTS_AMBER = "COUNTS_AMBER"
        PERCENTAGES_RED = "PERCENTAGES_RED"
        PERCENTAGES_AMBER = "PERCENTAGES_AMBER"
        ACTIVITY_GREY = "ACTIVITY_GREY"

    dismissed_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    alert_type = db.Column(db.Enum(AlertType), nullable=False)
    patient_id = db.Column(
        db.String(length=36), db.ForeignKey("patient.uuid"), nullable=False
    )

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(PatientAlert, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {"dismissed_at": str, "ended_at": str},
            "required": {"started_at": str, "alert_type": str, "patient_id": str},
            "updatable": {"dismissed_at": str, "ended_at": str},
        }

    def to_dict(self) -> Dict:
        return {
            **self.pack_identifier(),
            "dismissed_at": parse_datetime_to_iso8601(self.dismissed_at),
            "started_at": parse_datetime_to_iso8601(self.started_at),
            "ended_at": parse_datetime_to_iso8601(self.ended_at),
            "alert_type": self.alert_type.value,
            "patient_id": self.patient_id,
        }
