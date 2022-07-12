from flask_batteries_included.sqldb import generate_uuid

from gdm_bg_readings_api.models.reading_banding import ReadingBanding


class TestReadingBanding:
    def test_to_dict(self) -> None:
        banding = ReadingBanding(uuid=generate_uuid(), description="something", value=4)
        banding_dict = banding.to_dict()
        assert len(banding_dict) == 7
        assert isinstance(banding_dict["uuid"], str)
        assert banding_dict["description"] == "something"
        assert banding_dict["value"] == 4
