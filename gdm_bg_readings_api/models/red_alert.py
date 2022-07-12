from typing import Any, Dict

from flask_batteries_included.sqldb import ModelIdentifier, db


class RedAlert(ModelIdentifier, db.Model):

    dismissed = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs: Any) -> None:
        # Constructor to satisfy linters.
        super(RedAlert, self).__init__(**kwargs)

    @staticmethod
    def schema() -> Dict:
        return {
            "optional": {"dismissed"},
            "required": {},
            "updatable": {"dismissed": bool},
        }

    def to_dict(self) -> Dict:
        return {"dismissed": self.dismissed, **self.pack_identifier()}
