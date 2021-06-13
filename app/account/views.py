import logging
from http import HTTPStatus

from flask import Blueprint, abort, jsonify, make_response, request

from app.account import models
from app.account import serializers as ser
from app.core.decorators import json_consumer

bp = Blueprint("account", __name__)


@bp.route("", methods=["POST"])
@json_consumer
def create_account():
    parsed_data = ser.CreateAccountSchema().load(request.json)
    create_person = not parsed_data.get("person_id")
    if create_person:
        person_data = ser.CreatePersonSchema().load(request.json)
        parsed_data["person_id"] = models.Person.save(**person_data)

    try:
        account_id = models.Account.save(**parsed_data)
        return (
            "",
            HTTPStatus.CREATED,
            {"Content-Location": f"/account/{account_id}"},
        )
    except Exception:
        if create_person:
            logging.error("Problem saving the account. But person created")
            # delete person created with created

        raise abort(
            make_response(
                jsonify(error="Problem creating the account"),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        )
