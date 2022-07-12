from datetime import datetime, timezone

import pytest
import pytz

from gdm_bg_readings_api.utils.datetime_utils import (
    calculate_last_midnight,
    calculate_midnight_plus_days,
)


@pytest.mark.usefixtures("app")
class TestDatetimeUtils:
    def test_calculate_last_midnight(self) -> None:
        base = datetime(2018, 4, 1, 16, 57, 8, tzinfo=timezone.utc)
        assert str(calculate_last_midnight(base=base)) == "2018-04-01 00:00:00+01:00"
        base2 = datetime(2018, 3, 31, 23, 30, 0, tzinfo=timezone.utc)
        assert str(calculate_last_midnight(base=base2)) == "2018-04-01 00:00:00+01:00"
        eastern = pytz.timezone("US/Eastern")
        base3 = datetime(2018, 3, 31, 23, 30, 0, tzinfo=eastern)
        assert str(calculate_last_midnight(base=base3)) == "2018-04-01 00:00:00+01:00"
        sydney = pytz.timezone("Australia/Sydney")
        base4 = datetime(2018, 4, 1, 6, 30, 0, tzinfo=sydney)
        assert str(calculate_last_midnight(base=base4)) == "2018-03-31 00:00:00+01:00"

    def test_calculate_suppress_alerts_until(self) -> None:
        base = datetime(2018, 4, 1, 16, 57, 8, tzinfo=timezone.utc)
        assert (
            str(calculate_midnight_plus_days(base=base, offset=2))
            == "2018-04-03 00:00:00+01:00"
        )

    def test_from_midnight_calculation_fixed_datetime(self) -> None:
        fixed_datetime = datetime(
            year=2017,
            month=11,
            day=5,
            hour=7,
            minute=45,
            second=13,
            microsecond=943,
            tzinfo=timezone.utc,
        )

        assert calculate_last_midnight(fixed_datetime) == datetime(
            year=2017, month=11, day=5, tzinfo=timezone.utc
        )
