from datetime import datetime

from flask_batteries_included.sqldb import generate_uuid

from gdm_bg_readings_api.models.reading import Reading


class TestReading:
    def test_to_dict(self) -> None:
        reading = Reading(
            uuid=generate_uuid(),
            blood_glucose_value=5.1234567,
            units="mmol/L",
            patient_id="patient_uuid",
            measured_timestamp=datetime.now(),
            measured_timezone=0,
            comment="This is a comment",
            snoozed=True,
        )
        reading_dict = reading.to_dict()
        assert len(reading_dict.keys()) == 15
        assert reading_dict["blood_glucose_value"] == 5.123
        assert reading_dict["snoozed"] is True
        assert reading_dict["patient_id"] == "patient_uuid"
        assert reading_dict["comment"] == "This is a comment"
        assert reading_dict["reading_metadata"] == {}
        assert "reading_metadata_id" not in reading_dict
        assert "reading_id" not in reading_dict
        reading.blood_glucose_value = 5.55555
        assert reading.to_dict()["blood_glucose_value"] == 5.556
        reading.blood_glucose_value = 9.999999999999
        assert reading.to_dict()["blood_glucose_value"] == 10.000
