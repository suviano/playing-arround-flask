import functools
from http import HTTPStatus

from flask import abort, jsonify, make_response, request


def json_consumer(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "application/json" not in request.headers.get("Content-Type", ""):
            raise abort(
                make_response(
                    jsonify(error="content-type must be application/json"),
                    HTTPStatus.BAD_REQUEST,
                )
            )
        return f(*args, **kwargs)

    return decorated_function
