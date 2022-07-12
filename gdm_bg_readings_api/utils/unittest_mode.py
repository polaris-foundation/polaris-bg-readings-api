from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def populate_unittest_data(app: Flask, db: SQLAlchemy) -> None:

    from gdm_bg_readings_api.models.prandial_tag import PrandialTag
    from gdm_bg_readings_api.models.reading_banding import ReadingBanding

    prandial_tag_data = [
        {
            "uuid": "PRANDIAL-TAG-NONE",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "none",
            "value": 0,
        },
        {
            "uuid": "PRANDIAL-TAG-BEFORE-BREAKFAST",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "before_breakfast",
            "value": 1,
        },
        {
            "uuid": "PRANDIAL-TAG-AFTER-BREAKFAST",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "after_breakfast",
            "value": 2,
        },
        {
            "uuid": "PRANDIAL-TAG-BEFORE-LUNCH",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "before_lunch",
            "value": 3,
        },
        {
            "uuid": "PRANDIAL-TAG-AFTER-LUNCH",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "after_lunch",
            "value": 4,
        },
        {
            "uuid": "PRANDIAL-TAG-BEFORE-DINNER",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "before_dinner",
            "value": 5,
        },
        {
            "uuid": "PRANDIAL-TAG-AFTER-DINNER",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "after_dinner",
            "value": 6,
        },
        {
            "uuid": "PRANDIAL-TAG-OTHER",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "other",
            "value": 7,
        },
    ]

    banding_data = [
        {
            "uuid": "BG-READING-BANDING-LOW",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "low",
            "value": 1,
        },
        {
            "uuid": "BG-READING-BANDING-NORMAL",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "normal",
            "value": 2,
        },
        {
            "uuid": "BG-READING-BANDING-HIGH",
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
            "description": "high",
            "value": 3,
        },
    ]

    with app.app_context():
        db.drop_all()
        db.create_all()

        for d in prandial_tag_data:
            db.session.add(
                PrandialTag(
                    uuid=d["uuid"], description=d["description"], value=d["value"]
                )
            )

        for d in banding_data:
            db.session.add(
                ReadingBanding(
                    uuid=d["uuid"], description=d["description"], value=d["value"]
                )
            )

        db.session.commit()
