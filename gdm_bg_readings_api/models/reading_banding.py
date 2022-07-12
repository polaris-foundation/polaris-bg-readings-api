from typing import Any, Dict

from flask_batteries_included.sqldb import ModelIdentifier, db


class ReadingBanding(ModelIdentifier, db.Model):

    description = db.Column(db.String(20), unique=False, nullable=False)
    value = db.Column(db.Integer, unique=True, nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(ReadingBanding, self).__init__(**kwargs)

    def to_dict(self) -> Dict:
        return {
            "value": self.value,
            "description": self.description,
            **self.pack_identifier(),
        }
