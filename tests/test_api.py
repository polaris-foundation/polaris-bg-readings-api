import datetime
from typing import Any, Callable, Dict, List, Optional

import pytest
from flask.testing import FlaskClient
from flask_batteries_included.helpers import generate_uuid
from mock import Mock
from pytest_mock import MockFixture

from gdm_bg_readings_api.blueprint_api import controller


@pytest.mark.usefixtures()
class TestApi:
    @pytest.fixture(autouse=True)
    def mock_bearer_validation(self, mocker: MockFixture) -> Any:
        from jose import jwt

        mocked = mocker.patch.object(jwt, "get_unverified_claims")
        mocked.return_value = {
            "sub": "1234567890",
            "name": "John Doe",
            "iat": 1_516_239_022,
            "iss": "http://localhost/",
        }
        return mocked

    def test_wrong_methods(self, client: FlaskClient) -> None:
        method_list: List[Callable] = [
            client.patch,
            client.put,
            client.delete,
        ]
        for method in method_list:
            response = method(
                "/gdm/v1/patient/patient-uuid/reading",
                headers={"Authorization": "Bearer TOKEN"},
            )
            assert response.status_code == 405

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        reading_dict_in: Dict,
        patient_uuid: str,
        version: str,
    ) -> None:
        mock_create: Mock = mocker.patch.object(
            controller,
            f"create_reading{'_' + version if version == 'v1' else ''}",
            return_value={"uuid": generate_uuid()},
        )
        response = client.post(
            f"/gdm/{version}/patient/{patient_uuid}/reading",
            json=reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_create.call_count == 1
        mock_create.assert_called_with(
            patient_id=patient_uuid, reading_data=reading_dict_in, compact=False
        )

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_compact_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        reading_dict_in: Dict,
        patient_uuid: str,
        version: str,
    ) -> None:
        mock_create: Mock = mocker.patch.object(
            controller,
            f"create_reading{'_' + version if version == 'v1' else ''}",
            return_value={"uuid": generate_uuid()},
        )
        response = client.post(
            f"/gdm/{version}/patient/{patient_uuid}/reading?compact=True",
            json=reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_create.call_count == 1
        mock_create.assert_called_with(
            patient_id=patient_uuid, reading_data=reading_dict_in, compact=True
        )

    @pytest.mark.parametrize(
        "missing_field",
        ["measured_timestamp", "units", "blood_glucose_value"],
    )
    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_missing_fields_400(
        self,
        client: FlaskClient,
        reading_dict_in: Dict,
        patient_uuid: str,
        missing_field: str,
        version: str,
    ) -> None:
        del reading_dict_in[missing_field]
        response = client.post(
            f"/gdm/{version}/patient/{patient_uuid}/reading",
            json=reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "prandial_tag,expected",
        [
            (None, 200),
            (12, 400),
            ({"value": "something"}, 400),
            ({"value": 99}, 400),
            ({"value": 3}, 200),
        ],
    )
    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_prandial_tag(
        self,
        client: FlaskClient,
        reading_dict_in: Dict,
        patient_uuid: str,
        prandial_tag: Any,
        expected: int,
        version: str,
    ) -> None:
        reading_dict_in["prandial_tag"] = prandial_tag
        response = client.post(
            f"/gdm/{version}/patient/{patient_uuid}/reading",
            json=reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == expected

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_extra_key_400(
        self,
        client: FlaskClient,
        reading_dict_in: Dict,
        patient_uuid: str,
        version: str,
    ) -> None:
        reading_dict_in["extra"] = "key"
        response = client.post(
            f"/gdm/{version}/patient/{patient_uuid}/reading",
            json=reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_bad_timestamp_400(
        self,
        client: FlaskClient,
        reading_dict_in: Dict,
        patient_uuid: str,
        version: str,
    ) -> None:
        reading_dict_in["measured_timestamp"] = "t1m3st4mp"
        response = client.post(
            f"/gdm/{version}/patient/{patient_uuid}/reading",
            json=reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_with_prandial_tag_uuid_success(
        self, client: FlaskClient, version: str
    ) -> None:
        reading_data = {
            "blood_glucose_value": 5.5,
            "units": "mmol/L",
            "measured_timestamp": datetime.datetime.now().isoformat() + "Z",
            "prandial_tag": {"uuid": "PRANDIAL-TAG-AFTER-BREAKFAST"},
            "banding_id": "BG-READING-BANDING-NORMAL",
        }
        response = client.post(
            f"/gdm/{version}/patient/123/reading",
            json=reading_data,
            headers={"Authorization": "Bearer TOKEN"},
        )

        assert response.json
        assert response.status_code == 200
        assert response.json["prandial_tag"]["uuid"] == "PRANDIAL-TAG-AFTER-BREAKFAST"
        assert response.json["prandial_tag"]["value"] == 2

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_with_no_banding_id_failure(
        self, client: FlaskClient, version: str
    ) -> None:
        reading_data = {
            "blood_glucose_value": 5.5,
            "units": "mmol/L",
            "measured_timestamp": datetime.datetime.now().isoformat() + "Z",
            "prandial_tag": {"uuid": "PRANDIAL-TAG-AFTER-BREAKFAST"},
        }
        response = client.post(
            f"/gdm/{version}/patient/123/reading",
            json=reading_data,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_post_reading_prandial_tag_unknown(
        self, client: FlaskClient, version: str
    ) -> None:
        reading_data = {
            "blood_glucose_value": 5.5,
            "units": "mmol/L",
            "measured_timestamp": datetime.datetime.now().isoformat() + "Z",
            "prandial_tag": {"uuid": "NOT-A-REAL-TAG"},
            "banding_id": "BG-READING-BANDING-NORMAL",
        }
        response = client.post(
            f"/gdm/{version}/patient/123/reading",
            json=reading_data,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_post_reading_v1_deduplication(self, client: FlaskClient) -> None:
        results = {}
        uuid = None
        for i in range(5):
            reading_data = {
                "blood_glucose_value": 5.5,
                "units": "mmol/L",
                "measured_timestamp": "2000-01-01T01:01:01.000Z",
                "banding_id": "BG-READING-BANDING-NORMAL",
            }

            response = client.post(
                "/gdm/v1/patient/123/reading",
                json=reading_data,
                headers={"Authorization": "Bearer TOKEN"},
            )
            assert response.status_code == 200

            assert response.json
            uuid = response.json["uuid"]
            results[uuid] = response.json

        assert results
        assert len(results) == 1
        assert results[uuid]["blood_glucose_value"] == 5.5

    def test_post_reading_duplicate(self, client: FlaskClient) -> None:
        # first attempt
        reading_data = {
            "blood_glucose_value": 5.5,
            "units": "mmol/L",
            "measured_timestamp": datetime.datetime.now().isoformat() + "Z",
            "banding_id": "BG-READING-BANDING-NORMAL",
        }
        response = client.post(
            "/gdm/v2/patient/123/reading",
            json=reading_data,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200

        # posting a duplicate
        response = client.post(
            "/gdm/v2/patient/123/reading",
            json=reading_data,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 409
        assert response.json

        # getting metadata
        msg: str = response.json.get("message")
        assert msg
        assert "Duplicate reading found" in msg

        extra: Dict = response.json.get("extra")
        assert extra
        assert "reading_id" in extra
        reading_id: Optional[str] = extra.get("reading_id")
        assert reading_id

        assert response.headers
        location: Optional[str] = response.headers.get("Location")
        assert location
        assert reading_id in location

        # ensuring the location points to the correct reading
        response = client.get(location, headers={"Authorization": "Bearer TOKEN"})
        assert response.status_code == 200
        assert response.json
        response_reading_id: str = response.json["uuid"]
        assert response_reading_id == reading_id

    def test_get_reading_by_uuid(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        reading_uuid: str = generate_uuid()
        mock_get: Mock = mocker.patch.object(
            controller,
            "get_reading_by_uuid",
            return_value=[{"uuid": generate_uuid()}],
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/reading/{reading_uuid}",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_get.call_count
        mock_get.assert_called_with(
            patient_uuid=patient_uuid, reading_uuid=reading_uuid
        )

    def test_get_readings_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_readings_for_patient_with_tag",
            return_value=[{"uuid": generate_uuid()}],
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/reading",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert mock_retrieve.call_count
        mock_retrieve.assert_called_with(
            patient_id=patient_uuid, prandial_tag_value=None
        )

    def test_get_readings_recent_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_get: Mock = mocker.patch.object(
            controller,
            "retrieve_readings_for_period",
            return_value={patient_uuid: [{"uuid": generate_uuid()}]},
        )
        response = client.get(
            "/gdm/v1/reading/recent", headers={"Authorization": "Bearer TOKEN"}
        )
        assert response.status_code == 200
        assert isinstance(response.json, dict)
        assert mock_get.call_count == 1
        mock_get.assert_called_with(days=7, compact=True)

    def test_get_readings_recent_params(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_get: Mock = mocker.patch.object(
            controller,
            "retrieve_readings_for_period",
            return_value={patient_uuid: [{"uuid": generate_uuid()}]},
        )
        response = client.get(
            "/gdm/v1/reading/recent?days=30&compact=false",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert isinstance(response.json, dict)
        assert mock_get.call_count == 1
        mock_get.assert_called_with(days=30, compact=False)

    def test_get_readings_filter(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_readings_for_patient_with_tag",
            return_value=[{"uuid": generate_uuid()}],
        )
        prandial_tag = 5
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/reading/filter/{prandial_tag}",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(
            patient_id=patient_uuid, prandial_tag_value=prandial_tag
        )

    def test_get_reading_latest_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_latest_reading_for_patient",
            return_value={"uuid": generate_uuid()},
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/reading/latest",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert "uuid" in response.json
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(patient_id=patient_uuid)

    def test_get_patient_summary_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_patient_summaries",
            return_value={
                patient_uuid: {
                    "uuid": patient_uuid,
                    "latest_reading": {"uuid": generate_uuid()},
                }
            },
        )
        response = client.post(
            f"/gdm/v1/patient/summary",
            json=[patient_uuid],
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json.keys()) == 1
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(patient_ids=[patient_uuid])

    def test_get_patient_summary_empty(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_patient_summaries",
            return_value={
                patient_uuid: {
                    "uuid": patient_uuid,
                    "latest_reading": {"uuid": generate_uuid()},
                }
            },
        )
        response = client.post(
            f"/gdm/v1/patient/summary",
            json=[patient_uuid],
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json.keys()) == 1
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(patient_ids=[patient_uuid])

    @pytest.mark.parametrize(
        "update_details",
        [
            {"comment": "new comment"},
            {"prandial_tag": {"value": 6}},
            {"doses": [{"amount": 1.5, "medication_id": "12345"}]},
        ],
    )
    def test_patch_reading_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        patient_uuid: str,
        update_details: Dict,
    ) -> None:
        # Arrange
        reading_uuid: str = generate_uuid()
        mock_update: Mock = mocker.patch.object(
            controller, "update_reading", return_value={"uuid": reading_uuid}
        )
        # Act
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/reading/{reading_uuid}",
            json=update_details,
            headers={"Authorization": "Bearer TOKEN"},
        )
        # Assert
        assert mock_update.call_count == 1
        assert response.status_code == 200

        mock_update.assert_called_with(
            patient_id=patient_uuid,
            reading_id=reading_uuid,
            reading_data=update_details,
        )

    @pytest.mark.parametrize(
        "json_body", [None, {"comment": "new comment", "extra": "invalid key"}]
    )
    def test_reading_update_failure(
        self, client: FlaskClient, patient_uuid: str, json_body: Any
    ) -> None:
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/reading/reading-uuid",
            json=json_body,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "prandial_tag", [{"value": 99}, {"value": None}, {"value": "2"}]
    )
    def test_reading_update_invalid_prandial_tag(
        self, client: FlaskClient, patient_uuid: str, prandial_tag: Dict
    ) -> None:
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/reading/reading-uuid",
            json={"prandial_tag": prandial_tag},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_process_alerts_success(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        mocker.patch.object(controller, "process_percentages_alerts")
        response = client.post(
            "/gdm/v1/process_alerts",
            json={
                "patient_uuid_1": {"red_alert": True, "amber_alert": True},
                "patient_uuid_2": {"red_alert": True, "amber_alert": True},
            },
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 204

    @pytest.mark.parametrize(
        "json_body",
        [
            [],
            {},
            ["hello", 1],
            {"red_alert": True, "amber_alert": True},  # Missing patient UUID map
            {"some-patient-uuid": {"red_alert": True}},  # Missing amber alert
            {"some-patient-uuid": {"amber_alert": False}},  # Missing red alert
        ],
    )
    def test_process_alerts_failure(self, client: FlaskClient, json_body: Any) -> None:
        response = client.post(
            "/gdm/v1/process_alerts",
            json=json_body,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "body",
        [
            "one",
            [],
            {},
            {"key": "value"},
            {"patient_uuid": "hello"},
            {"patient_uuid": []},
            {"patient_uuid": {"key": "value"}},
            {"patient_uuid": {"red_alert": True}},
            {"patient_uuid": {"red_alert": "false", "amber_alert": "true"}},
            {"patient_uuid": {"red_alert": "false", "amber_alert": "true"}},
        ],
    )
    def test_process_alerts_unexpected_body(
        self, client: FlaskClient, body: Any
    ) -> None:
        response = client.post(
            "/gdm/v1/process_alerts",
            json=body,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_clear_alerts_success(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        expected = {"uuid": "patient_uuid_1"}
        mock_clear = mocker.patch.object(
            controller, "clear_alerts_for_patient", return_value=expected
        )
        response = client.post(
            "/gdm/v1/clear_alerts/patient/patient_uuid_1",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert mock_clear.called_with(patient_id="patient_uuid_1")
        assert response.status_code == 200
        assert response.json == expected

    def test_get_recent_readings(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        readings = {"some_patient_uuid": [{"uuid": "some_reading_uuid"}]}
        mock_retrieve: Mock = mocker.patch.object(
            controller, "retrieve_readings_for_period", return_value=readings
        )
        response = client.get(
            "/gdm/v1/reading/recent?compact=False",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json == readings
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(days=7, compact=False)

    def test_post_reading_dose_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_create: Mock = mocker.patch.object(
            controller, "add_dose_to_reading", return_value={"uuid": generate_uuid()}
        )
        reading_uuid: str = generate_uuid()
        dose_details = {
            "medication_id": "fb17c0e4-e468-4492-ab25-61ecbe0a1d31",
            "amount": 5.3,
        }
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/reading/{reading_uuid}/dose",
            json=dose_details,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_create.call_count == 1
        mock_create.assert_called_with(
            patient_id=patient_uuid, reading_id=reading_uuid, dose_data=dose_details
        )

    @pytest.mark.parametrize(
        "dose_details",
        [
            None,
            {"invalid": True, "i_dont_work": 123},
            {"medication_id": generate_uuid()},
            {"amount": 1.5},
            {"medication_id": generate_uuid(), "amount": 1.5, "extra": "key"},
        ],
    )
    def test_post_reading_dose_failure(
        self, client: FlaskClient, patient_uuid: str, dose_details: Any
    ) -> None:
        reading_uuid: str = generate_uuid()
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/reading/{reading_uuid}/dose",
            json=dose_details,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_post_reading_dose_unknown_reading(
        self,
        client: FlaskClient,
        patient_uuid: str,
    ) -> None:
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/reading/unknown-reading-uuid/dose",
            json={"medication_id": generate_uuid(), "amount": 1.5},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 404

    def test_patch_reading_dose_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_update: Mock = mocker.patch.object(
            controller, "update_dose_on_reading", return_value={"uuid": generate_uuid()}
        )
        reading_uuid: str = generate_uuid()
        dose_uuid: str = generate_uuid()
        dose_details = {
            "medication_id": generate_uuid(),
            "amount": 5.3,
        }
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/reading/{reading_uuid}/dose/{dose_uuid}",
            json=dose_details,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_update.call_count == 1
        mock_update.assert_called_with(
            patient_id=patient_uuid,
            reading_id=reading_uuid,
            dose_id=dose_uuid,
            dose_data=dose_details,
        )

    def test_get_patient_by_uuid(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_get: Mock = mocker.patch.object(
            controller, "get_patient", return_value={"uuid": patient_uuid}
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}", headers={"Authorization": "Bearer TOKEN"}
        )
        assert response.status_code == 200
        mock_get.assert_called_with(patient_uuid)

    def test_get_reading_earliest_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_first_reading_for_patient",
            return_value={"uuid": generate_uuid()},
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/reading/earliest",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert "uuid" in response.json
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(patient_id=patient_uuid)

    def test_process_counts_alerts_for_reading(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        reading_uuid: str = generate_uuid()
        mock_process: Mock = mocker.patch.object(
            controller,
            "process_counts_alerts_for_reading",
            return_value={"uuid": reading_uuid},
        )
        response = client.post(
            f"/gdm/v1/process_alerts/reading/{reading_uuid}",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert "uuid" in response.json
        assert mock_process.call_count == 1
        mock_process.assert_called_with(reading_id=reading_uuid)

    def test_process_activity_alerts(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        patient_uuid: str,
        sample_readings_plans: List[Dict],
    ) -> None:
        mock_process: Mock = mocker.patch.object(
            controller,
            "process_activity_alerts_for_patient",
            return_value={"uuid": patient_uuid, "alert_now": True},
        )
        response = client.post(
            f"/gdm/v1/process_activity_alerts/patient/{patient_uuid}",
            json={"readings_plans": sample_readings_plans},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert "alert_now" in response.json
        mock_process.assert_called_with(
            patient_id=patient_uuid, readings_plans=sample_readings_plans
        )

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/gdm/v1/patient/patient-uuid/reading",
            "/gdm/v1/patient/summary",
            "/gdm/v1/process_activity_alerts/patient/patient-uuid",
            "/gdm/v1/process_alerts",
        ],
    )
    def test_post_endpoints_mandatory_request_body(
        self, client: FlaskClient, endpoint: str
    ) -> None:
        response = client.post(endpoint, headers={"Authorization": "Bearer TOKEN"})
        assert response.status_code == 400

    def test_missing_auth(self, client: FlaskClient) -> None:
        response = client.post("/gdm/v1/process_alerts")
        assert response.status_code == 401

    def test_post_hba1c_reading_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        hba1c_reading_dict_in: Dict,
        patient_uuid: str,
    ) -> None:
        mock_create: Mock = mocker.patch.object(
            controller,
            "create_hba1c_reading",
            return_value={"uuid": "reading-1", "patient_id": patient_uuid},
        )
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/hba1c",
            json=hba1c_reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 201
        assert mock_create.call_count == 1
        mock_create.assert_called_with(
            patient_uuid=patient_uuid, reading_data=hba1c_reading_dict_in
        )
        assert response.headers["Location"].endswith("hba1c/reading-1")

    @pytest.mark.parametrize(
        "missing_field",
        ["measured_timestamp", "units", "value"],
    )
    def test_post_hba1c_reading_missing_fields_400(
        self,
        client: FlaskClient,
        hba1c_reading_dict_in: Dict,
        patient_uuid: str,
        missing_field: str,
    ) -> None:
        del hba1c_reading_dict_in[missing_field]
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/hba1c",
            json=hba1c_reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_get_hba1c_readings_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_hba1c_readings_for_patient",
            return_value=[{"uuid": generate_uuid()}],
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/hba1c",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(patient_uuid=patient_uuid)

    def test_get_hba1c_reading_by_uuid_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        patient_uuid: str,
        hba1c_reading_uuid: str,
    ) -> None:
        mock_get: Mock = mocker.patch.object(
            controller,
            "get_hba1c_reading_by_uuid",
            return_value={"uuid": hba1c_reading_uuid},
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/hba1c/{hba1c_reading_uuid}",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert mock_get.call_count == 1
        mock_get.assert_called_with(
            patient_uuid=patient_uuid, hba1c_reading_uuid=hba1c_reading_uuid
        )

    def test_patch_hba1c_reading_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        patient_uuid: str,
        hba1c_reading_uuid: str,
    ) -> None:
        mock_update: Mock = mocker.patch.object(
            controller,
            "update_hba1c_reading",
            return_value={"uuid": hba1c_reading_uuid, "patient_id": patient_uuid},
        )
        hba1c_reading_update: Dict = {
            "value": 40,
            "measured_timestamp": "2020-07-15T14:15:30.123Z",
        }
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/hba1c/{hba1c_reading_uuid}",
            json=hba1c_reading_update,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 204
        assert mock_update.call_count == 1
        mock_update.assert_called_with(
            patient_uuid=patient_uuid,
            hba1c_reading_uuid=hba1c_reading_uuid,
            reading_data=hba1c_reading_update,
        )

    def test_patch_hba1c_reading_empty_body(
        self,
        client: FlaskClient,
        patient_uuid: str,
        hba1c_reading_uuid: str,
    ) -> None:
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/hba1c/{hba1c_reading_uuid}",
            json={},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_delete_hba1c_reading_by_uuid_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        patient_uuid: str,
        hba1c_reading_uuid: str,
    ) -> None:
        mock_delete: Mock = mocker.patch.object(
            controller,
            "delete_hba1c_reading",
            return_value={"uuid": hba1c_reading_uuid, "patient_id": patient_uuid},
        )
        response = client.delete(
            f"/gdm/v1/patient/{patient_uuid}/hba1c/{hba1c_reading_uuid}",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 204
        assert mock_delete.call_count == 1
        mock_delete.assert_called_with(
            patient_uuid=patient_uuid, hba1c_reading_uuid=hba1c_reading_uuid
        )

    def test_delete_hba1c_reading_unknown_uuids_404(
        self,
        client: FlaskClient,
        patient_uuid: str,
        hba1c_reading_uuid: str,
    ) -> None:
        response = client.delete(
            f"/gdm/v1/patient/{patient_uuid}/hba1c/{hba1c_reading_uuid}",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 404

    def test_post_hba1c_target_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        hba1c_target_dict_in: Dict,
        patient_uuid: str,
    ) -> None:
        mock_create: Mock = mocker.patch.object(
            controller,
            "create_hba1c_target",
            return_value={"uuid": "target-1", "patient_id": patient_uuid},
        )
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/hba1c_target",
            json=hba1c_target_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 201
        assert mock_create.call_count == 1
        mock_create.assert_called_with(
            patient_uuid=patient_uuid, target_data=hba1c_target_dict_in
        )
        assert response.headers["Location"].endswith("hba1c_target/target-1")

    @pytest.mark.parametrize(
        "missing_field",
        ["units", "value"],
    )
    def test_post_hba1c_target_missing_fields_400(
        self,
        client: FlaskClient,
        hba1c_reading_dict_in: Dict,
        patient_uuid: str,
        missing_field: str,
    ) -> None:
        del hba1c_reading_dict_in[missing_field]
        response = client.post(
            f"/gdm/v1/patient/{patient_uuid}/hba1c_target",
            json=hba1c_reading_dict_in,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    def test_get_hba1c_targets_success(
        self, client: FlaskClient, mocker: MockFixture, patient_uuid: str
    ) -> None:
        mock_retrieve: Mock = mocker.patch.object(
            controller,
            "retrieve_hba1c_targets_for_patient",
            return_value=[{"uuid": generate_uuid()}],
        )
        response = client.get(
            f"/gdm/v1/patient/{patient_uuid}/hba1c_target",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        assert response.json
        assert len(response.json) == 1
        assert mock_retrieve.call_count == 1
        mock_retrieve.assert_called_with(patient_uuid=patient_uuid)

    def test_patch_hba1c_target_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        patient_uuid: str,
        hba1c_target_uuid: str,
    ) -> None:
        mock_update: Mock = mocker.patch.object(
            controller,
            "update_hba1c_target",
            return_value={"uuid": hba1c_target_uuid, "patient_id": patient_uuid},
        )
        hba1c_target_update: Dict = {"value": 40}
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/hba1c_target/{hba1c_target_uuid}",
            json=hba1c_target_update,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 204
        assert mock_update.call_count == 1
        mock_update.assert_called_with(
            patient_uuid=patient_uuid,
            hba1c_target_uuid=hba1c_target_uuid,
            target_data=hba1c_target_update,
        )

    def test_patch_hba1c_target_empty_body(
        self,
        client: FlaskClient,
        patient_uuid: str,
        hba1c_reading_uuid: str,
    ) -> None:
        response = client.patch(
            f"/gdm/v1/patient/{patient_uuid}/hba1c_target/{hba1c_reading_uuid}",
            json={},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400
