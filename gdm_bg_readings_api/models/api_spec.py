from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask_batteries_included.helpers.apispec import (
    FlaskBatteriesPlugin,
    Identifier,
    initialise_apispec,
    openapi_schema,
)
from marshmallow import EXCLUDE, Schema, fields

from gdm_bg_readings_api.models.prandial_tag import PrandialTagOptions

gdm_bg_readings_api_spec: APISpec = APISpec(
    version="1.1.0",
    openapi_version="3.0.3",
    title="GDM BG Readings API",
    info={
        "description": "The GDM BG Readings API is responsible for storing and retrieving blood glucose readings."
    },
    plugins=[FlaskPlugin(), MarshmallowPlugin(), FlaskBatteriesPlugin()],
)

initialise_apispec(gdm_bg_readings_api_spec)


@openapi_schema(gdm_bg_readings_api_spec, {"nullable": True})
class PrandialTagRequest(Schema):
    class Meta:
        ordered = True

    value = fields.Integer(
        required=False,
        description="Integer representation of prandial tag",
        enum=[e.value for e in PrandialTagOptions],
        example=2,
    )
    uuid = fields.String(
        required=False,
        description="String representation of prandial tag",
        enum=["PRANDIAL-TAG-" + e.name.replace("_", "-") for e in PrandialTagOptions],
        example="PRANDIAL-TAG-BEFORE-BREAKFAST",
    )


class PrandialTagResponse(Identifier):
    class Meta:
        ordered = True

    value = fields.Integer(
        required=True,
        description="Integer representation of prandial tag",
        enum=[e.value for e in PrandialTagOptions],
        example=2,
    )
    description = fields.String(
        required=True,
        description="Description of prandial tag",
        example="Before breakfast",
    )


class Alert(Identifier):
    class Meta:
        ordered = True

    dismissed = fields.Boolean(
        required=True,
        description="Whether or not the alert has been dismissed",
        example=False,
    )


class ReadingMetadataRequest(Schema):
    class Meta:
        ordered = True

    control = fields.Boolean(
        required=True,
        description="Whether or not the reading was taken using control solution",
        example=False,
    )
    manual = fields.Boolean(
        required=True,
        description="Whether or not the reading was taken manually",
        example=False,
    )
    meter_serial_number = fields.String(
        required=False,
        allow_none=True,
        description="Serial number of the blood glucose meter with which the reading was taken",
        example="D8H7HSYIF7DE",
    )
    meter_model = fields.String(
        required=False,
        allow_none=True,
        description="Model of the blood glucose meter with which the reading was taken",
        example="Jazz Wireless",
    )
    manufacturer = fields.String(
        required=False,
        allow_none=True,
        description="Manufacturer of the blood glucose meter with which the reading was taken",
        example="AgaMatrix",
    )
    reading_is_correct = fields.Boolean(
        required=False,
        allow_none=True,
        description="If the reading on the meter matches the reading in the app as validated by the patient",
        example=True,
    )
    transmitted_reading = fields.Float(
        required=False,
        allow_none=True,
        description="Blood glucose value that was transmitted directly from the blood glucose meter to the app",
        example=5.6,
    )


class ReadingMetadataResponse(Identifier, ReadingMetadataRequest):
    class Meta:
        ordered = True


class ReadingBanding(Identifier):
    class Meta:
        ordered = True

    value = fields.Integer(
        required=True,
        description="Integer representation of banding",
        example=3,
    )
    description = fields.String(
        required=True,
        description="Description of banding",
        example="high",
    )


