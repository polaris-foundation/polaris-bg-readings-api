from datetime import datetime, timedelta
from typing import Any, Generator

import pytest
from flask_batteries_included.sqldb import db, generate_uuid
from mock import MagicMock
from pytest_mock import MockFixture

from gdm_bg_readings_api.blueprint_api import counts_alerting
from gdm_bg_readings_api.models.amber_alert import AmberAlert
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.patient_alert import PatientAlert
from gdm_bg_readings_api.models.reading import Reading
from gdm_bg_readings_api.models.red_alert import RedAlert


@pytest.mark.usefixtures("app")
class TestCountsAlerting:
    @pytest.fixture
    def patient_with_two_high_readings(self) -> Generator[Patient, None, None]:
        patient = Patient(uuid=generate_uuid(), current_amber_alert=False)
        readings = [
            Reading(
                uuid=f"reading_uuid_{i + 1}",
                measured_timestamp=datetime.now() - timedelta(days=1, hours=i),
                measured_timezone=0,
                blood_glucose_value=14,
                units="mmol/L",
                patient_id=patient.uuid,
                reading_banding_id="BG-READING-BANDING-HIGH",
            )
            for i in range(2)
        ]
        db.session.add_all(readings)
        db.session.add(patient)
        db.session.commit()

        yield patient

        for r in readings:
            db.session.delete(r)
        db.session.delete(patient)
        db.session.commit()

    @pytest.fixture
    def patient_with_active_counts_alerts(self) -> Generator[Patient, None, None]:
        patient = Patient(uuid=generate_uuid())
        amber_alert = AmberAlert(uuid=generate_uuid())
        red_alert = RedAlert(uuid=generate_uuid())
        reading = Reading(
            uuid=generate_uuid(),
            measured_timestamp=datetime.now(),
            measured_timezone=0,
            blood_glucose_value=14,
            units="mmol/L",
            patient_id=patient.uuid,
            reading_banding_id="BG-READING-BANDING-HIGH",
            amber_alert=amber_alert,
            amber_alert_id=amber_alert.uuid,
            red_alert=red_alert,
            red_alert_id=red_alert.uuid,
        )

        db.session.add(amber_alert)
        db.session.add(red_alert)
        db.session.add(reading)
        db.session.add(patient)
        db.session.commit()

        yield patient

        db.session.delete(amber_alert)
        db.session.delete(red_alert)
        db.session.delete(reading)
        db.session.delete(patient)
        db.session.commit()

    def test_process_amber_alertable_readings(
        self, patient_with_two_high_readings: Patient, mocker: MockFixture
    ) -> None:
        mock_publish: MagicMock = mocker.patch.object(
            counts_alerting, "publish_patient_alert"
        )
        result = counts_alerting.process_amber_alertable_readings(
            reading=patient_with_two_high_readings.readings[0]
        )
        assert result.patient.current_amber_alert is True
        assert result.amber_alert is not None
        assert mock_publish.call_count == 1
        mock_publish.assert_called_with(
            patient_uuid=patient_with_two_high_readings.uuid,
            alert_type=PatientAlert.AlertType.COUNTS_AMBER,
        )

        # Clean up resulting alert.
        AmberAlert.query.delete()

    def test_dismiss_active_alerts_for_patient(
        self, patient_with_active_counts_alerts: Patient
    ) -> None:
        patient_uuid: str = patient_with_active_counts_alerts.uuid
        counts_alerting.dismiss_active_alerts_for_patient(patient_id=patient_uuid)
        reading = patient_with_active_counts_alerts.readings[0]
        assert reading.red_alert.dismissed is True
        assert reading.amber_alert.dismissed is True

    def test_is_reading_in_snooze_period(self) -> None:
        reading = Reading()
        patient = Patient()
        assert counts_alerting.is_reading_in_snooze_period(reading, patient) is False
        patient.suppress_reading_alerts_from = datetime(2019, 1, 2, 0, 0, 0)
        assert counts_alerting.is_reading_in_snooze_period(reading, patient) is False
        patient.suppress_reading_alerts_until = datetime(2019, 1, 10, 0, 0, 0)

        # Reading before snooze
        reading.measured_timestamp = datetime(2019, 1, 1, 0, 0, 0)
        assert counts_alerting.is_reading_in_snooze_period(reading, patient) is False

        # Reading during snooze
        reading.measured_timestamp = datetime(2019, 1, 6, 0, 0, 0)
        assert counts_alerting.is_reading_in_snooze_period(reading, patient) is True

        # Reading after snooze
        reading.measured_timestamp = datetime(2019, 1, 12, 0, 0, 0)
        assert counts_alerting.is_reading_in_snooze_period(reading, patient) is False

    def test_reading_could_trigger_alert(self) -> None:
        reading = Reading()
        reading.reading_banding_id = "BG-READING-BANDING-NORMAL"
        assert counts_alerting.reading_could_trigger_alert(reading) is False
        reading.reading_banding_id = "BG-READING-BANDING-HIGH"
        assert counts_alerting.reading_could_trigger_alert(reading) is True
        reading.snoozed = True
        assert counts_alerting.reading_could_trigger_alert(reading) is False

    def test_reading_could_trigger_red_alert(self) -> None:
        reading = Reading()
        reading.reading_banding_id = "BG-READING-BANDING-HIGH"
        assert counts_alerting.reading_could_trigger_red_alert(reading) is True
        reading.red_alert = RedAlert()
        reading.red_alert.dismissed = True
        assert counts_alerting.reading_could_trigger_red_alert(reading) is False
