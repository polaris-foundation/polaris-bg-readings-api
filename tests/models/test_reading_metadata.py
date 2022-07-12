from flask_batteries_included.sqldb import generate_uuid

from gdm_bg_readings_api.models.reading_metadata import ReadingMetadata


class TestReadingMetadata:
    def test_to_dict(self) -> None:
        reading_metadata = ReadingMetadata(
            uuid=generate_uuid(),
            meter_serial_number="H5J8S7R5G2D8S7",
            meter_model="S67",
            manufacturer="super awesome meter company",
            control=False,
            manual=False,
            reading_is_correct=True,
        )
        reading_metadata_dict = reading_metadata.to_dict()
        assert len(reading_metadata_dict) == 12
        assert isinstance(reading_metadata_dict["uuid"], str)
        assert reading_metadata_dict["meter_serial_number"] == "H5J8S7R5G2D8S7"
        assert reading_metadata_dict["meter_model"] == "S67"
        assert reading_metadata_dict["manufacturer"] == "super awesome meter company"
        assert reading_metadata_dict["control"] is False
        assert reading_metadata_dict["manual"] is False
        assert reading_metadata_dict["reading_is_correct"] is True
        assert reading_metadata_dict["transmitted_reading"] is None
