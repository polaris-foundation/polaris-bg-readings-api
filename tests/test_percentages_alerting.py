from datetime import datetime, timezone
from typing import Dict, Generator, List, Optional

import pytest
from flask_batteries_included.sqldb import db
from freezegun.api import FrozenDateTimeFactory
from mock import Mock
from pytest_mock import MockFixture

from gdm_bg_readings_api.blueprint_api import percentages_alerting
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.patient_alert import PatientAlert


@pytest.mark.usefixtures("app")
class TestPercentagesAlerting:
    @pytest.fixture
    def four_sample_alerts(self) -> Generator[List[PatientAlert], None, None]:
        alerts = [
            PatientAlert(
                uuid="old_red",
                started_at=datetime(2019, 1, 1, 0, 0, 0, 0),
                ended_at=datetime(2019, 1, 2, 0, 0, 0, 0),
                alert_type=PatientAlert.AlertType.PERCENTAGES_RED,
                patient_id="patient_uuid",
            ),
            PatientAlert(
                uuid="old_amber",
                started_at=datetime(2019, 1, 1, 0, 0, 0, 0),
                ended_at=datetime(2019, 1, 2, 0, 0, 0, 0),
                alert_type=PatientAlert.AlertType.PERCENTAGES_AMBER,
                patient_id="patient_uuid",
            ),
            PatientAlert(
                uuid="active_red",
                started_at=datetime(2019, 1, 3, 0, 0, 0, 0),
                alert_type=PatientAlert.AlertType.PERCENTAGES_RED,
                patient_id="patient_uuid",
            ),
            PatientAlert(
                uuid="active_amber",
                started_at=datetime(2019, 1, 3, 0, 0, 0, 0),
                alert_type=PatientAlert.AlertType.PERCENTAGES_AMBER,
                patient_id="patient_uuid",
            ),
        ]
        db.session.add_all(alerts)
        db.session.commit()

        yield alerts

        for a in alerts:
            db.session.delete(a)
        db.session.commit()

    def test_filter_unnecessary_plans_no_created(
        self, sample_readings_plans: List[Dict]
    ) -> None:
        sample_readings_plans[0]["created"] = None
        with pytest.raises(ValueError):
            percentages_alerting._filter_unnecessary_plans(
                plans=sample_readings_plans, start_date=datetime.now()
            )

    @pytest.mark.parametrize(
        ["suppress_from_dt", "suppress_until_dt"],
        [(None, None), (datetime.now(), None), (None, datetime.now())],
    )
    def test_is_patient_in_snooze_period_incomplete(
        self,
        suppress_from_dt: Optional[datetime],
        suppress_until_dt: Optional[datetime],
    ) -> None:
        patient = Patient(
            suppress_reading_alerts_from=suppress_from_dt,
            suppress_reading_alerts_until=suppress_until_dt,
        )
        snoozed = percentages_alerting.is_patient_in_snooze_period(patient)
        assert snoozed is False

    @pytest.mark.parametrize(
        ["mock_time_now", "should_snooze"],
        [
            ("2019-05-31", False),
            ("2019-06-01", True),
            ("2019-06-05", True),
            ("2019-06-10", True),
            ("2019-06-11", False),
        ],
    )
    def test_is_patient_in_snooze_period_complete(
        self, freezer: FrozenDateTimeFactory, mock_time_now: str, should_snooze: bool
    ) -> None:
        # Snoozed from June 1st to June 10th. Vary the date "now", and check that
        # the snooze status is flagged correctly when we're in that period.
        patient = Patient(
            suppress_reading_alerts_from=datetime(2019, 6, 1, 0, 0, 0, 0),
            suppress_reading_alerts_until=datetime(2019, 6, 10, 0, 0, 0, 0),
        )
        freezer.move_to(mock_time_now)
        snoozed = percentages_alerting.is_patient_in_snooze_period(patient)
        assert snoozed is should_snooze

    def test_update_alerts_for_patient_none_preexisting(
        self, mocker: MockFixture
    ) -> None:
        # We start with no alerts. Check that when we update the alerts for a given patient,
        # with red being true and amber being false, we end up with only one alert (a red one).
        mock_publish: Mock = mocker.patch.object(
            percentages_alerting, "publish_patient_alert"
        )
        patient = Patient(uuid="patient_uuid")
        percentages_alerting.update_alerts_for_patient(
            patient=patient,
            alert_type=PatientAlert.AlertType.PERCENTAGES_AMBER,
            alert_now=False,
        )
        percentages_alerting.update_alerts_for_patient(
            patient=patient,
            alert_type=PatientAlert.AlertType.PERCENTAGES_RED,
            alert_now=True,
        )
        resulting_alerts: List[PatientAlert] = PatientAlert.query.filter_by(
            patient_id=patient.uuid
        ).all()
        assert len(resulting_alerts) == 1
        assert resulting_alerts[0].alert_type == PatientAlert.AlertType.PERCENTAGES_RED
        assert mock_publish.call_count == 1
        mock_publish.assert_called_with(
            patient_uuid=patient.uuid, alert_type=PatientAlert.AlertType.PERCENTAGES_RED
        )

    def test_update_alerts_for_patient_preexisting(
        self, four_sample_alerts: List[PatientAlert], mocker: MockFixture
    ) -> None:
        # We start with four existing alerts for a patient, two of which are open (one red,
        # one amber). Check that when we update the alerts for that patient, with red being
        # true and amber being false, we still have those four alerts, but that only the open
        # red one is still active - the open amber one should have been closed. We also should
        # not have published any new alerts.
        mock_publish = mocker.patch.object(
            percentages_alerting, "publish_patient_alert"
        )
        patient = Patient(uuid="patient_uuid")
        percentages_alerting.update_alerts_for_patient(
            patient=patient,
            alert_type=PatientAlert.AlertType.PERCENTAGES_AMBER,
            alert_now=False,
        )
        percentages_alerting.update_alerts_for_patient(
            patient=patient,
            alert_type=PatientAlert.AlertType.PERCENTAGES_RED,
            alert_now=True,
        )
        resulting_alerts: List[PatientAlert] = PatientAlert.query.filter_by(
            patient_id=patient.uuid
        ).all()
        # There should still be four alerts, but only the red should be left active.
        assert len(resulting_alerts) == 4
        assert len([a for a in resulting_alerts if a.ended_at is None]) == 1
        assert (
            next(a for a in resulting_alerts if a.uuid == "active_red").ended_at is None
        )
        assert (
            next(a for a in resulting_alerts if a.uuid == "active_amber").ended_at
            is not None
        )
        assert mock_publish.call_count == 0

    def test_dismiss_active_alerts_for_patient(
        self, four_sample_alerts: List[PatientAlert]
    ) -> None:
        # Arrange - no dismissed alerts
        for a in four_sample_alerts:
            a.dismissed_at = None
        # Act - call the function under test
        percentages_alerting.dismiss_active_alerts_for_patient("patient_uuid")
        # Assert - make sure the active alerts have been dismissed
        for a in four_sample_alerts:
            if a.ended_at is None:
                # Alert is active and should have been dismissed
                assert a.dismissed_at is not None
            else:
                # Alert isn't active and should not have been dismissed
                assert a.dismissed_at is None

    def test_calculate_expected_reading_count_single_plan(self) -> None:
        basic_plan = {
            "created": "2017-10-16T04:00:00.000Z",
            "days_per_week_to_take_readings": 5,
            "readings_per_day": 3,
        }
        start_date = datetime(2017, 11, 5, 0, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2017, 11, 12, 0, 0, 0, 0, tzinfo=timezone.utc)

        assert (
            percentages_alerting.calculate_expected_reading_count(
                [basic_plan], start_date, end_date
            )
            == 15
        )

    def test_calculate_expected_reading_count_2_plans(self) -> None:
        plans = [
            {
                "created": "2017-10-16T04:00:00.000Z",
                "days_per_week_to_take_readings": 5,
                "readings_per_day": 2,
            },
            {
                "created": "2017-10-18T04:00:00.000Z",
                "days_per_week_to_take_readings": 5,
                "readings_per_day": 4,
            },
        ]
        start_date = datetime(2017, 10, 16, 0, 0, 0, 0, timezone.utc)
        end_date = datetime(2017, 10, 24, 0, 0, 0, 0, timezone.utc)

        value = percentages_alerting.calculate_expected_reading_count(
            plans, start_date, end_date
        )
        assert round(value) == 17
