from datetime import datetime
from typing import Any, Dict, Optional

from flask_batteries_included.helpers.timestamp import join_timestamp, split_timestamp
from flask_batteries_included.sqldb import ModelIdentifier, db


class Patient(ModelIdentifier, db.Model):

    suppress_reading_alerts_from = db.Column(db.DateTime, unique=False, nullable=True)
    suppress_reading_alerts_from_tz = db.Column(db.Integer, unique=False, nullable=True)

    suppress_reading_alerts_until = db.Column(db.DateTime, unique=False, nullable=True)
    suppress_reading_alerts_until_tz = db.Column(
        db.Integer, unique=False, nullable=True
    )

    current_red_alert = db.Column(db.Boolean, unique=False, nullable=True)
    current_amber_alert = db.Column(db.Boolean, unique=False, nullable=True)
    current_activity_alert = db.Column(db.Boolean, unique=False, nullable=True)

    readings = db.relationship(
        "Reading", backref="patient", lazy="dynamic", uselist=True
    )

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(Patient, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {
                "suppress_reading_alerts_from",
                "suppress_reading_alerts_until",
            },
            "required": {},
            "updatable": {
                "suppress_reading_alerts_from": str,
                "suppress_reading_alerts_until": str,
            },
        }

    def set_suppress_reading_alerts_from(self, timestamp: str) -> None:
        ts, tz = split_timestamp(timestamp)
        self.suppress_reading_alerts_from = ts
        self.suppress_reading_alerts_from_tz = tz

    def set_suppress_reading_alerts_until(self, timestamp: str) -> None:
        ts, tz = split_timestamp(timestamp)
        self.suppress_reading_alerts_until = ts
        self.suppress_reading_alerts_until_tz = tz

    def get_suppress_reading_alerts_from(self) -> Optional[datetime]:
        suppress_reading_alerts_from = None
        if self.suppress_reading_alerts_from is not None:
            suppress_reading_alerts_from = join_timestamp(
                self.suppress_reading_alerts_from, self.suppress_reading_alerts_from_tz
            )
        return suppress_reading_alerts_from

    def get_suppress_reading_alerts_until(self) -> Optional[datetime]:
        suppress_reading_alerts_until = None
        if self.suppress_reading_alerts_until is not None:
            suppress_reading_alerts_until = join_timestamp(
                self.suppress_reading_alerts_until,
                self.suppress_reading_alerts_until_tz,
            )
        return suppress_reading_alerts_until

    def to_dict(self) -> Dict:
        return {
            "suppress_reading_alerts_from": self.get_suppress_reading_alerts_from(),
            "suppress_reading_alerts_until": self.get_suppress_reading_alerts_until(),
            "current_red_alert": self.current_red_alert or False,
            "current_amber_alert": self.current_amber_alert or False,
            "current_activity_alert": self.current_activity_alert or False,
            **self.pack_identifier(),
        }
