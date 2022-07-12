from typing import Dict, List

import requests
from behave import fixture
from behave.runner import Context
from environs import Env
from helpers.jwt import get_system_token
from requests import Response

BG_READINGS_API_HOST = Env().str("GDM_BG_READINGS_API_HOST")


@fixture
def request_session(context: Context) -> None:
    session = requests.Session()
    context.requests = session
    context.system_jwt = get_system_token()
    session.headers.update({"Authorization": f"Bearer {context.system_jwt}"})


def drop_data(context: Context) -> Response:
    response = context.requests.post(
        f"{BG_READINGS_API_HOST}/drop_data",
        json={},
        timeout=15,
    )
    response.raise_for_status()
    return response


def post_bg_reading(
    patient_uuid: str, reading_data: Dict, context: Context
) -> Response:
    response = context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v2/patient/{patient_uuid}/reading",
        json=reading_data,
        timeout=15,
    )
    return response


def post_bg_reading_v1(
    patient_uuid: str, reading_data: Dict, context: Context
) -> Response:
    response = context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/reading",
        json=reading_data,
        timeout=15,
    )
    return response


def update_bg_reading(
    update_msg: Dict,
    patient_uuid: str,
    reading_uuid: str,
    reading_data: Dict,
    context: Context,
) -> Response:
    response = context.requests.patch(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/reading/{reading_uuid}",
        json=reading_data,
        timeout=15,
    )
    return response


def get_specific_reading(patient_uuid: str, which: str, context: Context) -> Response:
    '''Get a specific reading `which` is the reading UUID, or "earliest" or "latest"'''
    response = context.requests.get(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/reading/{which}",
        timeout=15,
    )
    return response


def get_recent_readings(days: int, context: Context) -> Response:
    """Get readings for all patients for the specified period"""
    response = context.requests.get(
        f"{BG_READINGS_API_HOST}/gdm/v1/reading/recent",
        params={"days": days, "compact": False},
        timeout=15,
    )
    return response


def retrieve_patient_summaries(patient_uuids: List[str], context: Context) -> Response:
    response = context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/summary",
        json=patient_uuids,
        timeout=15,
    )
    return response


def create_hba1c_target(
    patient_uuid: str, target_data: Dict, context: Context
) -> Response:
    return context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c_target",
        json=target_data,
        timeout=15,
    )


def update_hba1c_target(
    patient_uuid: str, target_uuid: str, target_data: Dict, context: Context
) -> Response:
    return context.requests.patch(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c_target/{target_uuid}",
        json=target_data,
        timeout=15,
    )


def get_hba1c_targets_by_patient_uuid(patient_uuid: str, context: Context) -> Response:
    return context.requests.get(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c_target",
        timeout=15,
    )


def get_statistics(days: int, context: Context) -> Response:
    return context.requests.get(
        f"{BG_READINGS_API_HOST}/gdm/v1/reading/statistics",
        params={"days": days, "compact": True},
        timeout=15,
    )


def process_alerts(alerts_details: Dict[str, Dict], context: Context) -> Response:
    return context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/process_alerts",
        json=alerts_details,
        timeout=15,
    )


def process_activity_alerts(
    patient_id: str, patient: Dict, context: Context
) -> Response:
    return context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/process_activity_alerts/patient/{patient_id}",
        params={"publish_alert": False},
        json=patient,
        timeout=15,
    )


def clear_alerts(patient_id: str, context: Context) -> Response:
    return context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/clear_alerts/patient/{patient_id}",
        timeout=15,
    )
