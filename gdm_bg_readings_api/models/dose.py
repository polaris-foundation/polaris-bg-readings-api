from typing import Any, Dict

from flask_batteries_included.sqldb import ModelIdentifier, db
from sqlalchemy import Index


class Dose(ModelIdentifier, db.Model):

    amount = db.Column(db.Float, unique=False, nullable=False)
    medication_id = db.Column(db.String, unique=False, nullable=False)
    reading_id = db.Column(db.String, db.ForeignKey("reading.uuid"))

    __table_args__ = (Index("dose_uuid", "uuid", unique=True),)

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(Dose, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return dict(
            optional={},
            required={"medication_id": str, "amount": float},
            updatable={"medication_id": str, "amount": float},
        )

    def to_dict(self) -> Dict:
        return {
            "amount": self.amount,
            "medication_id": self.medication_id,
            **self.pack_identifier(),
        }
