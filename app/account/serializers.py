from http import HTTPStatus

import marshmallow as ma
from flask import abort, jsonify, make_response


class CreatePersonSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE

    name = ma.fields.Str(data_key="nome", required=True)
    cpf = ma.fields.Str(required=True)
    birth = ma.fields.Date(data_key="dataNascimento", required=True)


class CreateAccountSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE

    balance = ma.fields.Decimal(required=True, data_key="saldo")
    active = ma.fields.Bool(required=True, data_key="flagAtivo")
    daily_withdraw_limit = ma.fields.Decimal(
        required=True, data_key="limiteSaqueDiario"
    )
    account_type = ma.fields.Integer(required=True, data_key="tipoConta")
    person_id = ma.fields.Str(data_key="idPessoa")


class DepositSchema(ma.Schema):
    value = ma.fields.Decimal(required=True, data_key="valor")

    @ma.post_load
    def post_load(self, data, **_):
        if data["value"] < 0:
            raise abort(
                make_response(
                    jsonify(error="Depósito aceita penas valores positivos"),
                    HTTPStatus.BAD_REQUEST,
                )
            )
        return data
