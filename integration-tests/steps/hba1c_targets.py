import uuid
from datetime import datetime, timezone
from typing import Optional

from behave import given, then, when
from behave.runner import Context
from clients import bg_readings_api_client


@given("a new Hba1c target is created")
def hba1c_target_exists(context: Context) -> None:
    context.hba1c_target_timestamp = datetime.now(tz=timezone.utc).isoformat(
        timespec="milliseconds"
    )
    context.patient_uuid = str(uuid.uuid4())
    target_data = {
        "value": 10.5,
        "units": "mmol/mol",
        "target_timestamp": context.hba1c_target_timestamp,
    }
    response = bg_readings_api_client.create_hba1c_target(
        patient_uuid=context.patient_uuid,
        target_data=target_data,
        context=context,
    )
    response.raise_for_status()
    assert response.status_code == 201
    location: Optional[str] = response.headers.get("Location")
    assert location is not None
    context.hba1c_target_uuid = location.split("/")[-1]


@when("the Hba1c target is updated")
def update_hba1c_target_step(context: Context) -> None:
    context.hba1c_target_value = 20.3
    response = bg_readings_api_client.update_hba1c_target(
        patient_uuid=context.patient_uuid,
        target_uuid=context.hba1c_target_uuid,
        target_data={"value": context.hba1c_target_value},
        context=context,
    )
    response.raise_for_status()
    assert response.status_code == 204


@then("the Hba1c targets can be retrieved")
def assert_target_data_stored(context: Context) -> None:
    response = bg_readings_api_client.get_hba1c_targets_by_patient_uuid(
        patient_uuid=context.patient_uuid, context=context
    )
    response.raise_for_status()
    assert response.status_code == 200
    targets = response.json()
    assert len(targets) == 1
    assert targets[0]["uuid"] == context.hba1c_target_uuid
    assert targets[0]["value"] == context.hba1c_target_value
    assert datetime.fromisoformat(
        targets[0]["target_timestamp"].replace("Z", "+00:00")
    ) == datetime.fromisoformat(context.hba1c_target_timestamp)
    assert targets[0]["patient_id"] == context.patient_uuid
