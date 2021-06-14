import datetime as dt
import decimal as d
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
    parsed_data = ser.CreateAccountSchema().loads(request.data)
    create_person = not parsed_data.get("person_id")
    if create_person:
        person_data = ser.CreatePersonSchema().loads(request.data)
        parsed_data["person_id"] = models.Person.add(**person_data)

    try:
        account_id = models.Account.add(**parsed_data)
        return (
            "",
            HTTPStatus.CREATED,
            {"Content-Location": f"/account/{account_id}"},
        )
    except Exception:
        if create_person:
            logging.error("Problem saving the account. But person created")
            # delete person if created now

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
                return (
                    {"error": "Account not found"},
                    HTTPStatus.NOT_FOUND,
                )
            kwargs["account"] = account
            return fn(**kwargs)

        return real_valid_path_inner

    return real_valid_path_decorator


def abort_blocked(f):
    @functools.wraps(f)
    def decorated_function(account_id: str, account: dict):
        if account["blocked"]:
            return {"error": "Account is blocked"}, HTTPStatus.FORBIDDEN
        return f(account_id, account)

    return decorated_function


def register_new_transaction(
    account_id: str, transaction_date: dt.datetime, value: d.Decimal
):
    transaction_id = models.Transaction.add(account_id, value, transaction_date)
    return (
        "",
        HTTPStatus.CREATED,
        {"Content-Location": f"/account/{account_id}/transaction/{transaction_id}"},
    )


@bp.route("/<string:account_id>/deposit", methods=["POST"])
@get_account_id(
    "account_id"
)  # not ideal but only notice this flaw sunday and was already too late
@abort_blocked
@json_consumer
def deposito_em_conta(account_id: str, account: dict):
    deposit_value = ser.DepositSchema().loads(request.data)
    transaction_date = models.Account.deposit_into(account_id, deposit_value["value"])
    return register_new_transaction(
        account_id, transaction_date, deposit_value["value"]
    )


@bp.route("/<string:account_id>/balance", methods=["GET"])
@get_account_id("account_id")
def get_balance(account_id: str, account: dict):
    withdrawn_today = models.Transaction.find_withdraw_limit_available(account_id)
    withdraw_available = account["daily_withdraw_limit"] - withdrawn_today
    account["withdraw_available"] = withdraw_available if withdraw_available > 0 else 0
    return ser.BalanceResponse().dump(account)


@bp.route("/<string:account_id>/block", methods=["PATCH"])
@json_consumer
def block_account(account_id: str):
    payload = ser.BlockAccountSchema().loads(request.data)
    models.Account.block(account_id, payload["block"])
    return "", HTTPStatus.NO_CONTENT


@bp.route("/<string:account_id>/withdraw", methods=["POST"])
@get_account_id("account_id")
@abort_blocked
@json_consumer
def withdraw(account_id: str, account: str):
    withdraw_data = ser.WithdrawSchema().loads(request.data)

    if account["balance"] < withdraw_data["value"]:
        return {
            "error": "withdrawa value greater than available in the account"
        }, HTTPStatus.FORBIDDEN

    error_msg = "It is not possible to carry out the withdraw"
    daily_limit = account["daily_withdraw_limit"]
    if withdraw_data["value"] > daily_limit:
        error_msg = f"{error_msg}. Limit reached."
        return {"error": error_msg}, HTTPStatus.FORBIDDEN

    reached_limit = models.Transaction.find_withdraw_limit_available(account_id)
    available_limit = daily_limit - reached_limit
    if withdraw_data["value"] > available_limit:
        available_msg = available_limit if available_limit > 0 else 0
        error_msg = f"{error_msg}. Withdraw available is R$ {available_msg}"
        return {"error": error_msg}, HTTPStatus.FORBIDDEN

    transaction_date = models.Account.withdraw(account_id, withdraw_data["value"])
    return register_new_transaction(
        account_id, transaction_date, withdraw_data["value"] * -1
    )
