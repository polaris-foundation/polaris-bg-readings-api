from datetime import timezone
from typing import Any, Dict

from flask_batteries_included.sqldb import ModelIdentifier, db


class Hba1cTarget(ModelIdentifier, db.Model):

    patient_id = db.Column(
        db.String(length=36),
        db.ForeignKey("patient.uuid", name="hba1c_target_patient_id"),
        unique=False,
        nullable=False,
        index=True,
    )
    value = db.Column(db.Float, unique=False, nullable=False)
    units = db.Column(db.String, unique=False, nullable=False)
    target_timestamp = db.Column(
        db.DateTime(timezone=True), unique=False, nullable=False
    )

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(Hba1cTarget, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {},
            "required": {
                "value": float,
                "units": str,
                "measured_timestamp": str,
            },
            "updatable": {
                "value": float,
                "units": str,
                "measured_timestamp": str,
            },
        }

    def to_dict(self) -> Dict:
        target_timestamp = self.target_timestamp
        if target_timestamp.tzinfo is None:
            # sqlite loses tzinfo, shouldn't happen outside tests
            target_timestamp = target_timestamp.replace(tzinfo=timezone.utc)
        return {
            "value": self.value,
            "units": self.units,
            "target_timestamp": target_timestamp,
            "patient_id": self.patient_id,
            **self.pack_identifier(),
        }
