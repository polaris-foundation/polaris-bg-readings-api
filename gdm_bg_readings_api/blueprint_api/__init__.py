from typing import Any, Dict, List

import flask
from flask import Blueprint, Response, jsonify, make_response
from flask_batteries_included.helpers import schema
from flask_batteries_included.helpers.routes import deprecated_route
from flask_batteries_included.helpers.security import protected_route
from flask_batteries_included.helpers.security.endpoint_security import (
    and_,
    key_present,
    match_keys,
    or_,
    scopes_present,
)
from she_logging import logger

from gdm_bg_readings_api.blueprint_api import controller
from gdm_bg_readings_api.models.dose import Dose
from gdm_bg_readings_api.models.reading import Reading

api_blueprint = Blueprint("gdm/v2", __name__)
api_blueprint_v1 = Blueprint("gdm/v1", __name__)


@api_blueprint.route("/patient/<patient_id>/reading", methods=["POST"])
@protected_route(
    and_(
        scopes_present(required_scopes="write:gdm_bg_reading"),
        or_(match_keys(patient_id="patient_id"), key_present("system_id")),
    )
)
def post_reading(
    patient_id: str, reading_data: Dict, compact: bool = False
) -> Response:
    """
    ---
    post:
      summary: Create new reading
      description: Create a new reading for a given patient using the details provided in the request body.
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          description: Patient UUID
          required: true
          schema:
            type: string
            example: cdda06c0-ccc4-4da0-b0b7-a8f1b20ede10
        - name: compact
          in: query
          required: false
          description: Whether readings in the response should be in compact form
          schema:
            type: boolean
            default: false
      requestBody:
        description: Reading details
        required: true
        content:
          application/json:
            schema:
                $ref: '#/components/schemas/ReadingRequest'
                x-body-name: reading_data
      responses:
        '200':
          description: New reading
          content:
            application/json:
              schema:
                oneOf:
                    - $ref: '#/components/schemas/ReadingResponse'
                    - $ref: '#/components/schemas/ReadingResponseCompact'
        '409':
          description: Duplicate reading
          headers:
            Location:
              description: URL of the original reading
              schema:
                type: string
          content:
            application/json:
              schema: Error
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.create_reading(
            patient_id=patient_id,
            reading_data=reading_data,
            compact=compact,
        )
    )


@deprecated_route(superseded_by="POST /gdm/v2/patient/<patient_id>/reading")
@api_blueprint_v1.route("/patient/<patient_id>/reading", methods=["POST"])
@protected_route(
    and_(
        scopes_present(required_scopes="write:gdm_bg_reading"),
        or_(match_keys(patient_id="patient_id"), key_present("system_id")),
    )
)
def post_reading_v1(
    patient_id: str, reading_data: Dict, compact: bool = False
) -> Response:
    """
    ---
    post:
      summary: Create new reading
      description: Create a new reading for a given patient using the details provided in the request body.
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          description: Patient UUID
          required: true
          schema:
            type: string
            example: cdda06c0-ccc4-4da0-b0b7-a8f1b20ede10
        - name: compact
          in: query
          required: false
          description: Whether readings in the response should be in compact form
          schema:
            type: boolean
            default: false
      requestBody:
        description: Reading details
        required: true
        content:
          application/json:
            schema:
                $ref: '#/components/schemas/ReadingRequest'
                x-body-name: reading_data
      responses:
        '200':
          description: New reading
          content:
            application/json:
              schema:
                oneOf:
                    - $ref: '#/components/schemas/ReadingResponse'
                    - $ref: '#/components/schemas/ReadingResponseCompact'
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.create_reading_v1(
            patient_id=patient_id, reading_data=reading_data, compact=compact
        )
    )


