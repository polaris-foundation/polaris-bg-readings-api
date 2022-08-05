import contextlib
import json
from datetime import datetime, timedelta
from typing import (
    Callable,
    ContextManager,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Type,
    Union,
)

import pytest
import sqlalchemy
from flask import Flask
from flask_batteries_included.helpers import generate_uuid
from flask_batteries_included.sqldb import db
from marshmallow import RAISE, Schema
from mock import Mock
from pytest_mock import MockFixture
from sqlalchemy.orm import Session

from gdm_bg_readings_api import trustomer
from gdm_bg_readings_api.blueprint_api import controller
from gdm_bg_readings_api.models.patient import Patient
from gdm_bg_readings_api.models.reading import Reading


@pytest.fixture
def mock_publish_abnormal(mocker: MockFixture) -> Mock:
    return mocker.patch.object(
        controller, "publish_abnormal_reading", return_value=None
    )


@pytest.fixture(scope="session")
def session_app() -> Flask:
    import gdm_bg_readings_api.app

    return gdm_bg_readings_api.app.create_app(
        use_pgsql=False, use_sqlite=True, testing=True
    )


@pytest.fixture
def app(session_app: Flask) -> Flask:
    """Fixture that creates app for testing"""
    import gdm_bg_readings_api.app

    return gdm_bg_readings_api.app.create_app(
        use_pgsql=False, use_sqlite=True, testing=True
    )


@pytest.fixture
def app_context(app: Flask) -> Generator[None, None, None]:
    with app.app_context():
        yield


@pytest.fixture
def assert_valid_schema(
    app: Flask,
) -> Callable[[Type[Schema], Union[Dict, List], bool], None]:
    def verify_schema(
        schema: Type[Schema], value: Union[Dict, List], many: bool = False
    ) -> None:
        # Roundtrip through JSON to convert datetime values to strings.
        serialised = json.loads(json.dumps(value, cls=app.json_encoder))
        schema().load(serialised, many=many, unknown=RAISE)

    return verify_schema


@pytest.fixture
def patient_uuid() -> str:
    return "patient_uuid"


@pytest.fixture
def hba1c_reading_uuid() -> str:
    return "hba1c_reading_uuid"


@pytest.fixture
def hba1c_target_uuid() -> str:
    return "hba1c_target_uuid"


@pytest.fixture
def alerts_system() -> str:
    return "counts"


@pytest.fixture
def gdm_config(alerts_system: str) -> Dict:
    return {
        "alerts_snooze_duration_days": 2,
        "alerts_system": alerts_system,
        "blood_glucose_units": "mmol/L",
    }


@pytest.fixture
def mock_trustomer(mocker: MockFixture, gdm_config: Dict) -> Mock:
    expected = {"gdm_config": gdm_config}
    return mocker.patch.object(trustomer, "get_trustomer_config", return_value=expected)


@pytest.fixture
def sample_readings_plans() -> List[Dict]:
    return [
        {
            "created": "2017-01-01T00:00:00.000Z",
            "readings_per_day": 4,
            "days_per_week_to_take_readings": 5,
        },
        {
            "created": "2018-01-01T00:00:00.000Z",
            "readings_per_day": 4,
            "days_per_week_to_take_readings": 5,
        },
        {
            "created": "2019-01-01T00:00:00.000Z",
            "readings_per_day": 4,
            "days_per_week_to_take_readings": 5,
        },
    ]


@pytest.mark.freeze_time("2019-11-14 00:00:00.000")
@pytest.fixture
def patient_with_readings(patient_uuid: str) -> Generator[Patient, None, None]:
    patient = Patient(uuid=patient_uuid, current_activity_alert=False)
    readings = [
        Reading(
            uuid=f"reading_uuid_{i+1}",
            measured_timestamp=datetime.now() - timedelta(days=1, hours=i),
            measured_timezone=0,
            blood_glucose_value=5.5,
            units="mmol/L",
            patient_id=1,
            doses=[],
        )
        for i in range(1)
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
def reading_dict_in() -> Dict:
    return {
        "prandial_tag": {"value": 2},
        "blood_glucose_value": 23.0,
        "units": "mmol/L",
        "measured_timestamp": "2000-01-01T01:01:01.000Z",
        "reading_metadata": {
            "meter_serial_number": "kbwiebc",
            "meter_model": "ksrbwi",
            "manufacturer": "wiefiwb",
            "control": False,
            "manual": False,
        },
        "doses": [{"amount": 123, "medication_id": generate_uuid()}],
        "banding_id": "BG-READING-BANDING-NORMAL",
    }


@pytest.fixture
def reading_dict_in_abnormal() -> Dict:
    return {
        "prandial_tag": {"value": 2},
        "blood_glucose_value": 99.0,
        "units": "mmol/L",
        "measured_timestamp": "2000-01-01T01:01:01.000Z",
        "reading_metadata": {
            "meter_serial_number": "kbwiebc",
            "meter_model": "ksrbwi",
            "manufacturer": "wiefiwb",
            "control": False,
            "manual": False,
        },
        "doses": [{"amount": 123, "medication_id": generate_uuid()}],
        "banding_id": "BG-READING-BANDING-HIGH",
    }


@pytest.fixture
def hba1c_reading_dict_in() -> Dict:
    return {
        "value": 41,
        "units": "mmol/mol",
        "measured_timestamp": "2020-06-14T13:15:20.456Z",
    }


@pytest.fixture
def hba1c_target_dict_in() -> Dict:
    return {
        "value": 41.5,
        "units": "mmol/mol",
        "target_timestamp": "2021-01-02T03:04:05.678Z",
    }


class DBStatementCounter(object):
    def __init__(self, limit: int = None) -> None:
        self.clauses: list[sqlalchemy.sql.ClauseElement] = []
        self.limit = limit

    @property
    def count(self) -> int:
        return len(self.clauses)

    def callback(
        self,
        conn: sqlalchemy.engine.Connection,
        clauseelement: sqlalchemy.sql.ClauseElement,
        multiparams: list[dict],
        params: dict,
        execution_options: dict,
    ) -> None:
        if isinstance(clauseelement, sqlalchemy.sql.elements.SavepointClause):
            return

        self.clauses.append(clauseelement)
        if self.limit:
            if len(self.clauses) > self.limit:
                clauses = [str(clause) for clause in self.clauses]
                print(clauses)
            assert (
                len(self.clauses) <= self.limit
            ), f"Too many SQL statements (limit was {self.limit})"


@contextlib.contextmanager
def db_statement_counter(
    limit: int = None, session: Session = None
) -> Iterator[DBStatementCounter]:
    if session is None:
        session = db.session
    counter = DBStatementCounter(limit=limit)
    cb = counter.callback
    sqlalchemy.event.listen(db.engine, "before_execute", cb)
    try:
        yield counter
    finally:
        sqlalchemy.event.remove(db.engine, "before_execute", cb)


@pytest.fixture
def statement_counter() -> Callable[
    [Optional[int], Optional[Session]], ContextManager[DBStatementCounter]
]:
    return db_statement_counter
