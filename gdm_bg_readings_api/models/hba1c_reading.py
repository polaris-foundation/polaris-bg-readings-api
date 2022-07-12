from datetime import datetime, timezone
from typing import Any, Dict

from flask_batteries_included.helpers.timestamp import parse_iso8601_to_datetime
from flask_batteries_included.sqldb import ModelIdentifier, db
from sqlalchemy import Index

from gdm_bg_readings_api.query.softdelete import QueryWithSoftDelete


class Hba1cReading(ModelIdentifier, db.Model):
    query_class = QueryWithSoftDelete

    patient_id = db.Column(
        db.String(length=36),
        db.ForeignKey("patient.uuid", name="hba1c_reading_patient_id"),
        unique=False,
        nullable=False,
        index=True,
    )

    value = db.Column(db.Float, unique=False, nullable=False)
    units = db.Column(db.String, unique=False, nullable=False)

    measured_timestamp = db.Column(
        db.DateTime(timezone=True), unique=False, nullable=False, index=True
    )

    # system
    deleted = db.Column(db.DateTime, unique=False, nullable=True)

    __table_args__ = (Index("hba1c_reading_uuid", "uuid", unique=True),)

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(Hba1cReading, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {},
            "required": {
                "measured_timestamp": str,
                "value": float,
                "units": str,
            },
            "updatable": {
                "measured_timestamp": str,
                "value": float,
                "units": str,
            },
        }

    def to_dict(self, compact: bool = False) -> Dict:
        measured_timestamp = self.measured_timestamp
        if measured_timestamp.tzinfo is None:
            # sqlite loses tzinfo, shouldn't happen outside tests
            measured_timestamp = measured_timestamp.replace(tzinfo=timezone.utc)
        reading = {
            "value": self.value,
            "units": self.units,
            "patient_id": self.patient_id,
            "measured_timestamp": measured_timestamp,
            **self.pack_identifier(),
        }

        if self.deleted is not None:
            reading["deleted"] = self.deleted

        return reading

    def set_property(self, key: str, value: Any) -> None:

        if key == "measured_timestamp":
            setattr(self, key, parse_iso8601_to_datetime(value))
            return

        setattr(self, key, value)

    def delete(self) -> None:
        self.deleted = datetime.utcnow()