@api_blueprint_v1.route("/patient/<patient_id>", methods=["GET"])
@protected_route(
    or_(
        scopes_present(required_scopes="read:gdm_bg_reading_all"),
        and_(
            scopes_present(required_scopes="read:gdm_bg_reading"),
            match_keys(patient_id="patient_id"),
        ),
    )
)
def get_patient_by_uuid(patient_id: str) -> Response:
    """
    ---
    get:
      summary: Get patient details by UUID
      description: >-
        Get the details of the patient with the provided UUID. Note that this is not the full
        patient information, which can be found in the Services API.
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          description:  UUID
          schema:
            type: string
            example: 9eac08b3-e1ad-4f81-929d-ec1590c51181
      responses:
        '200':
          description: Patient details
          content:
            application/json:
              schema: PatientResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(controller.get_patient(patient_id))


@api_blueprint_v1.route("/patient/<patient_id>/reading/<reading_id>", methods=["GET"])
@protected_route(
    or_(
        scopes_present(required_scopes="read:gdm_bg_reading_all"),
        and_(
            scopes_present(required_scopes="read:gdm_bg_reading"),
            or_(match_keys(patient_id="patient_id"), key_present("system_id")),
        ),
    )
)
def get_reading_by_uuid(patient_id: str, reading_id: str) -> Response:
    """
    ---
    get:
      summary: Get reading by UUID
      description: Get a patient's reading by UUID
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
        - name: reading_id
          in: path
          required: true
          description: Reading UUID
          schema:
            type: string
            example: 5d8250bb-1d1d-4aa5-86ed-38a5af1015a4
      responses:
        '200':
          description: Requested reading
          content:
            application/json:
              schema: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.get_reading_by_uuid(patient_uuid=patient_id, reading_uuid=reading_id)
    )


@api_blueprint_v1.route("/patient/<patient_id>/reading", methods=["GET"])
@protected_route(
    or_(
        scopes_present(required_scopes="read:gdm_bg_reading_all"),
        and_(
            scopes_present(required_scopes="read:gdm_bg_reading"),
            or_(match_keys(patient_id="patient_id"), key_present("system_id")),
        ),
    )
)
def get_readings(patient_id: str) -> Response:
    """
    ---
    get:
      summary: Get patient readings
      description: Get all readings for the patient with the provided UUID
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      responses:
        '200':
          description: List of readings
          content:
            application/json:
              schema:
                type: array
                items: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.retrieve_readings_for_patient_with_tag(
            patient_id=patient_id, prandial_tag_value=None
        )
    )


@api_blueprint_v1.route(
    "/patient/<patient_id>/reading/filter/<prandial_tag>", methods=["GET"]
)
@protected_route(
    or_(
        scopes_present(required_scopes="read:gdm_bg_reading_all"),
        and_(
            scopes_present(required_scopes="read:gdm_bg_reading"),
            or_(match_keys(patient_id="patient_id"), key_present("system_id")),
        ),
    )
)
def get_readings_with_filter(patient_id: str, prandial_tag: str = None) -> Response:
    """
    ---
    get:
      summary: Get filtered patient readings
      description: Get readings for the patient with the provided UUID, filtered by prandial tag
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
        - name: prandial_tag
          in: path
          required: true
          description: An integer representing the prandial tag
          schema:
            type: integer
            enum: [0, 1, 2, 3, 4, 5, 6, 7]
            example: 2
      responses:
        '200':
          description: List of readings
          content:
            application/json:
              schema:
                type: array
                items: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.retrieve_readings_for_patient_with_tag(
            patient_id=patient_id, prandial_tag_value=prandial_tag
        )
    )


@api_blueprint_v1.route("/reading/recent", methods=["GET"])
@protected_route(scopes_present("read:gdm_bg_reading_all"))
def retrieve_readings_for_period(days: int = 7, compact: bool = True) -> Response:
    """
    ---
    get:
      summary: Get recent readings
      description: Get recent readings for each patient for the specified number of previous days
      tags: [reading]
      parameters:
        - name: days
          in: query
          required: false
          description: Last number of days for which to retrieve readings
          schema:
            type: integer
            default: 7
        - name: compact
          in: query
          required: false
          description: Whether readings in the response should be in compact form
          schema:
            type: boolean
            default: true
      responses:
        '200':
          description: Map of patient UUID to recent readings
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  $ref: '#/components/schemas/ReadingResponse'
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(controller.retrieve_readings_for_period(days=days, compact=compact))


@api_blueprint_v1.route("/reading/statistics", methods=["GET"])
@protected_route(scopes_present("read:gdm_bg_reading_all"))
def retrieve_statistics_for_period(days: int = 7, compact: bool = True) -> Response:
    """
    ---
    get:
      summary: Get reading statistics
      description: >-
        Get per-patient reading statistics for the specified number of days. This includes minimum
        and maximum reading values, the total number of readings, and the number of readings banded
        as normal.
      tags: [reading]
      parameters:
        - name: days
          in: query
          required: false
          description: Last number of days for which to retrieve statistics
          schema:
            type: integer
            default: 7
        - name: compact
          in: query
          required: false
          description: Whether readings in the response should be in compact form
          schema:
            type: boolean
            default: true
      responses:
        '200':
          description: Map of patient UUID to reading statistics
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  $ref: '#/components/schemas/ReadingStatistics'
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.retrieve_statistics_for_period(days=days, compact=compact)
    )


