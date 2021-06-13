import datetime as dt
import functools
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


def get_account_id(path_key):
    def real_valid_path_decorator(fn):
        @functools.wraps(fn)
        def real_valid_path_inner(**kwargs):
            account = models.Account.find_one_by_id(kwargs[path_key])
            if not account:
                raise abort(
                    make_response(
                        jsonify(error="Account not found"),
                        HTTPStatus.NOT_FOUND,
                    )
                )
            kwargs["account"] = account
            return fn(**kwargs)

        return real_valid_path_inner

    return real_valid_path_decorator


@bp.route("/<string:account_id>", methods=["POST"])
@json_consumer
def deposito_em_conta(account_id: str):
    transaction_date = dt.datetime.now()
    deposit_value = ser.DepositSchema().loads(request.data)
    """
    1. get the balance
    2.change the value
    3.create another entry with the change
    4.
    """
    # models.Account.
    logging.info(deposit_value)
    return "nada"
