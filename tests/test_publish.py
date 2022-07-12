import uuid
from unittest.mock import Mock

import kombu_batteries_included
import pytest
from pytest_mock import MockFixture

from gdm_bg_readings_api.blueprint_api import publish


@pytest.fixture
def mock_publish(mocker: MockFixture) -> Mock:
    return mocker.patch.object(kombu_batteries_included, "publish_message")


def test_publish_audit_message(mock_publish: Mock) -> None:
    event_type = "some_reason_to_live"
    event_data = {
        "patient_id": str(uuid.uuid4()),
        "duplicate_reading_id": str(uuid.uuid4()),
    }
    expected = {"event_type": event_type, "event_data": event_data}
    publish.publish_audit_message(event_type=event_type, event_data=event_data)
    mock_publish.assert_called_with(routing_key="dhos.34837004", body=expected)