@api_blueprint_v1.route("/patient/<patient_id>/reading/latest", methods=["GET"])
@protected_route(
    or_(
        scopes_present(required_scopes="read:gdm_bg_reading_all"),
        and_(
            scopes_present(required_scopes="read:gdm_bg_reading"),
            or_(match_keys(patient_id="patient_id"), key_present("system_id")),
        ),
    )
)
def get_latest_reading(patient_id: str) -> Response:
    """
    ---
    get:
      summary: Get latest reading for patient
      description: Get the latest reading for the patient with the provided UUID
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      responses:
        '200':
          description: Most recent reading
          content:
            application/json:
              schema: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.retrieve_latest_reading_for_patient(patient_id=patient_id)
    )


@api_blueprint_v1.route("/patient/<patient_id>/reading/earliest", methods=["GET"])
@protected_route(
    or_(
        scopes_present(required_scopes="read:gdm_bg_reading_all"),
        and_(
            scopes_present(required_scopes="read:gdm_bg_reading"),
            or_(match_keys(patient_id="patient_id"), key_present("system_id")),
        ),
    )
)
def get_first_reading(patient_id: str) -> Response:
    """
    ---
    get:
      summary: Get earliest reading for patient
      description: Get the earliest reading for the patient with the provided UUID
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      responses:
        '200':
          description: Earliest reading
          content:
            application/json:
              schema: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(controller.retrieve_first_reading_for_patient(patient_id=patient_id))


@api_blueprint_v1.route("/patient/summary", methods=["POST"])
@protected_route(scopes_present(required_scopes="read:gdm_bg_reading_all"))
def retrieve_patient_summaries(patient_ids: List[str]) -> Response:
    """
    ---
    post:
      summary: Retrieve patient summaries
      description: >-
        Retrieves a summary of patient and latest reading details for the patients
        with the UUIDs provided in the request body.
      tags: [reading]
      requestBody:
        description: List of patient UUIDs
        required: true
        content:
          application/json:
            schema:
              type: array
              x-body-name: patient_ids
              items:
                type: string
              example: ["d461f6c1-f642-465e-8e5c-1058db58ec5b"]
      responses:
        '200':
          description: Map of patient UUID to summary
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  $ref: '#/components/schemas/PatientSummaryResponse'
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(controller.retrieve_patient_summaries(patient_ids=patient_ids))


@api_blueprint_v1.route("/patient/<patient_id>/reading/<reading_id>", methods=["PATCH"])
@protected_route(
    and_(
        scopes_present(required_scopes="write:gdm_bg_reading"),
        or_(match_keys(patient_id="patient_id"), key_present("system_id")),
    )
)
def patch_reading(patient_id: str, reading_id: str) -> Response:
    """
    ---
    patch:
      summary: Update reading
      description: Update the reading with the provided UUID using the details in the request body.
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
        - name: reading_id
          in: path
          required: true
          description: Reading UUID
          schema:
            type: string
            example: 5d8250bb-1d1d-4aa5-86ed-38a5af1015a4
      requestBody:
        description: Reading update
        required: true
        content:
          application/json:
            schema: ReadingUpdateRequest
      responses:
        '200':
          description: Updated reading
          content:
            application/json:
              schema: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error

    """
    reading_data: Dict = schema.update(**Reading.schema())
    return jsonify(
        controller.update_reading(
            patient_id=patient_id, reading_id=reading_id, reading_data=reading_data
        )
    )


@api_blueprint_v1.route(
    "/patient/<patient_id>/reading/<reading_id>/dose", methods=["POST"]
)
@protected_route(
    and_(
        scopes_present(required_scopes="write:gdm_bg_reading"),
        or_(match_keys(patient_id="patient_id"), key_present("system_id")),
    )
)
def post_dose_to_reading(patient_id: str, reading_id: str) -> Response:
    """
    ---
    post:
      summary: Add dose to reading
      description: Add the dose with the details provided in the request body to the reading specified by UUID.
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
        - name: reading_id
          in: path
          required: true
          description: Reading UUID
          schema:
            type: string
            example: 5d8250bb-1d1d-4aa5-86ed-38a5af1015a4
      requestBody:
        description: Dose details
        required: true
        content:
          application/json:
            schema: DoseRequest
      responses:
        '200':
          description: New dose
          content:
            application/json:
              schema: DoseResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    dose_details: Dict = schema.post(**Dose.schema())
    return jsonify(
        controller.add_dose_to_reading(
            patient_id=patient_id, reading_id=reading_id, dose_data=dose_details
        )
    )


