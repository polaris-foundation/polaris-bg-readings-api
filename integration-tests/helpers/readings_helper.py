from datetime import datetime, timezone
from typing import Dict, Optional

from assertpy import assert_that, soft_assertions

PRANDIAL_TAGS = {
    "PRANDIAL-TAG-NONE": 0,
    "PRANDIAL-TAG-BEFORE-BREAKFAST": 1,
    "PRANDIAL-TAG-AFTER-BREAKFAST": 2,
    "PRANDIAL-TAG-BEFORE-LUNCH": 3,
    "PRANDIAL-TAG-AFTER-LUNCH": 4,
    "PRANDIAL-TAG-BEFORE-DINNER": 5,
    "PRANDIAL-TAG-AFTER-DINNER": 6,
    "PRANDIAL-TAG-OTHER": 7,
}


def generate_reading_request(
    value: int,
    banding: str,
    measured_time: Optional[datetime] = None,
    dose: Dict = None,
    comment: str = "Reading from GDM BG Readings integration tests",
    tag: str = "OTHER",
) -> Dict:
    if measured_time is None:
        measured_time = datetime.utcnow().replace(tzinfo=timezone.utc)
    assert_that(measured_time.tzinfo).is_not_none()

    return {
        "measured_timestamp": measured_time.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        ),
        "blood_glucose_value": value,
        "units": "mmol/L",
        "prandial_tag": generate_prandial_tag(tag),
        "comment": comment,
        "doses": [dose] if dose is not None else [],
        "banding_id": "BG-READING-BANDING-" + banding.upper(),
    }


def generate_reading_value(banding: str) -> int:
    bandings = {"HIGH": 14, "LOW": 2, "NORMAL": 6}
    return bandings.get(banding.upper(), 6)


def generate_prandial_tag(name: str) -> Dict:
    tag_id = f"PRANDIAL-TAG-{name}"
    tag_value = PRANDIAL_TAGS[tag_id]
    return {"uuid": tag_id, "value": tag_value}


def assert_reading_body(actual_reading_body: dict, expected_reading_body: dict) -> None:
    with soft_assertions():
        assert_that(actual_reading_body).has_blood_glucose_value(
            expected_reading_body["blood_glucose_value"]
        ).has_units(expected_reading_body["units"]).has_comment(
            expected_reading_body["comment"]
        )
        assert_that(actual_reading_body["doses"]).extracting("amount").is_equal_to(
            [dose["amount"] for dose in expected_reading_body["doses"]]
        )
        assert_that(actual_reading_body["doses"]).extracting(
            "medication_id"
        ).is_equal_to(
            [dose["medication_id"] for dose in expected_reading_body["doses"]]
        )
        assert_that(actual_reading_body["reading_banding"]["uuid"]).is_equal_to(
            expected_reading_body["banding_id"]
        )
        assert_that(actual_reading_body["prandial_tag"]["uuid"]).is_equal_to(
            expected_reading_body["prandial_tag"]["uuid"]
        )
