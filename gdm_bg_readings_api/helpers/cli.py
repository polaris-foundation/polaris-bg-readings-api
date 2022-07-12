import click
from flask import Flask
from flask_batteries_included.helpers.apispec import generate_openapi_spec

from gdm_bg_readings_api import blueprint_api
from gdm_bg_readings_api.models.api_spec import gdm_bg_readings_api_spec


def add_cli_command(app: Flask) -> None:
    @app.cli.command("create-openapi")
    @click.argument("output", type=click.Path())
    def create_api(output: str) -> None:
        generate_openapi_spec(
            gdm_bg_readings_api_spec,
            output,
            blueprint_api.api_blueprint,
            blueprint_api.api_blueprint_v1,
        )
