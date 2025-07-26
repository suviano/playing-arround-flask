import functools
import urllib.parse
from http import HTTPStatus

from flask import abort, jsonify, make_response, request


def json_consumer(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "application/json" not in request.headers.get("Content-Type", ""):
            abort(
                make_response(
                    jsonify(error="content-type must be application/json"),
                    HTTPStatus.BAD_REQUEST,
                )
            )
        return f(*args, **kwargs)

    return decorated_function


def query_to_json(schema):
    def query_to_json_decorator(fn):
        @functools.wraps(fn)
        def query_to_json_inner(**kwargs):
            query = urllib.parse.parse_qsl(request.query_string)
            kwargs["queries"] = schema().load(
                {q[0].decode("utf-8"): q[1].decode("utf-8") for q in query}
            )
            return fn(**kwargs)

        return query_to_json_inner

    return query_to_json_decorator
