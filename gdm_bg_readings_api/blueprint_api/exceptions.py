from typing import Dict, Optional, Tuple

import flask
from flask import Flask, Response
from flask_batteries_included.helpers.error_handler import DuplicateResourceException
from she_logging import logger


class DuplicateReadingException(DuplicateResourceException):
    def __init__(
        self, message: str, extra: Optional[Dict] = None, headers: Optional[Dict] = None
    ):
        super(DuplicateReadingException, self).__init__(message)

        self.extra = extra if extra else {}
        self.headers = headers if headers else {}


def catch_duplicate_reading_exception(
    error: DuplicateReadingException,
) -> Tuple[Response, int]:
    logger.warning(str(error), extra=error.extra)
    resp: flask.Response = flask.jsonify({"message": str(error), "extra": error.extra})
    resp.headers.update(error.headers)
    return resp, 409


def init_duplicate_reading_exception_handler(app: Flask) -> None:
    # fixme: https://sensynehealth.atlassian.net/browse/PLAT-874
    app.errorhandler(DuplicateReadingException)(catch_duplicate_reading_exception)
