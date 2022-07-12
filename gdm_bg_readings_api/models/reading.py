from datetime import datetime
from typing import Any, Dict

from flask_batteries_included.helpers.timestamp import join_timestamp
from flask_batteries_included.sqldb import ModelIdentifier, db
from sqlalchemy import Index


class Reading(ModelIdentifier, db.Model):
    patient_id = db.Column(
        db.String(length=36),
        db.ForeignKey("patient.uuid"),
        unique=False,
        nullable=False,
        index=True,
    )

    blood_glucose_value = db.Column(db.Float, unique=False, nullable=False)
    units = db.Column(db.String, unique=False, nullable=False)
    comment = db.Column(db.String, unique=False, nullable=True)

    doses = db.relationship("Dose", backref="reading")

    red_alert_id = db.Column(db.String(length=36), db.ForeignKey("red_alert.uuid"))

    red_alert = db.relationship("RedAlert", backref="reading", uselist=False)

    amber_alert_id = db.Column(db.String(length=36), db.ForeignKey("amber_alert.uuid"))
    amber_alert = db.relationship("AmberAlert", backref="reading", uselist=False)

    prandial_tag_id = db.Column(
        db.String(length=36), db.ForeignKey("prandial_tag.uuid")
    )
    prandial_tag = db.relationship("PrandialTag", backref="reading", uselist=False)

    reading_metadata_id = db.Column(
        db.String(length=36), db.ForeignKey("reading_metadata.uuid"), nullable=True
    )
    reading_metadata = db.relationship(
        "ReadingMetadata", backref="reading", uselist=False
    )

    reading_banding_id = db.Column(
        db.String(length=36), db.ForeignKey("reading_banding.uuid")
    )
    reading_banding = db.relationship("ReadingBanding", uselist=False)

    # FIXME: https://sensynehealth.atlassian.net/browse/PLAT-674
    measured_timestamp = db.Column(
        db.DateTime, unique=False, nullable=False, index=True
    )
    measured_timezone = db.Column(db.Integer, unique=False, nullable=False)

    # A reading taken within a snooze period will not be able to trigger
    # an alert
    snoozed = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        Index(
            "reading_unique_idx",
            blood_glucose_value,
            units,
            measured_timestamp,
            measured_timezone,
            patient_id,
            unique=True,
        ),
        Index("reading_uuid", "uuid", unique=True),
    )

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(Reading, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {
                "prandial_tag": dict,
                "doses": list,
                "comment": str,
                "reading_metadata": dict,
                "banding_id": str,
            },
            "required": {
                "measured_timestamp": str,
                "blood_glucose_value": float,
                "units": str,
            },
            "updatable": {
                "comment": str,
                "prandial_tag": dict,
                "doses": list,
                "red_alert": dict,
                "amber_alert": dict,
                "banding_id": str,
            },
        }

    def get_measured_timestamp(self) -> datetime:
        return join_timestamp(self.measured_timestamp, self.measured_timezone)

    def to_dict(self, compact: bool = False) -> Dict:
        resp = {
            "blood_glucose_value": float("%.03f" % self.blood_glucose_value),
            "units": self.units,
            "patient_id": self.patient_id,
            "measured_timestamp": self.get_measured_timestamp(),
            **self.pack_identifier(),
        }

        if self.comment:
            resp["comment"] = self.comment
        if self.snoozed:
            resp["snoozed"] = self.snoozed

        if compact is True:
            return self._to_compact_dict(resp)
        else:
            return self._to_expanded_dict(resp)

    def _to_compact_dict(self, resp: Dict) -> Dict:
        compacted_fields_resp = {
            "prandial_tag": self.prandial_tag_id,
            "reading_metadata": (
                self.reading_metadata.to_dict()
                if self.reading_metadata is not None
                else {}
            ),
            "reading_banding": self.reading_banding_id,
            "patient_id": self.patient_id,
            **self.pack_identifier(),
        }

        resp = {**resp, **compacted_fields_resp}

        if self.red_alert:
            resp["red_alert"] = self.red_alert_id
        if self.amber_alert:
            resp["amber_alert"] = self.amber_alert_id

        return resp

    def _to_expanded_dict(self, resp: Dict) -> Dict:
        expanded_fields_resp = {
            "doses": [dose.to_dict() for dose in self.doses],
            "prandial_tag": (
                self.prandial_tag.to_dict() if self.prandial_tag is not None else {}
            ),
            "reading_metadata": (
                self.reading_metadata.to_dict()
                if self.reading_metadata is not None
                else {}
            ),
            "reading_banding": (
                self.reading_banding.to_dict()
                if self.reading_banding is not None
                else {}
            ),
        }

        resp = {**resp, **expanded_fields_resp}

        if self.red_alert:
            resp["red_alert"] = self.red_alert.to_dict()
        if self.amber_alert:
            resp["amber_alert"] = self.amber_alert.to_dict()

        return resp
