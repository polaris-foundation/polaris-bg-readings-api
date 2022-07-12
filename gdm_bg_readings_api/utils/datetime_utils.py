from datetime import datetime, timedelta
from typing import Optional

from flask import current_app as app
from pytz import timezone


def calculate_last_midnight(base: Optional[datetime] = None) -> datetime:
    """
    Takes in a base datetime (defaults to now if not supplied)
    and calculates the datetime of the previous midnight.
    Then it returns that datetime.

    :param base: the date to start from (defaults to now)
    :return: a datetime of the previous midnight from base
    """
    local_tz = timezone(app.config["SERVER_TIMEZONE"])

    if base is None:
        base = datetime.now()

    if base.tzinfo is None or base.tzinfo.utcoffset(base) is None:
        base = local_tz.localize(base)

    # Get convert incoming dt to server timezone
    local_datetime = base.astimezone(local_tz)

    midnight = datetime(
        local_datetime.year, local_datetime.month, local_datetime.day, 0, 0, 0, 0
    )

    # output server's midnight
    midnight_localised = local_tz.localize(midnight)

    return midnight_localised


def calculate_midnight_plus_days(base: Optional[datetime], offset: int = 0) -> datetime:
    """
    Takes in a base datetime (defaults to now if not supplied)
    and calculates the datetime of the previous midnight.
    Then returns that datetime, with a days offset applied if necessary.
    This is useful for calculating dates in requirements such as:
    "Get me all the readings from the last full 7 days"::

        start_date: datetime.datetime = calculate_midnight_plus_days(additional_days=-7)
        end_date: datetime.datetime = calculate_midnight_plus_days(additional_days=0)

    :param base: the date to start from (defaults to now)
    :param offset: the offset of days to find the midnight of
    :return: a datetime of the previous midnight from base, with offset applied
    """
    midnight = calculate_last_midnight(base=base)
    return midnight + timedelta(days=offset)
