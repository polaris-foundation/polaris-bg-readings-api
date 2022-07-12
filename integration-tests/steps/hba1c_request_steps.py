from datetime import datetime

from behave import given, use_step_matcher, when
from behave.runner import Context
from clients.hba1c_readings_api_client import (
    delete_hba1c_reading,
    patch_hba1c_reading,
    post_hba1c_reading,
)

use_step_matcher("cfparse")


@when(
    "a valid Hba1c reading of {value:float} {units} for patient {patient_uuid} is posted"
)
def create_hba1c_reading_valid(
    context: Context,
    value: float,
    units: str,
    patient_uuid: str,
) -> None:

    create_hba1c_reading(
        context=context, patient_uuid=patient_uuid, value=value, units=units
    )
    context.response.raise_for_status()


@when(
    "an invalid Hba1c reading of {value:float} {units} for patient {patient_uuid} is posted"
)
def create_hba1c_reading_invalid(
    context: Context,
    value: float,
    units: str,
    patient_uuid: str,
) -> None:
    create_hba1c_reading(
        context=context, patient_uuid=patient_uuid, value=value, units=units
    )


def create_hba1c_reading(
    context: Context, patient_uuid: str, value: float, units: str
) -> None:
    context.patient_uuid = patient_uuid
    measured_timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    context.reading_data = {
        "measured_timestamp": measured_timestamp,
        "value": value,
        "units": units,
    }
    context.response = post_hba1c_reading(
        patient_uuid=context.patient_uuid,
        reading_data=context.reading_data,
        context=context,
    )


@given("a new Hba1c reading is created")
def hba1c_reading_exists(context: Context) -> None:

    create_hba1c_reading(
        context=context, patient_uuid="patient-1", value=42.0, units="mmol/mol"
    )
    context.response.raise_for_status()


@when("the Hba1c reading is updated")
def update_hba1c_reading_step(context: Context) -> None:

    response = context.requests.get(
        url=context.response.headers["Location"],
        timeout=15,
    )
    response.raise_for_status()

    context.reading_uuid = response.json()["uuid"]
    measured_timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    context.reading_data = {
        "measured_timestamp": measured_timestamp,
        "value": 43,
        "units": "mmol/mol",
    }
    context.response = patch_hba1c_reading(
        patient_uuid=context.patient_uuid,
        reading_uuid=context.reading_uuid,
        reading_data=context.reading_data,
        context=context,
    )


@when("the Hba1c reading is deleted")
def delete_hba1c_reading_step(context: Context) -> None:

    response = context.requests.get(
        url=context.response.headers["Location"],
        timeout=15,
    )
    response.raise_for_status()

    context.reading_uuid = response.json()["uuid"]
    context.response = delete_hba1c_reading(
        patient_uuid=context.patient_uuid,
        reading_uuid=context.reading_uuid,
        context=context,
    )
