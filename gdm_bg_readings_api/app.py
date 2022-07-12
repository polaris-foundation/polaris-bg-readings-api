from pathlib import Path

import connexion
import kombu_batteries_included
from connexion import FlaskApp
from flask import Flask
from flask_batteries_included import augment_app as fbi_augment_app
from flask_batteries_included.config import is_not_production_environment
from flask_batteries_included.sqldb import db, init_db

from gdm_bg_readings_api.blueprint_api import api_blueprint, api_blueprint_v1
from gdm_bg_readings_api.blueprint_api.exceptions import (
    init_duplicate_reading_exception_handler,
)
from gdm_bg_readings_api.blueprint_development import gdm_development
from gdm_bg_readings_api.config import init_config
from gdm_bg_readings_api.helpers.cli import add_cli_command
from gdm_bg_readings_api.utils.unittest_mode import populate_unittest_data


def create_app(
    use_pgsql: bool = True, use_sqlite: bool = False, testing: bool = False
) -> Flask:
    openapi_dir: Path = Path(__file__).parent / "openapi"
    connexion_app: FlaskApp = connexion.App(
        __name__,
        specification_dir=openapi_dir,
        options={"swagger_ui": is_not_production_environment()},
    )
    connexion_app.add_api("openapi.yaml")
    app: Flask = fbi_augment_app(
        app=connexion_app.app,
        use_pgsql=use_pgsql,
        use_sqlite=use_sqlite,
        use_auth0=True,
        testing=testing,
    )

    init_duplicate_reading_exception_handler(app)

    init_config(app)

    # Configure the SQL database
    init_db(app=app, testing=testing)

    # Initialise k-b-i library to allow publishing to RabbitMQ.
    kombu_batteries_included.init()

    # API blueprint registration
    app.register_blueprint(api_blueprint_v1, url_prefix="/gdm/v1")
    app.register_blueprint(api_blueprint, url_prefix="/gdm/v2")
    app.logger.info("Registered API blueprint")

    # Register development endpoint if in a lower environment
    if is_not_production_environment():
        app.register_blueprint(gdm_development)
        app.logger.info("Registered development blueprint")

    if testing:
        populate_unittest_data(app, db)

    add_cli_command(app)

    app.logger.info("App ready to serve requests")

    return app
