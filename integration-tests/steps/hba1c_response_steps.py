from assertpy import assert_that, soft_assertions
from behave import then
from behave.runner import Context
from clients.bg_readings_api_client import (
    BG_READINGS_API_HOST,
    retrieve_patient_summaries,
)
from clients.hba1c_readings_api_client import get_hba1c_reading_by_uuid


@then("the Hba1c reading POST response is correct")
def response_is_ok(context: Context) -> None:

    with soft_assertions():
        assert_that("Location" in context.response.headers)
        assert_that(context.response.status_code).is_equal_to(201)


@then("the Hba1c reading is saved in the database")
def assert_reading_data_stored(context: Context) -> None:

    if context.response.status_code == 201:
        response = context.requests.get(
            url=f"{BG_READINGS_API_HOST}/{context.response.headers['Location']}",
            timeout=15,
        )
    else:
        response = get_hba1c_reading_by_uuid(
            patient_uuid=context.patient_uuid,
            reading_uuid=context.reading_uuid,
            context=context,
        )
    response.raise_for_status()

    with soft_assertions():
        assert_that(response.json()).has_patient_id(context.patient_uuid)
        assert_that(response.json()).has_measured_timestamp(
            context.reading_data["measured_timestamp"]
        )
        assert_that(response.json()).has_value(context.reading_data["value"])
        assert_that(response.status_code).is_equal_to(200)


@then("the patient summary can be retrieved without any BG readings")
def assert_get_patient_summary_ok(context: Context) -> None:
    response = retrieve_patient_summaries(
        patient_uuids=[context.patient_uuid], context=context
    )

    with soft_assertions():
        assert_that(context.patient_uuid in response.json())
        assert_that(response.json()[context.patient_uuid]).is_equal_to({})
        assert_that(response.status_code).is_equal_to(200)


@then("the Hba1c reading API response status is 400 if units are invalid")
def response_is_error(context: Context) -> None:

    with soft_assertions():
        assert_that(context.response.status_code).is_equal_to(400)


@then("the Hba1c reading can not be retrieved")
def assert_reading_data_cannot_be_retrieved(context: Context) -> None:

    response = get_hba1c_reading_by_uuid(
        patient_uuid=context.patient_uuid,
        reading_uuid=context.reading_uuid,
        context=context,
    )

    with soft_assertions():
        assert_that(response.status_code).is_equal_to(404)
