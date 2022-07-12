import itertools
from datetime import datetime, timedelta, timezone

from assertpy import assert_that
from behave import given, use_step_matcher, when
from behave.runner import Context
from clients import wiremock_client
from clients.bg_readings_api_client import (
    get_recent_readings,
    get_specific_reading,
    get_statistics,
    post_bg_reading,
    post_bg_reading_v1,
    process_alerts,
    update_bg_reading,
)
from clients.rabbitmq_client import RABBITMQ_MESSAGES, get_rabbitmq_message
from helpers.readings_helper import (
    generate_prandial_tag,
    generate_reading_request,
    generate_reading_value,
)

use_step_matcher("cfparse")


@given("the Trustomer API is running")
def setup_mock_trustomer_api(context: Context) -> None:
    wiremock_client.setup_mock_get_trustomer_config()


@when("a {banding:str} BG reading is posted")
def create_bg_reading(context: Context, banding: str) -> None:
    context.patient_uuid = "uuid_patient_for_reading_post"
    reading_value = generate_reading_value(banding)
    context.reading_data = generate_reading_request(
        value=reading_value, banding=banding
    )
    context.response = post_bg_reading(
        patient_uuid=context.patient_uuid,
        reading_data=context.reading_data,
        context=context,
    )


@when("a {banding:str} BG reading is posted using api v1")
def create_bg_reading_v1(context: Context, banding: str) -> None:
    context.patient_uuid = "uuid_patient_for_reading_post"
    reading_value = generate_reading_value(banding)
    context.reading_data = generate_reading_request(
        value=reading_value, banding=banding
    )
    context.response = post_bg_reading_v1(
        patient_uuid=context.patient_uuid,
        reading_data=context.reading_data,
        context=context,
    )


@when("the same BG reading is posted")
def create_duplicate_bg_reading(context: Context) -> None:
    context.response = post_bg_reading(
        patient_uuid=context.patient_uuid,
        reading_data=context.reading_data,
        context=context,
    )


@when("the same BG reading is posted using api v1")
def create_duplicate_bg_reading_v1(context: Context) -> None:
    context.response = post_bg_reading_v1(
        patient_uuid=context.patient_uuid,
        reading_data=context.reading_data,
        context=context,
    )


@given("a NORMAL BG reading exists")
def normal_reading_exists(context: Context) -> None:
    context.patient_uuid = "uuid_patient_for_reading_post"
    reading_value = generate_reading_value("NORMAL")

    context.reading_data = generate_reading_request(
        value=reading_value,
        banding="NORMAL",
    )
    context.response = post_bg_reading(
        patient_uuid=context.patient_uuid,
        reading_data=context.reading_data,
        context=context,
    )
    assert_that(context.response.status_code).is_equal_to(200)
    context.reading_uuid = context.response.json()["uuid"]


@given(
    "readings for {count:int} days exist ({abnormal:int} ABNORMAL_READING messages are published to RabbitMQ)"
)
def many_days_readings(context: Context, count: int, abnormal: int) -> None:
    context.patient_uuid = "uuid_patient_for_reading_post"
    base_time = datetime.utcnow().replace(tzinfo=timezone.utc)

    context.responses = []
    context.multi_reading_data = []
    tags = itertools.cycle(
        (
            "BEFORE-BREAKFAST",
            "AFTER-BREAKFAST",
            "BEFORE-LUNCH",
            "AFTER-LUNCH",
            "BEFORE-DINNER",
            "AFTER-DINNER",
            "OTHER",
        )
    )
    bands = itertools.cycle(
        ("NORMAL", "LOW", "LOW", "HIGH", "HIGH", "NORMAL", "NORMAL")
    )

    for age in range(count):
        banding, tag = next(bands), next(tags)
        reading_value = generate_reading_value(banding)
        context.reading_data = generate_reading_request(
            value=reading_value,
            banding=banding,
            measured_time=base_time - timedelta(days=age),
            dose={"amount": 1, "medication_id": "uuid-for-meds"},
            comment=f"Reading {age} days ago",
            tag=tag,
        )
        context.multi_reading_data.insert(0, context.reading_data)
        response = post_bg_reading(
            patient_uuid=context.patient_uuid,
            reading_data=context.reading_data,
            context=context,
        )
        assert_that(response.status_code).is_equal_to(200)

        context.responses.insert(0, response)

    for i in range(abnormal):
        get_rabbitmq_message(context, RABBITMQ_MESSAGES["ABNORMAL_READING"])


@when(
    "the BG reading is updated with {comment:str?}, {dose:float?}, {prandial_tag:str?}",
)
def bg_reading_is_updated(
    context: Context, comment: str, dose: str, prandial_tag: str
) -> None:
    new_prandial_tag = generate_prandial_tag(prandial_tag) if prandial_tag else None
    new_meds = ([{"amount": dose, "medication_id": "uuid-for-meds"}]) if dose else None

    update_msg = {
        "comment": comment if comment else None,
        "doses": new_meds,
        "prandial_tag": new_prandial_tag,
    }
    context.response = update_bg_reading(
        update_msg,
        patient_uuid=context.patient_uuid,
        reading_uuid=context.reading_uuid,
        reading_data=update_msg,
        context=context,
    )
    assert_that(context.response.status_code).is_equal_to(200)

    # Update expected data for verification
    if comment:
        context.reading_data["comment"] = comment
    if dose:
        context.reading_data["doses"] += new_meds
    if prandial_tag:
        context.reading_data["prandial_tag"] = new_prandial_tag


@when("the {which:str} reading is retrieved")
def specific_reading_is_fetched(context: Context, which: str) -> None:
    context.response = get_specific_reading(
        patient_uuid=context.patient_uuid, which=which, context=context
    )
    assert_that(context.response.status_code).is_equal_to(200)
    context.reading_data = (
        context.multi_reading_data[0]
        if which == "earliest"
        else context.multi_reading_data[-1]
        if which == "latest"
        else context.multi_reading_data.find(lambda r: r["uuid"] == which)
    )


@when("the readings for the past {days:int} days are retrieved")
def recent_readings_are_fetched(context: Context, days: int) -> None:
    context.expected_readings = context.multi_reading_data[-days:]
    response = get_recent_readings(days=days, context=context)
    assert_that(response.status_code).is_equal_to(200)

    context.response_map = response.json()


@when("statistics for the past {days:int} days are retrieved")
def statistics_are_retrieved(context: Context, days: int) -> None:
    response = get_statistics(days=days, context=context)
    assert_that(response.status_code).is_equal_to(200)

    context.response_map = response.json()


@when("an {level:str} alert is generated")
def an_alert_is_generated(context: Context, level: str) -> None:
    response = process_alerts(
        {
            context.patient_uuid: {
                "red_alert": level == "RED",
                "amber_alert": level == "AMBER",
            }
        },
        context=context,
    )
    assert_that(response.status_code).is_equal_to(204)