@api_blueprint_v1.route(
    "/patient/<patient_id>/reading/<reading_id>/dose/<dose_id>", methods=["PATCH"]
)
@protected_route(
    and_(
        scopes_present(required_scopes="write:gdm_bg_reading"),
        or_(match_keys(patient_id="patient_id"), key_present("system_id")),
    )
)
def patch_dose_on_reading(patient_id: str, reading_id: str, dose_id: str) -> Response:
    """
    ---
    patch:
      summary: Update dose for reading
      description: Update the dose with the specified UUID using the details provided in the request body.
      tags: [reading]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
        - name: reading_id
          in: path
          required: true
          description: Reading UUID
          schema:
            type: string
            example: 5d8250bb-1d1d-4aa5-86ed-38a5af1015a4
        - name: dose_id
          in: path
          required: true
          description: Dose UUID
          schema:
            type: string
            example: e30ce361-39ab-483c-a5ac-246cacf871d6
      requestBody:
        description: Dose update
        required: true
        content:
          application/json:
            schema: DoseRequest
      responses:
        '200':
          description: Updated dose
          content:
            application/json:
              schema: DoseResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    dose_update: Dict = schema.update(**Dose.schema())
    return jsonify(
        controller.update_dose_on_reading(
            patient_id=patient_id,
            reading_id=reading_id,
            dose_id=dose_id,
            dose_data=dose_update,
        )
    )


### ALERTS


@api_blueprint_v1.route("/clear_alerts/patient/<patient_id>", methods=["POST"])
@protected_route(scopes_present(required_scopes="write:gdm_alert"))
def clear_alerts_for_patient(patient_id: str) -> Response:
    """
    ---
    post:
      summary: Clear patient alerts
      description: >-
        Clear alerts (both "counts" and "percentages" alerts) for the patient with the provided UUID.
      tags: [alert]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      responses:
        '200':
          description: Alerts cleared
          content:
            application/json:
              schema:
                type: object
                properties:
                  completed:
                    type: boolean
                    description: Whether the alerts were cleared successfully
                    example: true
                  suppress_reading_alerts_from:
                    type: string
                    description: ISO8601 timestamp from when alerts were suppressed
                    example: 2020-01-01T00:00:00.000Z
                  suppress_reading_alerts_until:
                    type: string
                    description: ISO8601 timestamp until when alerts were suppressed
                    example: 2020-01-08T00:00:00.000Z
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    logger.debug("Clearing alerts for patient with UUID %s", patient_id)
    return jsonify(controller.clear_alerts_for_patient(patient_id=patient_id))


