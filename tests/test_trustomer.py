from typing import Any
from unittest.mock import Mock

import pytest
import requests
from flask_batteries_included.helpers.error_handler import ServiceUnavailableException
from requests_mock import Mocker

from gdm_bg_readings_api import trustomer
from gdm_bg_readings_api.trustomer import AlertsSystem


@pytest.mark.usefixtures("app")
class TestTrustomer:
    def test_get_config_success(self, requests_mock: Mocker) -> None:
        trustomer._cache.clear()
        trustomer_config = {"some": "config"}
        mock_get: Any = requests_mock.get(
            f"{trustomer.get_trustomer_base_url()}/dhos/v1/trustomer/test",
            json=trustomer_config,
        )
        actual = trustomer.get_trustomer_config()
        assert actual == trustomer_config
        assert mock_get.call_count == 1
        assert (
            mock_get.last_request.headers["Authorization"]
            == "secret"  # From tox.ini env var
        )

    def test_get_config_failure(self, requests_mock: Mocker) -> None:
        trustomer._cache.clear()
        mock_get: Any = requests_mock.get(
            f"{trustomer.get_trustomer_base_url()}/dhos/v1/trustomer/test",
            exc=requests.exceptions.ConnectionError,
        )
        with pytest.raises(ServiceUnavailableException):
            trustomer.get_trustomer_config()
        assert mock_get.call_count == 1

    @pytest.mark.parametrize(
        ["alerts_system", "expected"],
        [("counts", AlertsSystem.COUNTS), ("percentages", AlertsSystem.PERCENTAGES)],
    )
    def test_get_alerts_system(
        self, mock_trustomer: Mock, alerts_system: str, expected: AlertsSystem
    ) -> None:
        actual = trustomer.get_alerts_system()
        assert actual == expected

    def test_get_alerts_snooze_duration_days(self, mock_trustomer: Mock) -> None:
        duration = trustomer.get_alerts_snooze_duration_days()
        assert duration == 2
