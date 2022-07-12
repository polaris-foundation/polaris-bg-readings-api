from typing import Any, Dict

from flask_batteries_included.sqldb import ModelIdentifier, db
from sqlalchemy import Index


class ReadingMetadata(ModelIdentifier, db.Model):

    meter_serial_number = db.Column(db.String, unique=False, nullable=True)
    meter_model = db.Column(db.String, unique=False, nullable=True)
    manufacturer = db.Column(db.String, unique=False, nullable=True)

    manual = db.Column(db.Boolean, unique=False, nullable=False)
    control = db.Column(db.Boolean, unique=False, nullable=False)

    transmitted_reading = db.Column(db.Float, unique=False, nullable=True)
    reading_is_correct = db.Column(db.Boolean, unique=False, nullable=True)

    __table_args__ = (Index("reading_metadata_uuid", "uuid", unique=True),)

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(ReadingMetadata, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {
                "meter_serial_number": str,
                "meter_model": str,
                "manufacturer": str,
                "reading_is_correct": bool,
                "transmitted_reading": float,
            },
            "required": {"control": bool, "manual": bool},
            "updatable": {},
        }

    def to_dict(self) -> Dict:
        resp = {
            "manual": self.manual,
            "control": self.control,
            "reading_is_correct": self.reading_is_correct,
            "transmitted_reading": self.transmitted_reading,
            **self.pack_identifier(),
        }

        if not self.manual:
            resp["meter_serial_number"] = self.meter_serial_number
            resp["meter_model"] = self.meter_model
            resp["manufacturer"] = self.manufacturer

        return resp
