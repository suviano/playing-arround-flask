import pprint
from http import HTTPStatus

from flask import Blueprint, abort, request

from app.account import serializers as ser

bp = Blueprint("account", __name__)


@bp.route("", methods=["POST"])
def create_account():
    if not request.json:
        raise abort(HTTPStatus.BAD_REQUEST, error="empty request body")

    parsed_data = ser.CreateAccountSchema().load(request.json)
    pprint.pprint(parsed_data)
    account_id = 3333
    return (
        '',
        HTTPStatus.CREATED,
        {"Content-Location": account_id},
    )
