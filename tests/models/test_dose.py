from typing import Dict

from flask_batteries_included.sqldb import generate_uuid

from gdm_bg_readings_api.models.dose import Dose


class TestDose:
    def test_to_dict(self) -> None:
        dose = Dose(
            uuid=generate_uuid(),
            amount=10,
            reading_id=None,
            medication_id="hasvcveclyualjevclvadlusv",
        )
        dose_dict = dose.to_dict()
        assert len(dose_dict.keys()) == 7
        assert isinstance(dose_dict["uuid"], str)
        assert dose_dict["amount"] == 10
        assert dose_dict["medication_id"] == "hasvcveclyualjevclvadlusv"
        assert "reading_id" not in dose_dict
