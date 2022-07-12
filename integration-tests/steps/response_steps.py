from typing import Dict, List

from assertpy import assert_that, soft_assertions
from behave import step, then, use_step_matcher
from behave.runner import Context
from clients.bg_readings_api_client import (
    clear_alerts,
    get_specific_reading,
    retrieve_patient_summaries,
)
from helpers.readings_helper import assert_reading_body

use_step_matcher("cfparse")


@then("the reading API response status code is {status_code:int}")
def assert_response_status_code(context: Context, status_code: int) -> None:
    assert context.response.status_code == status_code


@then("the reading API response header contains {header:str}")
def assert_response_contains_header(context: Context, header: str) -> None:
    assert context.response.headers.get(header) is not None


@then("the reading API response body is correct")
def response_is_ok(context: Context) -> None:
    assert_reading_body(
        actual_reading_body=context.response.json(),
        expected_reading_body=context.reading_data,
    )
    with soft_assertions():
        assert_that(context.response.json()).has_patient_id(
            context.patient_uuid
        ).has_measured_timestamp(context.reading_data["measured_timestamp"])


@then("the reading is saved in the database")
def assert_reading_data_stored(context: Context) -> None:
    reading_uuid: str = context.response.json()["uuid"]
    response = get_specific_reading(
        patient_uuid=context.patient_uuid, which="latest", context=context
    )
    assert_reading_body(
        actual_reading_body=response.json(), expected_reading_body=context.reading_data
    )
    with soft_assertions():
        assert_that(response.status_code).is_equal_to(200)
        assert_that(response.json()).has_patient_id(context.patient_uuid).has_uuid(
            reading_uuid
        ).has_measured_timestamp(context.reading_data["measured_timestamp"])


@step("the fields have been updated")
def fields_have_been_updated(context: Context) -> None:
    """the initial response was already validated but fetch the reading to verify the database was updated"""
    reading_uuid: str = context.response.json()["uuid"]
    response = get_specific_reading(
        patient_uuid=context.patient_uuid, which=reading_uuid, context=context
    )
    data: Dict = response.json()

    assert_reading_body(data, context.reading_data)

    with soft_assertions():
        assert_that(response.status_code).is_equal_to(200)
        assert_that(data).has_patient_id(context.patient_uuid).has_uuid(
            reading_uuid
        ).has_measured_timestamp(context.reading_data["measured_timestamp"])


@then("the expected readings were returned")
def expected_multiple_readings(context: Context) -> None:
    patient_readings: List[Dict] = context.expected_readings
    patient_uuid = context.patient_uuid

    assert_that(context.response_map.keys()).is_equal_to({patient_uuid})

    readings_returned: List[Dict] = sorted(
        context.response_map[patient_uuid], key=lambda r: r["measured_timestamp"]
    )
    for actual_reading, expected_reading in zip(readings_returned, patient_readings):
        assert_reading_body(
            actual_reading_body=actual_reading,
            expected_reading_body=expected_reading,
        )


@then("the statistics match {min:float}, {max:float}, {count:int}, {normal:int}")
def statistics_match(
    context: Context, min: float, max: float, count: int, normal: int
) -> None:
    stats: Dict[str, Dict] = context.response_map
    assert len(stats) == 1, "Only expecting stats for one patient"
    patient_stats = stats[context.patient_uuid]

    with soft_assertions():
        assert_that(patient_stats).has_readings_count(count)
        assert_that(patient_stats).has_readings_count_banding_normal(normal)
        assert_that(patient_stats["min_reading"]).has_blood_glucose_value(min)
        assert_that(patient_stats["max_reading"]).has_blood_glucose_value(max)


@then(r"the patient summary can be retrieved with {level:str} alert")
def patient_summary_has_alert(context: Context, level: str) -> None:
    response = retrieve_patient_summaries(
        patient_uuids=[context.patient_uuid], context=context
    )

    assert_that(response.status_code).is_equal_to(200)
    assert_that(response.json()[context.patient_uuid]).has_current_red_alert(
        level == "RED"
    ).has_current_amber_alert(level == "AMBER")


@then("we clear the alert for the patient")
def clear_patient_alert(context: Context) -> None:
    response = clear_alerts(context.patient_uuid, context=context)
    with soft_assertions():
        assert_that(response.status_code).is_equal_to(200)
        assert_that(response.json()).has_completed(True)
