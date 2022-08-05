from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Generator, Iterable, List, Optional, Tuple

import pytest
from _pytest.logging import LogCaptureFixture
from flask_batteries_included.helpers.error_handler import EntityNotFoundException
from flask_batteries_included.helpers.timestamp import parse_iso8601_to_datetime
from flask_batteries_included.sqldb import db, generate_uuid
from mock import Mock
from pytest_mock import MockFixture

from gdm_bg_readings_api import trustomer
from gdm_bg_readings_api.blueprint_api import (
    controller,
    counts_alerting,
    percentages_alerting,
)
from gdm_bg_readings_api.models.api_spec import (
    Hba1cReadingResponse,
    Hba1cTargetResponse,
    ReadingResponse,
    ReadingResponseCompact,
    ReadingStatistics,
)
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.patient_alert import PatientAlert
from gdm_bg_readings_api.models.reading import Reading
from gdm_bg_readings_api.trustomer import AlertsSystem


@pytest.mark.usefixtures("app")
class TestController:
    @pytest.fixture
    def reading_count(self) -> int:
        return 1

    @pytest.fixture
    def patient_with_readings(
        self, reading_count: int, patient_uuid: str
    ) -> Generator[Patient, None, None]:
        patient = Patient(uuid=patient_uuid, current_activity_alert=False)
        readings = [
            Reading(
                uuid=f"reading_uuid_{i+1}",
                measured_timestamp=datetime.now() - timedelta(days=1, hours=i),
                measured_timezone=0,
                blood_glucose_value=5.5,
                units="mmol/L",
                patient_id=patient_uuid,
            )
            for i in range(reading_count)
        ]
        db.session.add_all(readings)
        db.session.add(patient)
        db.session.commit()

        yield patient

        db.session.delete(patient)
        for r in readings:
            db.session.delete(r)
        db.session.commit()

    @pytest.fixture
    def single_sample_patient(
        self, patient_uuid: str
    ) -> Generator[Patient, None, None]:
        patient = Patient(uuid=patient_uuid, current_activity_alert=False)
        db.session.add(patient)
        db.session.commit()

        yield patient

        db.session.delete(patient)
        db.session.commit()

    @pytest.fixture
    def four_sample_patients(
        self, patient_uuid: str
    ) -> Generator[List[Patient], None, None]:
        patients = [
            Patient(uuid=f"{patient_uuid}_{i+1}", current_activity_alert=False)
            for i in range(4)
        ]
        db.session.add_all(patients)
        db.session.commit()

        yield patients

        for p in patients:
            db.session.delete(p)
        db.session.commit()

    @pytest.fixture
    def preexisting_activity_alerts(
        self, patient_uuid: str
    ) -> Generator[Tuple, None, None]:
        existing_ended_alert = PatientAlert(
            uuid=generate_uuid(),
            started_at=datetime.now(),
            ended_at=datetime.now(),
            alert_type=PatientAlert.AlertType.ACTIVITY_GREY,
            patient_id=patient_uuid,
        )
        existing_current_alert = PatientAlert(
            uuid=generate_uuid(),
            started_at=datetime.now(),
            alert_type=PatientAlert.AlertType.ACTIVITY_GREY,
            patient_id=patient_uuid,
        )
        db.session.add(existing_ended_alert)
        db.session.add(existing_current_alert)
        db.session.commit()

        yield (existing_ended_alert, existing_current_alert)

        db.session.delete(existing_ended_alert)
        db.session.delete(existing_current_alert)
        db.session.commit()

    def test_create_reading_success(
        self, patient_uuid: str, reading_dict_in: Dict, assert_valid_schema: Callable
    ) -> None:
        result = controller.create_reading(patient_uuid, reading_dict_in)
        assert_valid_schema(ReadingResponse, result)
        readings: List[Dict] = list(
            controller.retrieve_readings_for_patient_with_tag(patient_uuid)
        )
        assert len(readings) == 1
        assert "uuid" in result
        assert readings[0]["uuid"] == result["uuid"]

    def test_create_reading_success_compact(
        self, patient_uuid: str, reading_dict_in: Dict, assert_valid_schema: Callable
    ) -> None:
        result = controller.create_reading(
            patient_id=patient_uuid, reading_data=reading_dict_in, compact=True
        )
        assert_valid_schema(ReadingResponseCompact, result)
        readings: List[Dict] = list(
            controller.retrieve_readings_for_patient_with_tag(patient_uuid)
        )
        assert len(readings) == 1
        assert "uuid" in result
        assert readings[0]["uuid"] == result["uuid"]
        assert "doses" not in result
        assert isinstance(result["prandial_tag"], str)
        assert isinstance(result["reading_metadata"], dict)
        assert isinstance(result["reading_banding"], str)

    @pytest.mark.parametrize(
        ["banding_id", "banding_value"],
        [
            ("BG-READING-BANDING-LOW", 1),
            ("BG-READING-BANDING-NORMAL", 2),
            ("BG-READING-BANDING-HIGH", 3),
        ],
    )
    def test_create_reading_with_banding(
        self, banding_id: str, banding_value: int
    ) -> None:
        reading_data = {
            "blood_glucose_value": 5.5,
            "units": "mmol/L",
            "measured_timestamp": "2000-01-01T01:01:01.000Z",
            "prandial_tag": {"value": 2},
            "banding_id": banding_id,
        }
        reading = controller.create_reading(patient_id="123", reading_data=reading_data)
        assert reading["reading_banding"]["uuid"] == banding_id
        assert reading["reading_banding"]["value"] == banding_value

    def test_create_reading_counts_alerts(
        self, mock_trustomer: Mock, patient_uuid: str
    ) -> None:
        blood_glucose_values = [1, 5, 5, 5, 8, 5, 5, 8, 8, 1]
        banding_ids = [
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-LOW",
        ]
        expected_amber_alert = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]
        expected_retrospective_red_alert = [0, 0, 0, 0, 0, 0, 0, 1, 1, 1]
        for i, blood_glucose_value in enumerate(blood_glucose_values):
            result = controller.create_reading(
                patient_uuid,
                {
                    "prandial_tag": {"value": 2},
                    "blood_glucose_value": blood_glucose_value,
                    "units": "mmol/L",
                    "banding_id": banding_ids[i],
                    "measured_timestamp": "2000-01-"
                    + str(i + 1).zfill(2)
                    + "T01:01:02.000+01:00",
                },
            )
            process_result: Dict = controller.process_counts_alerts_for_reading(
                reading_id=result["uuid"]
            )
            assert ("amber_alert" in process_result) == expected_amber_alert[i]

        for i, reading in enumerate(
            sorted(
                controller.retrieve_readings_for_patient_with_tag(
                    patient_id=patient_uuid
                ),
                key=lambda x: x["measured_timestamp"],
            )
        ):
            assert ("red_alert" in reading) == expected_retrospective_red_alert[i]

    def test_create_reading_red_alerts(
        self, mock_trustomer: Mock, patient_uuid: str
    ) -> None:
        blood_glucose_values = [1, 1, 1, 5, 8, 8, 8, 5, 8, 9, 5, 8, 1, 9]
        banding_ids = [
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-NORMAL",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-HIGH",
        ]
        expected_immediate_red_alert = [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1]
        expected_retrospective_red_alert = [1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1]
        for i, blood_glucose_value in enumerate(blood_glucose_values):
            result = controller.create_reading(
                patient_uuid,
                {
                    "prandial_tag": {"value": 2},
                    "blood_glucose_value": blood_glucose_value,
                    "units": "mmol/L",
                    "banding_id": banding_ids[i],
                    "measured_timestamp": "2000-01-"
                    + str(i + 1).zfill(2)
                    + "T01:01:02.000+01:00",
                },
            )
            process_result: Dict = controller.process_counts_alerts_for_reading(
                reading_id=result["uuid"]
            )
            assert ("red_alert" in process_result) == expected_immediate_red_alert[i]

        for i, reading in enumerate(
            sorted(
                controller.retrieve_readings_for_patient_with_tag(
                    patient_id=patient_uuid
                ),
                key=lambda x: x["measured_timestamp"],
            )
        ):
            assert ("red_alert" in reading) == expected_retrospective_red_alert[i]

    def test_get_reading_by_uuid(
        self, patient_uuid: str, reading_dict_in: Dict, assert_valid_schema: Callable
    ) -> None:
        existing_reading = controller.create_reading(patient_uuid, reading_dict_in)
        reading: Dict = controller.get_reading_by_uuid(
            patient_uuid=patient_uuid, reading_uuid=existing_reading["uuid"]
        )
        assert reading["uuid"] == existing_reading["uuid"]
        assert_valid_schema(ReadingResponse, reading)

    def test_retrieve_readings_for_patient_with_tag_success(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        existing_reading = controller.create_reading(patient_uuid, reading_dict_in)
        readings: Iterable[Dict] = controller.retrieve_readings_for_patient_with_tag(
            patient_uuid
        )
        assert len(list(readings)) == 1
        assert list(readings)[0]["uuid"] == existing_reading["uuid"]

    def test_retrieve_readings_for_patient_with_tag_filtered(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        for i in range(10):
            measured_timestamp = f"2000-{str(i + 1).zfill(2)}-01T01:01:01.000Z"
            controller.create_reading(
                patient_uuid,
                {
                    **reading_dict_in,
                    "prandial_tag": {"value": 2},
                    "measured_timestamp": measured_timestamp,
                },
            )
        for i in range(3):
            measured_timestamp = f"2000-{str(i + 1).zfill(2)}-01T02:02:02.000Z"
            controller.create_reading(
                patient_uuid,
                {
                    **reading_dict_in,
                    "prandial_tag": {"value": 3},
                    "measured_timestamp": measured_timestamp,
                },
            )
        result = list(
            controller.retrieve_readings_for_patient_with_tag(patient_uuid, "3")
        )
        assert len(result) == 3

    def test_retrieve_readings_ordered_by_measured_timestamp(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        for i in range(5):
            reading_data = {
                **reading_dict_in,
                "measured_timestamp": "2000-0%s-01T01:01:01.000Z" % str(i + 1),
            }
            controller.create_reading(patient_uuid, reading_data)
        readings = list(controller.retrieve_readings_for_patient_with_tag(patient_uuid))
        assert len(readings) == 5
        for i in range(1, len(readings)):
            last = readings[i - 1]["measured_timestamp"]
            this = readings[i]["measured_timestamp"]
            assert last > this

    def test_retrieve_readings_for_period(self, patient_with_readings: Patient) -> None:
        result = controller.retrieve_readings_for_period(days=7, compact=False)
        assert result[patient_with_readings.uuid][0]["blood_glucose_value"] == 5.5
        assert result[patient_with_readings.uuid][0]["doses"] == []
        assert result[patient_with_readings.uuid][0]["reading_banding"] == {}

    def test_retrieve_readings_for_period_days(self, reading_dict_in: Dict) -> None:
        patient_1 = generate_uuid()
        patient_2 = generate_uuid()
        base_time = datetime.now(tz=timezone.utc)
        for i in range(20):
            measured_time = (base_time - timedelta(hours=6 * i)).isoformat(
                timespec="milliseconds"
            )
            controller.create_reading(
                patient_id=patient_1,
                reading_data={**reading_dict_in, "measured_timestamp": measured_time},
            )
            controller.create_reading(
                patient_id=patient_2,
                reading_data={**reading_dict_in, "measured_timestamp": measured_time},
            )

        # Correct patient count for 10 days
        results = controller.retrieve_readings_for_period(days=10, compact=True)
        assert len(results) == 2
        assert patient_1 in results
        assert patient_2 in results

        # 1 day
        results = controller.retrieve_readings_for_period(days=1, compact=True)
        assert len(results[patient_1]) == 4

        # 4 day
        results = controller.retrieve_readings_for_period(days=4, compact=True)
        assert len(results[patient_1]) == 16

        # all the days
        results = controller.retrieve_readings_for_period(days=9999, compact=True)
        assert len(results[patient_1]) == 20

    @pytest.mark.freeze_time("2020-08-21T00:00:00.000+00:00")
    def test_retrieve_readings_for_period_timezone_aware(
        self, reading_dict_in: Dict
    ) -> None:
        """
        Tests that the `retrieve_readings_for_period` function correctly takes timezone into
        account when searching for readings.
        """
        patient_uuid: str = generate_uuid()
        expected_timestamps: List[str] = [
            "2020-08-20T12:00:00.000+00:00",
            "2020-08-20T00:00:00.001+00:00",
            "2020-08-19T23:30:00.000-01:00",
            "2020-08-19T20:00:00.000-05:00",
        ]
        unexpected_timestamps: List[str] = [
            "2020-08-19T23:00:00.000+00:00",
            "2020-08-20T00:00:00.001+01:00",
            "2020-08-20T04:00:00.001+05:00",
        ]
        for ts in expected_timestamps + unexpected_timestamps:
            controller.create_reading(
                patient_id=patient_uuid,
                reading_data={**reading_dict_in, "measured_timestamp": ts},
            )

        results = controller.retrieve_readings_for_period(days=1, compact=True)
        assert len(results) == 1  # 1 patient
        assert len(results[patient_uuid]) == 4  # 4 readings
        actual_timestamps = {
            r["measured_timestamp"].isoformat(timespec="milliseconds")
            for r in results[patient_uuid]
        }
        assert actual_timestamps == set(expected_timestamps)

    @pytest.mark.freeze_time("2020-08-21T00:00:00.000+00:00")
    def test_retrieve_statistics_for_period(
        self, reading_dict_in: Dict, assert_valid_schema: Callable
    ) -> None:
        patient_1 = generate_uuid()
        patient_2 = generate_uuid()
        patient_3 = generate_uuid()
        patient_4 = generate_uuid()
        data = [
            (patient_1, "2020-08-18T00:00:00.000+00:00", 5.0, "NORMAL"),
            (patient_1, "2020-08-17T00:00:00.000+00:00", 8.0, "HIGH"),
            (patient_1, "2020-08-09T00:00:00.000+00:00", 3.0, "LOW"),
            (patient_1, "2020-08-08T00:00:00.000+00:00", 11.0, "HIGH"),
            (patient_2, "2020-08-18T00:00:00.000+00:00", 1.0, "LOW"),
            (patient_2, "2020-08-17T00:00:00.000+00:00", 9.0, "HIGH"),
            (patient_2, "2020-08-09T00:00:00.000+00:00", 4.0, "NORMAL"),
            (patient_2, "2020-08-08T00:00:00.000+00:00", 5.0, "NORMAL"),
            (patient_3, "2020-08-18T00:00:00.000+00:00", 6.5, "NORMAL"),
            (patient_4, "1990-01-01T00:00:00.000+00:00", 10.0, "HIGH"),
        ]
        for patient_id, ts, val, banding in data:
            controller.create_reading(
                patient_id=patient_id,
                reading_data={
                    **reading_dict_in,
                    "measured_timestamp": ts,
                    "blood_glucose_value": val,
                    "banding_id": f"BG-READING-BANDING-{banding}",
                },
            )
        results = controller.retrieve_statistics_for_period(days=7, compact=False)
        assert_valid_schema(ReadingStatistics, list(results.values()), many=True)
        assert results[patient_1]["min_reading"]["blood_glucose_value"] == 5.0
        assert results[patient_1]["max_reading"]["blood_glucose_value"] == 8.0
        assert results[patient_1]["readings_count"] == 2
        assert results[patient_1]["readings_count_banding_normal"] == 1
        assert results[patient_2]["min_reading"]["blood_glucose_value"] == 1.0
        assert results[patient_2]["max_reading"]["blood_glucose_value"] == 9.0
        assert results[patient_2]["readings_count"] == 2
        assert results[patient_2]["readings_count_banding_normal"] == 0
        assert results[patient_3]["min_reading"]["blood_glucose_value"] == 6.5
        assert results[patient_3]["max_reading"]["blood_glucose_value"] == 6.5
        assert results[patient_3]["readings_count"] == 1
        assert results[patient_3]["readings_count_banding_normal"] == 1
        assert patient_4 not in results

    def test_retrieve_latest_reading(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        base_time = datetime.now(tz=timezone.utc)
        reading_uuids: List[str] = []
        for i in range(5):
            measured_time = (base_time - timedelta(hours=6 * i)).isoformat(
                timespec="milliseconds"
            )
            reading = controller.create_reading(
                patient_id=patient_uuid,
                reading_data={**reading_dict_in, "measured_timestamp": measured_time},
            )
            reading_uuids.append(reading["uuid"])

        result = controller.retrieve_latest_reading_for_patient(patient_uuid)
        assert result is not None
        assert result["uuid"] == reading_uuids[0]

    def test_retrieve_patient_summaries(self, mocker: MockFixture) -> None:
        mocker.patch(
            "gdm_bg_readings_api.blueprint_api.controller._query_patient_summaries_from_db",
            autospec=True,
            return_value={
                str(patient_id): {"some_key": "some_value"}
                for patient_id in range(1, 3)
            },
        )
        summary = controller.retrieve_patient_summaries(["0", "1", "2"])
        assert "0" in summary
        assert summary["0"] == {}

    def test_retrieve_patient_summaries_empty(self) -> None:
        assert controller.retrieve_patient_summaries([]) == {}

    @pytest.mark.parametrize(
        "update_details,is_published",
        [
            ({"comment": "new comment"}, False),
            (
                {"prandial_tag": {"value": 1}, "banding_id": "BG-READING-BANDING-HIGH"},
                True,
            ),
            ({"doses": [{"amount": 1.5, "medication_id": "12345"}]}, False),
        ],
    )
    def test_update_reading_success(
        self,
        patient_uuid: str,
        reading_dict_in: Dict,
        update_details: Dict,
        is_published: bool,
        mock_publish_abnormal: Mock,
    ) -> None:
        # Arrange
        original_reading: Dict = controller.create_reading(
            patient_uuid, reading_dict_in
        )
        # Act
        updated_reading: Dict = controller.update_reading(
            patient_uuid, original_reading["uuid"], update_details
        )
        # Assert
        if is_published:
            mock_publish_abnormal.assert_called_once()
        else:
            mock_publish_abnormal.assert_not_called()
        assert updated_reading["uuid"] == original_reading["uuid"]
        for key in update_details.keys():
            if key == "prandial_tag":
                assert updated_reading[key]["value"] == update_details[key]["value"]
            elif key == "banding_id":
                assert updated_reading["reading_banding"]["uuid"] == update_details[key]
            elif key == "doses":
                assert (
                    updated_reading[key][0]["medication_id"]
                    == update_details[key][0]["medication_id"]
                )
            else:
                assert updated_reading[key] == update_details[key]

    def test_update_reading_doses(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        del reading_dict_in["doses"]
        original_reading: Dict = controller.create_reading(
            patient_uuid, reading_dict_in
        )
        assert len(original_reading["doses"]) == 0
        first_update = controller.update_reading(
            patient_uuid,
            original_reading["uuid"],
            {"doses": [{"amount": 1.5, "medication_id": "first"}]},
        )
        assert len(first_update["doses"]) == 1
        assert first_update["doses"][0]["medication_id"] == "first"
        assert first_update["doses"][0]["amount"] == 1.5
        first_dose_uuid = first_update["doses"][0]["uuid"]
        second_update = controller.update_reading(
            patient_uuid,
            original_reading["uuid"],
            {
                "doses": [
                    {"uuid": first_dose_uuid, "amount": 2.5, "medication_id": "first"},
                    {"amount": 3.5, "medication_id": "second"},
                ]
            },
        )
        assert len(second_update["doses"]) == 2
        assert second_update["doses"][0]["medication_id"] == "first"
        assert second_update["doses"][0]["amount"] == 2.5
        assert second_update["doses"][1]["medication_id"] == "second"
        assert second_update["doses"][1]["amount"] == 3.5

    def test_update_reading_counts_alerts(
        self, mock_trustomer: Mock, patient_uuid: str
    ) -> None:
        blood_glucose_values = [1, 1, 1, 8, 6]
        banding_ids = [
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-LOW",
            "BG-READING-BANDING-HIGH",
            "BG-READING-BANDING-HIGH",
        ]
        expected_immediate_red_alert = [0, 0, 1, 1, 1]
        expected_retrospective_red_alert = [1, 1, 1, 1, 0]
        last_reading_uuid: str = ""
        for i, blood_glucose_value in enumerate(blood_glucose_values):
            result = controller.create_reading(
                patient_uuid,
                {
                    "prandial_tag": {"value": 1},
                    "blood_glucose_value": blood_glucose_value,
                    "units": "mmol/L",
                    "banding_id": banding_ids[i],
                    "measured_timestamp": "2000-01-01T01:01:"
                    + str(i).zfill(2)
                    + ".000+01:00",
                },
            )
            process_result: Dict = controller.process_counts_alerts_for_reading(
                reading_id=result["uuid"]
            )
            assert ("red_alert" in process_result) == expected_immediate_red_alert[i]
            last_reading_uuid = result["uuid"]

        # Update the last reading so it's no longer high
        controller.update_reading(
            patient_uuid,
            last_reading_uuid,
            {"prandial_tag": {"value": 2}, "banding_id": "BG-READING-BANDING-NORMAL"},
        )
        updated_process_result: Dict = controller.process_counts_alerts_for_reading(
            reading_id=last_reading_uuid
        )
        assert "red_alert" not in updated_process_result

        # Select all the readings
        for i, reading in enumerate(
            sorted(
                controller.retrieve_readings_for_patient_with_tag(
                    patient_id=patient_uuid
                ),
                key=lambda x: x["measured_timestamp"],
            )
        ):
            assert ("red_alert" in reading) == expected_retrospective_red_alert[i]

    @pytest.mark.parametrize(
        ["reading_count", "should_have_alert"],
        [(0, True), (1, True), (13, True), (14, False), (25, False)],
    )
    def test_process_activity_alerts_for_patient(
        self,
        sample_readings_plans: List[Dict],
        reading_count: int,
        should_have_alert: bool,
        patient_with_readings: Patient,
    ) -> None:
        """
        The readings plan fixture expects 20 readings per week, so we need at least 14 readings in order not to trigger
        an activity alert.
        """
        patient_data: Dict = controller.process_activity_alerts_for_patient(
            patient_id=patient_with_readings.uuid,
            readings_plans=sample_readings_plans,
        )
        alerts = PatientAlert.query.filter_by(
            patient_id=patient_with_readings.uuid
        ).all()
        assert patient_data["current_activity_alert"] is should_have_alert
        if should_have_alert:
            assert len(alerts) == 1
            assert alerts[0].alert_type == PatientAlert.AlertType.ACTIVITY_GREY
            assert alerts[0].ended_at is None
        else:
            assert len(alerts) == 0

    @pytest.mark.parametrize(
        ["reading_count", "should_have_alert"],
        [(0, True), (1, True), (13, True), (14, False), (25, False)],
    )
    def test_process_activity_alerts_for_patient_preexisting_alert(
        self,
        sample_readings_plans: List[Dict],
        reading_count: int,
        should_have_alert: bool,
        patient_with_readings: Patient,
        preexisting_activity_alerts: Tuple,
    ) -> None:
        """
        This time we're checking that pre-existing alerts are dealt with as expected.
        """
        patient_data: Dict = controller.process_activity_alerts_for_patient(
            patient_id=patient_with_readings.uuid,
            readings_plans=sample_readings_plans,
        )
        all_alerts: List[PatientAlert] = PatientAlert.query.filter_by(
            patient_id=patient_with_readings.uuid,
            alert_type=PatientAlert.AlertType.ACTIVITY_GREY,
        ).all()
        active_alerts: List[PatientAlert] = [
            a for a in all_alerts if a.ended_at is None
        ]
        assert patient_data["current_activity_alert"] is should_have_alert
        assert len(all_alerts) == 2
        if should_have_alert:
            assert len(active_alerts) == 1
            assert active_alerts[0].uuid == preexisting_activity_alerts[1].uuid
        else:
            assert len(active_alerts) == 0
            assert preexisting_activity_alerts[1].ended_at is not None

    def test_process_percentages_alerts_unknown_patient(self) -> None:
        alerts_data = {"patient_uuid_1": {"red_alert": True, "amber_alert": True}}
        with pytest.raises(EntityNotFoundException):
            controller.process_percentages_alerts(alerts_data)

    def test_process_percentages_alerts_single_patient_success(
        self, single_sample_patient: Patient, mocker: MockFixture
    ) -> None:
        alerts_data = {
            single_sample_patient.uuid: {"red_alert": True, "amber_alert": False}
        }
        mock_db_commit = mocker.patch.object(db.session, "commit")
        mock_update_alerts = mocker.patch.object(
            percentages_alerting, "update_alerts_for_patient"
        )
        controller.process_percentages_alerts(alerts_data)
        assert single_sample_patient.current_red_alert is True
        assert single_sample_patient.current_amber_alert is False
        calls = mock_update_alerts.call_args_list
        assert len(calls) == 2
        assert calls[0][1] == {
            "patient": single_sample_patient,
            "alert_type": PatientAlert.AlertType.PERCENTAGES_RED,
            "alert_now": True,
        }
        assert calls[1][1] == {
            "patient": single_sample_patient,
            "alert_type": PatientAlert.AlertType.PERCENTAGES_AMBER,
            "alert_now": False,
        }
        assert mock_db_commit.call_count == 1

    def test_process_percentages_alerts_multiple_patients_success(
        self, four_sample_patients: List[Patient], mocker: MockFixture
    ) -> None:
        patient_1 = four_sample_patients[0]
        patient_2 = four_sample_patients[1]
        patient_3 = four_sample_patients[2]
        patient_4 = four_sample_patients[3]
        alerts_data = {
            patient_1.uuid: {"red_alert": True, "amber_alert": True},
            patient_2.uuid: {"red_alert": False, "amber_alert": False},
            patient_3.uuid: {"red_alert": True, "amber_alert": False},
            patient_4.uuid: {"red_alert": False, "amber_alert": True},
        }
        mock_update_alerts = mocker.patch.object(
            percentages_alerting, "update_alerts_for_patient"
        )
        controller.process_percentages_alerts(alerts_data)
        assert patient_1.current_red_alert is True
        assert patient_1.current_amber_alert is True
        assert patient_2.current_red_alert is False
        assert patient_2.current_amber_alert is False
        assert patient_3.current_red_alert is True
        assert patient_3.current_amber_alert is False
        assert patient_4.current_red_alert is False
        assert patient_4.current_amber_alert is True
        assert mock_update_alerts.call_count == 8

    def test_process_percentages_alerts_multiple_patients_snoozed_success(
        self, four_sample_patients: List[Patient], mocker: MockFixture
    ) -> None:
        patient_1 = four_sample_patients[0]
        patient_2 = four_sample_patients[1]
        patient_3 = four_sample_patients[2]
        patient_4 = four_sample_patients[3]
        alerts_data = {
            patient_1.uuid: {"red_alert": True, "amber_alert": True},
            patient_2.uuid: {"red_alert": False, "amber_alert": False},
            patient_3.uuid: {"red_alert": True, "amber_alert": False},
            patient_4.uuid: {"red_alert": False, "amber_alert": True},
        }
        mock_is_snoozed = mocker.patch.object(
            percentages_alerting, "is_patient_in_snooze_period", return_value=True
        )
        mock_update_alerts = mocker.patch.object(
            percentages_alerting, "update_alerts_for_patient"
        )
        controller.process_percentages_alerts(alerts_data)
        assert patient_1.current_red_alert is False
        assert patient_1.current_amber_alert is False
        assert patient_2.current_red_alert is False
        assert patient_2.current_amber_alert is False
        assert patient_3.current_red_alert is False
        assert patient_3.current_amber_alert is False
        assert patient_4.current_red_alert is False
        assert patient_4.current_amber_alert is False
        assert mock_is_snoozed.call_count == 4
        assert mock_update_alerts.call_count == 8

    @pytest.mark.freeze_time("2019-01-01 12:00:00")
    def test_clear_alerts_for_patient_percentages(
        self, mocker: MockFixture, patient_with_readings: Patient
    ) -> None:
        expected_from = datetime(2019, 1, 1, 12, 0, 0, 0)
        expected_until = datetime(2019, 1, 4, 0, 0, 0, 0)
        patient_with_readings.current_amber_alert = True
        patient_with_readings.current_red_alert = True
        mocker.patch.object(
            trustomer, "get_alerts_snooze_duration_days", return_value=3
        )
        mock_dismiss_percentages = mocker.patch.object(
            percentages_alerting, "dismiss_active_alerts_for_patient"
        )
        mock_dismiss_counts = mocker.patch.object(
            counts_alerting, "dismiss_active_alerts_for_patient"
        )
        result: Dict = controller.clear_alerts_for_patient(patient_with_readings.uuid)
        assert result == {
            "completed": True,
            "suppress_reading_alerts_from": expected_from,
            "suppress_reading_alerts_until": expected_until,
        }
        assert mock_dismiss_percentages.called_with(
            patient_id=patient_with_readings.uuid
        )
        assert mock_dismiss_counts.called_with(patient_id=patient_with_readings.uuid)
        assert patient_with_readings.current_amber_alert is False
        assert patient_with_readings.current_amber_alert is False
        assert patient_with_readings.suppress_reading_alerts_from == expected_from
        assert patient_with_readings.suppress_reading_alerts_until == expected_until

    @pytest.mark.freeze_time("2019-01-01 12:00:00")
    def test_clear_alerts_for_patient_counts(
        self, mocker: MockFixture, patient_with_readings: Patient
    ) -> None:
        expected_from = datetime(2019, 1, 1, 12, 0, 0, 0)
        expected_until = datetime(2019, 1, 4, 0, 0, 0, 0)
        patient_with_readings.current_amber_alert = True
        patient_with_readings.current_red_alert = True
        mocker.patch.object(
            trustomer, "get_alerts_snooze_duration_days", return_value=3
        )
        mock_dismiss = mocker.patch.object(
            percentages_alerting, "dismiss_active_alerts_for_patient"
        )
        result: Dict = controller.clear_alerts_for_patient(patient_with_readings.uuid)
        assert result == {
            "completed": True,
            "suppress_reading_alerts_from": expected_from,
            "suppress_reading_alerts_until": expected_until,
        }
        assert mock_dismiss.called_with(patient_id=patient_with_readings.uuid)
        assert patient_with_readings.current_amber_alert is False
        assert patient_with_readings.current_amber_alert is False
        assert patient_with_readings.suppress_reading_alerts_from == expected_from
        assert patient_with_readings.suppress_reading_alerts_until == expected_until

    def test_clear_alerts_for_patient_unknown(self) -> None:
        with pytest.raises(EntityNotFoundException):
            controller.clear_alerts_for_patient("non_existent_uuid")

    def test_process_counts_alerts_for_reading_aborts_when_percentages(
        self,
        patient_with_readings: Patient,
        mocker: MockFixture,
        caplog: LogCaptureFixture,
    ) -> None:
        reading: Reading = patient_with_readings.readings[0]
        mocker.patch.object(
            trustomer, "get_alerts_system", return_value=AlertsSystem.PERCENTAGES
        )
        result = controller.process_counts_alerts_for_reading(reading.uuid)
        assert result["uuid"] == reading.uuid
        assert caplog.messages[-1].startswith("Process alerts for reading ignored")

    @pytest.mark.parametrize("reading_count", [4])
    def test_get_first_reading(
        self, reading_count: int, patient_with_readings: Patient
    ) -> None:
        result: Optional[Dict] = controller.retrieve_first_reading_for_patient(
            patient_with_readings.uuid
        )
        assert result is not None
        assert result["uuid"] == "reading_uuid_4"

    @pytest.mark.parametrize(
        "reading_plans,expected",
        [
            (
                [
                    {
                        "created": "2020-01-01T00:00:00.000Z",
                        "readings_per_day": 1,
                        "days_per_week_to_take_readings": 5,
                    }
                ],
                False,
            ),
            (
                [
                    {
                        "created": "2020-01-01T00:00:00.000Z",
                        "readings_per_day": 2,
                        "days_per_week_to_take_readings": 5,
                    }
                ],
                True,
            ),
            (
                [
                    {
                        "created": "2020-01-01T00:00:00.000Z",
                        "readings_per_day": 1,
                        "days_per_week_to_take_readings": 5,
                    },
                    {
                        "created": "2020-01-02T00:00:00.000Z",
                        "readings_per_day": 2,
                        "days_per_week_to_take_readings": 5,
                    },
                    {
                        "created": "2020-01-03T00:00:00.000Z",
                        "readings_per_day": 3,
                        "days_per_week_to_take_readings": 5,
                    },
                ],
                True,
            ),
            (
                [
                    {
                        "created": "2020-01-01T00:00:00.000Z",
                        "readings_per_day": 1,
                        "days_per_week_to_take_readings": 5,
                    },
                    {
                        "created": "2020-01-02T00:00:00.000Z",
                        "readings_per_day": 1,
                        "days_per_week_to_take_readings": 4,
                    },
                ],
                False,
            ),
        ],
    )
    def test_activity_alerts(
        self,
        patient_uuid: str,
        reading_dict_in: Dict,
        reading_plans: List[Dict],
        expected: bool,
    ) -> None:
        # Create a reading for the last 5 days.
        for i in range(5):
            current_day = datetime.now(tz=timezone.utc) - timedelta(days=1)
            reading_details = {
                **reading_dict_in,
                "measured_timestamp": current_day.isoformat(timespec="milliseconds"),
            }
            controller.create_reading(patient_uuid, reading_details)

        # Process activity alerts.
        result = controller.process_activity_alerts_for_patient(
            patient_uuid, reading_plans
        )
        assert result["current_activity_alert"] is expected

    def test_add_dose_to_reading(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        reading = controller.create_reading(patient_uuid, reading_dict_in)
        dose_details = {"medication_id": generate_uuid(), "amount": 1.5}
        result = controller.add_dose_to_reading(
            patient_uuid, reading["uuid"], dose_details
        )
        updated_reading = controller.retrieve_latest_reading_for_patient(patient_uuid)
        assert updated_reading is not None
        assert result["amount"] == 1.5
        assert updated_reading["uuid"] == reading["uuid"]
        assert len(reading["doses"]) == 1
        assert len(updated_reading["doses"]) == 2

    def test_update_dose_on_reading(
        self, patient_uuid: str, reading_dict_in: Dict
    ) -> None:
        reading = controller.create_reading(patient_uuid, reading_dict_in)
        dose_details = {"amount": 99.6}
        result = controller.update_dose_on_reading(
            patient_uuid, reading["uuid"], reading["doses"][0]["uuid"], dose_details
        )
        updated_reading = controller.retrieve_latest_reading_for_patient(patient_uuid)
        assert updated_reading is not None
        assert result["amount"] == 99.6
        assert updated_reading["uuid"] == reading["uuid"]
        assert len(updated_reading["doses"]) == 1
        assert updated_reading["doses"][0]["amount"] == 99.6

    def test_create_hba1c_reading_success(
        self,
        patient_uuid: str,
        hba1c_reading_dict_in: Dict,
        assert_valid_schema: Callable,
    ) -> None:

        create_response = controller.create_hba1c_reading(
            patient_uuid=patient_uuid, reading_data=hba1c_reading_dict_in
        )

        hba1c_reading: Dict = controller.get_hba1c_reading_by_uuid(
            patient_uuid=patient_uuid, hba1c_reading_uuid=create_response["uuid"]
        )
        assert_valid_schema(Hba1cReadingResponse, hba1c_reading)

        assert hba1c_reading["patient_id"] == patient_uuid

        readings: List[Dict] = list(
            controller.retrieve_hba1c_readings_for_patient(patient_uuid=patient_uuid)
        )
        assert readings[0]["uuid"] == create_response["uuid"]

    def test_create_hba1c_reading_missing_fields(
        self,
        patient_uuid: str,
    ) -> None:

        with pytest.raises(KeyError):
            controller.create_hba1c_reading(patient_uuid=patient_uuid, reading_data={})

    def test_update_hba1c_reading_success(
        self,
        patient_uuid: str,
        hba1c_reading_dict_in: Dict,
    ) -> None:

        create_response = controller.create_hba1c_reading(
            patient_uuid=patient_uuid, reading_data=hba1c_reading_dict_in
        )

        hba1c_reading_update: Dict = {
            "value": 40,
            "measured_timestamp": "2020-07-15T14:15:30.123Z",
        }

        update_response = controller.update_hba1c_reading(
            patient_uuid=patient_uuid,
            hba1c_reading_uuid=create_response["uuid"],
            reading_data=hba1c_reading_update,
        )

        assert update_response["value"] == hba1c_reading_update["value"]
        assert update_response["measured_timestamp"] == parse_iso8601_to_datetime(
            hba1c_reading_update["measured_timestamp"]
        )

        hba1c_reading: Dict = controller.get_hba1c_reading_by_uuid(
            patient_uuid=patient_uuid, hba1c_reading_uuid=create_response["uuid"]
        )

        assert hba1c_reading["value"] == hba1c_reading_update["value"]
        assert hba1c_reading["measured_timestamp"] == parse_iso8601_to_datetime(
            hba1c_reading_update["measured_timestamp"]
        )

    def test_delete_hba1c_reading_success(
        self,
        patient_uuid: str,
        hba1c_reading_dict_in: Dict,
    ) -> None:

        create_response = controller.create_hba1c_reading(
            patient_uuid=patient_uuid, reading_data=hba1c_reading_dict_in
        )

        delete_response = controller.delete_hba1c_reading(
            patient_uuid=patient_uuid, hba1c_reading_uuid=create_response["uuid"]
        )

        assert delete_response["uuid"] == create_response["uuid"]

    def test_create_hba1c_target_success(
        self,
        patient_uuid: str,
        hba1c_target_dict_in: Dict,
        assert_valid_schema: Callable,
    ) -> None:
        # Act
        target = controller.create_hba1c_target(
            patient_uuid=patient_uuid, target_data=hba1c_target_dict_in
        )
        # Assert
        assert_valid_schema(Hba1cTargetResponse, target)
        assert target["patient_id"] == patient_uuid

    def test_retrieve_hba1c_targets(
        self,
        patient_uuid: str,
        hba1c_target_dict_in: Dict,
        assert_valid_schema: Callable,
    ) -> None:
        # Arrange
        target_1 = controller.create_hba1c_target(
            patient_uuid=patient_uuid, target_data=hba1c_target_dict_in
        )
        target_2 = controller.create_hba1c_target(
            patient_uuid=patient_uuid, target_data=hba1c_target_dict_in
        )
        # Act
        targets: List[Dict] = controller.retrieve_hba1c_targets_for_patient(
            patient_uuid=patient_uuid
        )
        # Assert
        assert_valid_schema(Hba1cTargetResponse, targets, many=True)
        assert len(targets) == 2
        assert targets[0]["uuid"] == target_2["uuid"]
        assert targets[1]["uuid"] == target_1["uuid"]

    def test_update_hba1c_target_success(
        self,
        patient_uuid: str,
        hba1c_target_dict_in: Dict,
    ) -> None:
        # Arrange
        target = controller.create_hba1c_target(
            patient_uuid=patient_uuid, target_data=hba1c_target_dict_in
        )
        target_update: Dict = {"value": 40, "units": "mmol/mol"}
        # Act
        update_response = controller.update_hba1c_target(
            patient_uuid=patient_uuid,
            hba1c_target_uuid=target["uuid"],
            target_data=target_update,
        )
        # Assert
        assert update_response["value"] == target_update["value"]

    def test_validate_reading(self) -> None:
        reading_data = {
            "blood_glucose_value": 6.5,
            "comment": "Having a 'great-day'",
            "doses": [
                {"amount": 5.0, "medication_id": "73bb73d9-e892-4fe7-9cd5-d6730899cf6f"}
            ],
            "measured_timestamp": "2020-11-12T08:29:19.123+00:00",
            "prandial_tag": {"uuid": "PRANDIAL-TAG-BEFORE-BREAKFAST", "value": 1},
            "units": "mmol/L",
            "reading_metadata": {
                "control": False,
                "manual": False,
                "reading_is_correct": True,
                "transmitted_reading": None,
            },
        }
        (
            doses,
            comment,
            reading_metadata,
            reading,
            banding_id,
        ) = controller._validate_reading(reading_data)
        assert reading == {
            "blood_glucose_value": 6.5,
            "measured_timestamp": "2020-11-12T08:29:19.123+00:00",
            "prandial_tag": {"uuid": "PRANDIAL-TAG-BEFORE-BREAKFAST", "value": 1},
            "units": "mmol/L",
        }

    def test_retrieve_readings_performance(
        self, reading_dict_in_abnormal: Dict, statement_counter: Callable
    ) -> None:
        patient_1 = generate_uuid()
        base_time = datetime.now(tz=timezone.utc)

        for i in range(5000):
            measured_time = (base_time - timedelta(minutes=1 * i)).isoformat(
                timespec="milliseconds"
            )
            controller.create_reading(
                patient_id=patient_1,
                reading_data={
                    **reading_dict_in_abnormal,
                    "measured_timestamp": measured_time,
                },
            )

        with statement_counter(limit=1):
            results = controller.retrieve_readings_for_period(days=10, compact=True)
        assert len(results[patient_1]) == 5000

        with statement_counter(limit=1):
            results = controller.retrieve_readings_for_period(days=10, compact=False)
        assert len(results[patient_1]) == 5000
