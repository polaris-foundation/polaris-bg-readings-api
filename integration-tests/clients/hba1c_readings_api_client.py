from typing import Dict

from behave.runner import Context
from clients.bg_readings_api_client import BG_READINGS_API_HOST
from requests import Response


def post_hba1c_reading(
    patient_uuid: str, reading_data: Dict, context: Context
) -> Response:
    response = context.requests.post(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c",
        json=reading_data,
        timeout=15,
    )
    return response


def patch_hba1c_reading(
    patient_uuid: str, reading_uuid: str, reading_data: Dict, context: Context
) -> Response:
    response = context.requests.patch(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c/{reading_uuid}",
        json=reading_data,
        timeout=15,
    )
    return response


def delete_hba1c_reading(
    patient_uuid: str, reading_uuid: str, context: Context
) -> Response:
    response = context.requests.delete(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c/{reading_uuid}",
        timeout=15,
    )
    return response


def get_hba1c_readings_by_patient_uuid(patient_uuid: str, context: Context) -> Response:
    response = context.requests.get(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c",
        timeout=15,
    )
    return response


def get_hba1c_reading_by_uuid(
    patient_uuid: str, reading_uuid: str, context: Context
) -> Response:
    response = context.requests.get(
        f"{BG_READINGS_API_HOST}/gdm/v1/patient/{patient_uuid}/hba1c/{reading_uuid}",
        timeout=15,
    )
    return response
