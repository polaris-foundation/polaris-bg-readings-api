from pathlib import Path

import pytest
import yaml
from flask import Flask
from flask_batteries_included import init_metrics, init_monitoring
from flask_batteries_included.helpers.apispec import generate_openapi_spec

from gdm_bg_readings_api.blueprint_api import api_blueprint, api_blueprint_v1
from gdm_bg_readings_api.models.api_spec import gdm_bg_readings_api_spec


@pytest.mark.usefixtures("app")
def test_openapi(tmp_path: str, app: Flask) -> None:

    # Add the metrics paths to the app
    init_monitoring(app)
    init_metrics(app)

    new_spec_path = Path(tmp_path) / "testapi.yaml"

    generate_openapi_spec(
        gdm_bg_readings_api_spec, new_spec_path, api_blueprint, api_blueprint_v1
    )

    new_spec = yaml.safe_load(new_spec_path.read_bytes())
    existing_spec = (
        Path(__file__).parent / "../gdm_bg_readings_api/openapi/openapi.yaml"
    )
    existing = yaml.safe_load(existing_spec.read_bytes())

    assert existing == new_spec