@api_blueprint_v1.route("/process_alerts/reading/<reading_id>", methods=["POST"])
@protected_route(scopes_present(required_scopes="write:gdm_alert"))
def add_counts_alerts_to_reading(reading_id: str) -> Response:
    """
    ---
    post:
      summary: Process reading counts alerts
      description: Process the "counts" alerts for the reading with the specified UUID.
      tags: [alert]
      parameters:
        - name: reading_id
          in: path
          required: true
          description: Reading UUID
          schema:
            type: string
            example: 5d8250bb-1d1d-4aa5-86ed-38a5af1015a4
      responses:
        '200':
          description: Alerts processed
          content:
            application/json:
              schema: ReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    logger.debug("Checking 'counts' alerts for reading with UUID %s", reading_id)
    return jsonify(controller.process_counts_alerts_for_reading(reading_id=reading_id))


@api_blueprint_v1.route(
    "/process_activity_alerts/patient/<patient_id>", methods=["POST"]
)
@protected_route(scopes_present(required_scopes="write:gdm_alert"))
def process_activity_alert_for_patient(
    patient_id: str, readings_plans_request: Dict[str, List]
) -> Response:
    """
    ---
    post:
      summary: Process patient activity alerts
      description: >-
        Process the "activity" alerts for the patient with the specified UUID, using the
        readings plans in the request body to determine the expected number of readings.
      tags: [alert]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      requestBody:
        description: List of readings plans
        required: true
        content:
          application/json:
            schema:
                $ref: '#/components/schemas/ReadingsPlansRequest'
                x-body-name: readings_plans_request
      responses:
        '200':
          description: Alerts processed
          content:
            application/json:
              schema: PatientResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    logger.debug("Processing activity alerts for patient with UUID %s", patient_id)
    readings_plans: List = readings_plans_request.get("readings_plans", [])
    if not readings_plans or not isinstance(readings_plans, List):
        raise ValueError(f"No readings plan(s) supplied")

    logger.info(
        "Found %d readings plan(s) for patient with UUID %s",
        len(readings_plans),
        patient_id,
    )

    return jsonify(
        controller.process_activity_alerts_for_patient(
            patient_id=patient_id,
            readings_plans=readings_plans,
        )
    )


@api_blueprint_v1.route("/process_alerts", methods=["POST"])
@protected_route(scopes_present(required_scopes="write:gdm_alert"))
def process_percentages_alerts(alerts_map: Dict) -> Response:
    """
    ---
    post:
      summary: Process percentages alerts
      description: Process the "percentages" alerts for the group of patients specified in the request body.
      tags: [alert]
      requestBody:
        description: Map of patient UUID to alert details
        required: true
        content:
          application/json:
            schema:
              type: object
              x-body-name: alerts_map
              additionalProperties:
                type: object
                properties:
                  red_alert:
                    type: boolean
                    description: Whether the patient should have a red alert
                    example: True
                  amber_alert:
                    type: boolean
                    description: Whether the patient should have an ambere alert
                    example: False
                required:
                  - red_alert
                  - amber_alert
      responses:
        '204':
          description: Alerts processed
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    if not alerts_map:
        raise ValueError("Request body is empty")
    controller.process_percentages_alerts(alerts_data=alerts_map)
    return make_response("", 204)


@api_blueprint_v1.route("/patient/<patient_id>/hba1c", methods=["POST"])
@protected_route(scopes_present(required_scopes="write:gdm_bg_reading"))
def post_hba1c_reading(patient_id: str, reading_data: Dict) -> Response:
    """
    ---
    post:
      summary: Create new Hba1c reading
      description: Create a new Hba1c reading for a given patient using the details provided in the request body.
      tags: [hba1c]
      parameters:
        - name: patient_id
          in: path
          description: Patient UUID
          required: true
          schema:
            type: string
            example: cdda06c0-ccc4-4da0-b0b7-a8f1b20ede10
      requestBody:
        description: Hba1c reading details
        required: true
        content:
          application/json:
            schema:
                $ref: '#/components/schemas/Hba1cReadingRequest'
                x-body-name: reading_data
      responses:
        '201':
          description: New Hba1c reading
          headers:
            Location:
              description: The location of the created Hba1c reading
              schema:
                type: string
                example: http://server/gdm/v1/patient/bb747396-3b5a-4891-9547-496984ab1a95/hba1c/1f441bf6-81e4-4d85-9f85-d967a6f363c3
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    hba1c_reading: Dict = controller.create_hba1c_reading(
        patient_uuid=patient_id, reading_data=reading_data
    )

    response: Response = flask.Response(status=201)
    response.headers[
        "Location"
    ] = f"/gdm/v1/patient/{hba1c_reading['patient_id']}/hba1c/{hba1c_reading['uuid']}"
    return response


