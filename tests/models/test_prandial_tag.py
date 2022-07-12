from flask_batteries_included.helpers import generate_uuid

from gdm_bg_readings_api.models.prandial_tag import PrandialTag


class TestPrandialTag:
    def test_to_dict(self) -> None:
        tag = PrandialTag(uuid=generate_uuid(), description="Before dinner", value=6)
        tag_dict = tag.to_dict()
        assert len(tag_dict.keys()) == 7
        assert isinstance(tag_dict["uuid"], str)
        assert tag_dict["description"] == "Before dinner"
        assert tag_dict["value"] == 6
