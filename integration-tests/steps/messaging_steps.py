from assertpy import assert_that, soft_assertions
from behave import given, then, use_fixture, use_step_matcher
from behave.runner import Context
from clients.rabbitmq_client import (
    RABBITMQ_MESSAGES,
    create_rabbitmq_connection,
    create_rabbitmq_queues,
    get_rabbitmq_message,
)
from helpers.readings_helper import assert_reading_body

use_step_matcher("re")


@given("RabbitMQ is running")
def create_rabbit_queues(context: Context) -> None:
    if not hasattr(context, "rabbit_connection"):
        context.rabbit_connection = use_fixture(create_rabbitmq_connection, context)

    if not hasattr(context, "rabbit_queues"):
        use_fixture(
            create_rabbitmq_queues,
            context,
            routing_keys=RABBITMQ_MESSAGES,
        )


@then(
    "(?:an)?(?P<count>\d*) ABNORMAL_READING message(?:s are| is) published to RabbitMQ"
)
def assert_abnormal_reading_message_published(context: Context, count: str) -> None:
    expected_count: int = int(count or "1")
    message = get_rabbitmq_message(context, RABBITMQ_MESSAGES["ABNORMAL_READING"])

    if not count:
        assert_reading_body(
            actual_reading_body=message, expected_reading_body=context.reading_data
        )
        with soft_assertions():
            assert_that(message).has_patient_id(context.patient_uuid).has_uuid(
                context.response.json()["uuid"]
            )

    # Additional messages are retrieved but not verified
    for i in range(expected_count - 1):
        message = get_rabbitmq_message(context, RABBITMQ_MESSAGES["ABNORMAL_READING"])


@then("a PATIENT_ALERT level (?P<level>\w+) message is published to RabbitMQ")
def assert_patient_alert_message_published(context: Context, level: str) -> None:
    message = get_rabbitmq_message(context, RABBITMQ_MESSAGES["PATIENT_ALERT"])

    with soft_assertions():
        assert_that(message).has_patient_uuid(context.patient_uuid).has_alert_type(
            level
        )