@api_blueprint_v1.route("/patient/<patient_id>/hba1c", methods=["GET"])
@protected_route(scopes_present(required_scopes="read:gdm_bg_reading_all"))
def get_hba1c_readings(patient_id: str) -> Response:
    """
    ---
    get:
      summary: Get patient Hba1c readings
      description: Get all Hba1c readings for the patient with the provided UUID
      tags: [hba1c]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      responses:
        '200':
          description: List of Hba1c readings
          content:
            application/json:
              schema:
                type: array
                items: Hba1cReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.retrieve_hba1c_readings_for_patient(patient_uuid=patient_id)
    )


@api_blueprint_v1.route(
    "/patient/<patient_id>/hba1c/<hba1c_reading_id>", methods=["GET"]
)
@protected_route(scopes_present(required_scopes="read:gdm_bg_reading_all"))
def get_hba1c_reading_by_uuid(patient_id: str, hba1c_reading_id: str) -> Response:
    """
    ---
    get:
      summary: Get Hba1c reading by UUID
      description: Get a patient's Hba1c reading by UUID
      tags: [hba1c]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
        - name: hba1c_reading_id
          in: path
          required: true
          description: Hba1c reading UUID
          schema:
            type: string
            example: 5d8250bb-1d1d-4aa5-86ed-38a5af1015a4
      responses:
        '200':
          description: Requested Hba1c reading
          content:
            application/json:
              schema: Hba1cReadingResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.get_hba1c_reading_by_uuid(
            patient_uuid=patient_id, hba1c_reading_uuid=hba1c_reading_id
        )
    )


@api_blueprint_v1.route(
    "/patient/<patient_id>/hba1c/<hba1c_reading_id>", methods=["PATCH"]
)
@protected_route(scopes_present(required_scopes="write:gdm_bg_reading"))
def patch_hba1c_reading(
    patient_id: str, hba1c_reading_id: str, reading_data: Dict
) -> Response:
    """
    ---
    patch:
      summary: Update Hba1c reading
      description: >-
        Update the Hba1c reading to the field values provided in the request body
        for a given patient and reading identified by the UUIDs in the request path
      tags: [hba1c]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: '18439f36-ffa9-42ae-90de-0beda299cd37'
        - name: hba1c_reading_id
          in: path
          required: true
          description: Hba1c reading UUID
          schema:
            type: string
            example: '15439f36-ffa9-42ae-90de-0beda299cd38'
      requestBody:
        description: JSON body containing the Hba1c reading
        required: true
        content:
          application/json:
            schema:
                $ref: '#/components/schemas/Hba1cReadingPatchRequest'
                x-body-name: reading_data
      responses:
        '204':
            description: Hba1c reading updated
        default:
          description: >-
              Error, e.g. 400 Bad Request, 404 Not Found, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    if not reading_data:
        raise ValueError("No fields provided in update request")

    controller.update_hba1c_reading(
        patient_uuid=patient_id,
        hba1c_reading_uuid=hba1c_reading_id,
        reading_data=reading_data,
    )
    return flask.Response(status=204)


@api_blueprint_v1.route(
    "/patient/<patient_id>/hba1c/<hba1c_reading_id>", methods=["DELETE"]
)
@protected_route(scopes_present(required_scopes="write:gdm_bg_reading"))
def delete_hba1c_reading(patient_id: str, hba1c_reading_id: str) -> Response:
    """---
    delete:
      summary: Delete Hba1c reading
      description: Delete a Hba1c reading by UUID
      tags: [hba1c]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: '18439f36-ffa9-42ae-90de-0beda299cd37'
        - name: hba1c_reading_id
          in: path
          required: true
          description: Hba1c reading UUID
          schema:
            type: string
            example: '15439f36-ffa9-42ae-90de-0beda299cd38'
      responses:
        '204':
          description: Hba1c reading deleted
        default:
          description: >-
              Error, e.g. 400 Bad Request, 404 Not Found, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    controller.delete_hba1c_reading(
        patient_uuid=patient_id, hba1c_reading_uuid=hba1c_reading_id
    )
    return flask.Response(status=204)


