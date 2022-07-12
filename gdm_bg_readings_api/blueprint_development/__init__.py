import time

from flask import Blueprint, Response, abort, current_app, jsonify, render_template
from flask_batteries_included.helpers.security import protected_route
from flask_batteries_included.helpers.security.endpoint_security import key_present

from .controller import reset_database

gdm_development = Blueprint("gdm/dev", __name__, template_folder="templates")


@gdm_development.route("/drop_data", methods=["POST"])
@protected_route(key_present("system_id"))
def drop_data_route() -> Response:

    if current_app.config["ALLOW_DROP_DATA"] is not True:
        raise PermissionError("Cannot drop data in this environment")

    start = time.time()
    reset_database()
    total_time = time.time() - start
    return jsonify({"complete": True, "time_taken": str(total_time) + "s"})


@gdm_development.route("/viewer")
@protected_route(key_present("system_id"))
def view_data() -> str:
    return render_template("development/viewer.html")