class ReadingCommonFields(Schema):
    class Meta:
        ordered = True

    measured_timestamp = fields.String(
        required=True,
        description="ISO8601 timestamp at which reading was taken",
        example="2020-01-01T00:00:00.000Z",
    )
    blood_glucose_value = fields.Float(
        required=True, description="Blood glucose reading value", example=5.5
    )
    units = fields.String(
        required=True,
        description="Blood glucose reading units",
        enum=["mmol/L", "mg/dL"],
        example="mmol/L",
    )
    comment = fields.String(
        required=False,
        allow_none=True,
        description="Comment associated with reading",
        example="I ate earlier than usual today!",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class DoseRequest(Schema):
    class Meta:
        description = "Dose request"
        ordered = True
        unknown = EXCLUDE

    medication_id = fields.String(
        required=True,
        description="Medication UUID",
        example="9a72d4bc-761a-460c-958c-9133bd38c854",
    )
    amount = fields.Float(
        required=True, description="Amount of medication", example=1.5
    )


@openapi_schema(gdm_bg_readings_api_spec)
class DoseResponse(Identifier, DoseRequest):
    class Meta:
        description = "Dose response"
        ordered = True
        unknown = EXCLUDE


@openapi_schema(gdm_bg_readings_api_spec)
class ReadingRequest(ReadingCommonFields):
    class Meta:
        description = "Reading request"
        unknown = EXCLUDE
        ordered = True

    prandial_tag = fields.Nested(
        PrandialTagRequest,
        required=False,
        allow_none=True,
        description="Prandial tag (meal label) for the reading",
    )
    doses = fields.List(
        fields.Nested(DoseRequest),
        required=False,
        allow_none=True,
        description="Medication doses associated with the reading",
    )
    reading_metadata = fields.Nested(
        ReadingMetadataRequest,
        required=False,
        allow_none=True,
        description="Metadata associated with the reading",
    )
    banding_id = fields.String(
        required=True,
        description="ID of the reading banding",
        enum=[
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
        ],
        example="BG-READING-BANDING-NORMAL",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class ReadingResponseCompact(Identifier, ReadingCommonFields):
    class Meta:
        description = "Reading response (compact)"
        unknown = EXCLUDE
        ordered = True

    patient_id = fields.String(
        required=True,
        description="Patient UUID",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )
    snoozed = fields.String(
        required=False,
        description="Whether or not the alert(s) resulting from this reading have been snoozed",
        example=True,
    )

    prandial_tag = fields.String(
        required=False,
        description="Prandial tag (meal label) id for the reading",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )
    reading_metadata = fields.Nested(
        ReadingMetadataResponse,
        required=False,
        description="Metadata associated with the reading",
    )
    reading_banding = fields.String(
        required=False,
        description="Banding (severity) id of the reading",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )

    red_alert = fields.String(
        Arequired=False,
        description="A red alert id associated with the reading",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )
    amber_alert = fields.String(
        required=False,
        description="An amber alert associated with the reading",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class ReadingResponse(Identifier, ReadingCommonFields):
    class Meta:
        description = "Reading response"
        unknown = EXCLUDE
        ordered = True

    patient_id = fields.String(
        required=True,
        description="Patient UUID",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )
    snoozed = fields.String(
        required=False,
        description="Whether or not the alert(s) resulting from this reading have been snoozed",
        example=True,
    )
    doses = fields.List(
        fields.Nested(DoseResponse),
        required=False,
        description="Medication doses associated with the reading",
    )
    prandial_tag = fields.Nested(
        PrandialTagResponse,
        required=False,
        description="Prandial tag (meal label) for the reading",
    )
    reading_metadata = fields.Nested(
        ReadingMetadataResponse,
        required=False,
        description="Metadata associated with the reading",
    )
    reading_banding = fields.Nested(
        ReadingBanding, required=False, description="Banding (severity) of the reading"
    )
    red_alert = fields.Nested(
        Alert, required=False, description="A red alert associated with the reading"
    )
    amber_alert = fields.Nested(
        Alert, required=False, description="An amber alert associated with the reading"
    )


@openapi_schema(gdm_bg_readings_api_spec)
class ReadingUpdateRequest(Schema):
    class Meta:
        description = "Reading update request"
        unknown = EXCLUDE
        ordered = True

    comment = fields.String(
        required=False,
        allow_none=True,
        description="Comment associated with reading",
        example="I ate earlier than usual today!",
    )
    prandial_tag = fields.Nested(
        PrandialTagRequest,
        required=False,
        allow_none=True,
        description="Prandial tag (meal label) for the reading",
    )
    doses = fields.List(
        fields.Nested(DoseRequest),
        required=False,
        allow_none=True,
        description="Medication doses associated with the reading",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cReadingCommonFields(Schema):
    class Meta:
        description = "Hba1c reading request"
        unknown = EXCLUDE
        ordered = True

    measured_timestamp = fields.AwareDateTime(
        required=True,
        description="ISO8601 timestamp at which reading was taken",
        example="2020-01-01T00:00:00.000Z",
    )
    value = fields.Float(required=True, description="Hba1c reading value", example=40.0)
    units = fields.String(
        required=True,
        description="Hba1c reading units",
        enum=["mmol/mol"],
        example="mmol/mol",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cReadingPatchRequest(Schema):
    class Meta:
        description = "Hba1c reading request"
        unknown = EXCLUDE
        ordered = True

    measured_timestamp = fields.AwareDateTime(
        required=False,
        description="ISO8601 timestamp at which reading was taken",
        example="2020-01-01T00:00:00.000Z",
    )
    value = fields.Float(
        required=False, description="Hba1c reading value", example=40.0
    )
    units = fields.String(
        required=False,
        description="Hba1c reading units",
        enum=["mmol/mol"],
        example="mmol/mol",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cReadingRequest(Hba1cReadingCommonFields):
    class Meta:
        description = "Hba1c reading request"
        unknown = EXCLUDE
        ordered = True


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cReadingResponse(Identifier, Hba1cReadingCommonFields):
    class Meta:
        description = "Hba1c reading response"
        unknown = EXCLUDE
        ordered = True

    patient_id = fields.String(
        required=True,
        description="Patient UUID",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cTargetRequest(Schema):
    class Meta:
        description = "Hba1c target request"
        unknown = EXCLUDE
        ordered = True

    value = fields.Float(required=True, description="Hba1c target value", example=40.0)
    units = fields.String(
        required=True,
        description="Hba1c target units",
        enum=["mmol/mol"],
        example="mmol/mol",
    )
    target_timestamp = fields.AwareDateTime(
        required=True,
        description="ISO8601 timestamp at which hba1c target was set",
        example="2020-01-01T00:00:00.000Z",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cTargetUpdate(Schema):
    class Meta:
        description = "Hba1c target update request"
        unknown = EXCLUDE
        ordered = True

    value = fields.Float(required=False, description="Hba1c target value", example=40.0)
    units = fields.String(
        required=False,
        description="Hba1c target units",
        enum=["mmol/mol"],
        example="mmol/mol",
    )
    target_timestamp = fields.AwareDateTime(
        required=False,
        description="ISO8601 timestamp at which hba1c target was set",
        example="2020-01-01T00:00:00.000Z",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class Hba1cTargetResponse(Identifier, Hba1cTargetRequest):
    class Meta:
        description = "Hba1c target response"
        unknown = EXCLUDE
        ordered = True

    patient_id = fields.String(
        required=True,
        description="Patient UUID",
        example="bfd1de2d-2a8d-464a-99bc-7c3fe8f881bc",
    )


@openapi_schema(gdm_bg_readings_api_spec)
class PatientResponse(Identifier):
    class Meta:
        description = "Patient response"
        unknown = EXCLUDE
        ordered = True

    suppress_reading_alerts_from = fields.String(
        required=True,
        allow_none=True,
        description="ISO8601 timestamp from when alerts were suppressed",
        example="2020-01-01T00:00:00.000Z",
    )
    suppress_reading_alerts_until = fields.String(
        required=True,
        allow_none=True,
        description="ISO8601 timestamp until when alerts were suppressed",
        example="2020-01-08T00:00:00.000Z",
    )
    current_red_alert = fields.Boolean(
        required=True,
        description="Whether or not the patient has an active red alert",
        example=True,
    )
    current_amber_alert = fields.Boolean(
        required=True,
        description="Whether or not the patient has an active amber alert",
        example=True,
    )
    current_activity_alert = fields.Boolean(
        required=True,
        description="Whether or not the patient has an active activity alert",
        example=True,
    )
    alert_now = fields.Boolean(
        required=False,
        description="Whether an alert has just been generated",
        example=True,
    )


@openapi_schema(gdm_bg_readings_api_spec)
class PatientSummaryResponse(PatientResponse):
    class Meta:
        description = "Patient summary response"
        unknown = EXCLUDE
        ordered = True

    latest_reading = fields.Nested(
        ReadingResponse, required=True, description="Latest reading"
    )


@openapi_schema(gdm_bg_readings_api_spec)
class PrandialTagUpdateRequest(Schema):
    class Meta:
        description = "Prandial tag update request"
        unknown = EXCLUDE
        ordered = True

    prandial_tag = fields.Nested(
        PrandialTagRequest,
        required=True,
        description="Prandial tag (meal label) for the reading",
    )
    banding_id = fields.String(
        required=False,
        description="ID of the reading banding",
        enum=[
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
        ],
        example="BG-READING-BANDING-NORMAL",
    )


class ReadingsPlan(Schema):
    class Meta:
        ordered = True

    created = fields.String(
        required=True,
        description="ISO8601 datetime of plan creation",
        exmaple="2017-01-01T00:00:00.000Z",
    )
    readings_per_day = fields.Integer(
        required=True, description="Number of readings to take per day", example=4
    )
    days_per_week_to_take_readings = fields.Integer(
        required=True, description="Number of days per week to take readings", example=7
    )


@openapi_schema(gdm_bg_readings_api_spec)
class ReadingsPlansRequest(Schema):
    class Meta:
        description = "Readings plans request"
        unknown = EXCLUDE
        ordered = True

    readings_plans = fields.List(fields.Nested(ReadingsPlan), required=True)


@openapi_schema(gdm_bg_readings_api_spec)
class ReadingStatistics(Schema):
    class Meta:
        description = "Reading statistics"
        unknown = EXCLUDE
        ordered = True

    min_reading = fields.Nested(
        ReadingResponse, required=True, description="Minimum blood glucose reading"
    )
    max_reading = fields.Nested(
        ReadingResponse, required=True, description="Maximum blood glucose reading"
    )
    readings_count = fields.Integer(
        required=True, description="Total number of readings"
    )
    readings_count_banding_normal = fields.Integer(
        required=True, description="Total number of readings banded as normal"
    )