@api_blueprint_v1.route("/patient/<patient_id>/hba1c_target", methods=["POST"])
@protected_route(scopes_present(required_scopes="write:gdm_bg_reading"))
def post_hba1c_target(
    patient_id: str, hba1c_target_details: Dict[str, Any]
) -> Response:
    """
    ---
    post:
      summary: Create new Hba1c target
      description: Create a new Hba1c target for a given patient using the details provided in the request body.
      tags: [hba1c-target]
      parameters:
        - name: patient_id
          in: path
          description: Patient UUID
          required: true
          schema:
            type: string
            example: cdda06c0-ccc4-4da0-b0b7-a8f1b20ede10
      requestBody:
        description: Hba1c target details
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Hba1cTargetRequest'
              x-body-name: hba1c_target_details
      responses:
        '201':
          description: New Hba1c target
          headers:
            Location:
              description: The location of the created Hba1c target
              schema:
                type: string
                example: http://server/gdm/v1/patient/bb747396-3b5a-4891-9547-496984ab1a95/hba1c_target/76b2c0cc-991b-4ac2-94df-7bfbd888bf1f
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    hba1c_target: Dict = controller.create_hba1c_target(
        patient_uuid=patient_id, target_data=hba1c_target_details
    )
    response: Response = flask.Response(status=201)
    response.headers[
        "Location"
    ] = f"/gdm/v1/patient/{hba1c_target['patient_id']}/hba1c_target/{hba1c_target['uuid']}"
    return response


@api_blueprint_v1.route("/patient/<patient_id>/hba1c_target", methods=["GET"])
@protected_route(scopes_present(required_scopes="read:gdm_bg_reading_all"))
def get_hba1c_targets(patient_id: str) -> Response:
    """
    ---
    get:
      summary: Get patient Hba1c targets
      description: Get all Hba1c targets for the patient with the provided UUID
      tags: [hba1c-target]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: 3c0cb994-f5f6-4910-b654-0d23f4b5e6c8
      responses:
        '200':
          description: List of Hba1c targets
          content:
            application/json:
              schema:
                type: array
                items: Hba1cTargetResponse
        default:
          description: >-
              Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    return jsonify(
        controller.retrieve_hba1c_targets_for_patient(patient_uuid=patient_id)
    )


@api_blueprint_v1.route(
    "/patient/<patient_id>/hba1c_target/<hba1c_target_id>", methods=["PATCH"]
)
@protected_route(scopes_present(required_scopes="write:gdm_bg_reading"))
def patch_hba1c_target(
    patient_id: str, hba1c_target_id: str, hba1c_target_details: Dict[str, Any]
) -> Response:
    """
    ---
    patch:
      summary: Update Hba1c target
      description: >-
        Update the Hba1c target to the field values provided in the request body
        for a given patient and target identified by the UUIDs in the request path
      tags: [hba1c-target]
      parameters:
        - name: patient_id
          in: path
          required: true
          description: Patient UUID
          schema:
            type: string
            example: '18439f36-ffa9-42ae-90de-0beda299cd37'
        - name: hba1c_target_id
          in: path
          required: true
          description: Hba1c target UUID
          schema:
            type: string
            example: '76b2c0cc-991b-4ac2-94df-7bfbd888bf1f'
      requestBody:
        description: JSON body containing the Hba1c target
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Hba1cTargetUpdate'
              x-body-name: hba1c_target_details
      responses:
        '204':
            description: Hba1c target updated
        default:
          description: >-
              Error, e.g. 400 Bad Request, 404 Not Found, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    if not hba1c_target_details:
        raise ValueError("No fields provided in update request")
    controller.update_hba1c_target(
        patient_uuid=patient_id,
        hba1c_target_uuid=hba1c_target_id,
        target_data=hba1c_target_details,
    )
    return flask.Response(status=204)
