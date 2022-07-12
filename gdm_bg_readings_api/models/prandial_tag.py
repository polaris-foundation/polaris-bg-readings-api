from enum import Enum
from typing import Any, Dict

from flask_batteries_included.sqldb import ModelIdentifier, db
from sqlalchemy import Index


class PrandialTagOptions(Enum):
    NONE = 0
    BEFORE_BREAKFAST = 1
    AFTER_BREAKFAST = 2
    BEFORE_LUNCH = 3
    AFTER_LUNCH = 4
    BEFORE_DINNER = 5
    AFTER_DINNER = 6
    OTHER = 7


class PrandialTag(ModelIdentifier, db.Model):

    description = db.Column(db.String, unique=False, nullable=False)
    value = db.Column(db.Integer, unique=False, nullable=False)

    __table_args__ = (Index("prandial_tag_uuid", "uuid", unique=True),)

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(PrandialTag, self).__init__(**kwargs)

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "value": self.value,
            **self.pack_identifier(),
        }
