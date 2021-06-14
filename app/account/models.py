import datetime as dt
import decimal as d
import uuid
from dataclasses import dataclass
from http import HTTPStatus

import botocore
from boto3.dynamodb.conditions import Key
from flask import abort, jsonify, make_response

from app.core.aws.dynamodb import DynamoResource

date_format = "%Y-%m-%d"


class Account:
    table_name = "account"

    SUM = "+"
    SUB = "-"

    @classmethod
    def add(
        cls,
        person_id: str,
        balance: d.Decimal,
        daily_withdraw_limit: d.Decimal,
        active: bool,
        account_type: int,
    ):
        payload = {
            "id": str(uuid.uuid4()),
            "person_id": person_id,
            "created_at": dt.datetime.now().isoformat(),
            "balance": balance,
            "blocked": False,
            "daily_withdraw_limit": daily_withdraw_limit,
            "active": active,
            "account_type": account_type,
        }
        DynamoResource().add(cls.table_name, payload)
        return payload["id"]

    @classmethod
    def find_one_by_id(cls, account_id: str):
        return DynamoResource().find_one_by_id(
            cls.table_name, {"hash_key": "id", "hash_value": account_id}
        )

    @classmethod
    def _balance_operation(
        cls, account_id: str, value: d.Decimal, operator: str = "+"
    ) -> dt.datetime:
        dynamodb_resource = DynamoResource()
        withdraw_operation = operator == "-"
        expression_attr_values = {":balance": value, ":blocked": False}
        condition_expression = "#blocked = :blocked"
        if withdraw_operation:
            condition_expression = f"{condition_expression} And #balance > :balance"
        try:
            dynamodb_resource.table_resource(cls.table_name).update_item(
                Key={"id": account_id},
                UpdateExpression=f"SET #balance = #balance {operator} :balance",
                ExpressionAttributeNames={
                    "#balance": "balance",
                    "#blocked": "blocked",
                },
                ExpressionAttributeValues=expression_attr_values,
                ConditionExpression=condition_expression,
            )
            return dt.datetime.now()
        except botocore.exceptions.ClientError as error:
            error_code = error.response["Error"]["Code"]
            if error_code == "ConditionalCheckFailedException":
                error_msg = "Account got blocked before the deposit execution"
                error_msg += (
                    " or the withdraw was more than the balance available"
                    if withdraw_operation
                    else ""
                )
                raise abort(
                    make_response(
                        jsonify(error=error_msg),
                        HTTPStatus.FORBIDDEN,
                    )
                )
            dynamodb_resource.handle_error(error)

    @classmethod
    def deposit_into(cls, account_id: str, value: d.Decimal) -> dt.datetime:
        return cls._balance_operation(account_id, value, cls.SUM)

    @classmethod
    def block(cls, account_id: str, block: bool):
        dynamodb_resource = DynamoResource()
        try:
            dynamodb_resource.table_resource(cls.table_name).update_item(
                Key={"id": account_id},
                UpdateExpression="SET #blocked = :blocked",
                ExpressionAttributeNames={
                    "#blocked": "blocked",
                },
                ExpressionAttributeValues={":blocked": block},
            )
        except botocore.exceptions.ClientError as error:
            error_code = error.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise abort(
                    make_response(
                        jsonify(error="Account not found"),
                        HTTPStatus.NOT_FOUND,
                    )
                )
            dynamodb_resource.handle_error(error)

    @classmethod
    def withdraw(cls, account_id: str, value: d.Decimal):
        return cls._balance_operation(account_id, value, cls.SUB)


@dataclass
class TransactionWithdrawIndex:
    name = "withdraw_index"
    hash_key = "account_id"
    sort_key = "withdraw_date"


@dataclass
class TransactionDatetimeIndex:
    name = "transaction_date_index"
    hash_key = "account_id"
    sort_key = "created_at"


@dataclass
class TransactionIndex:
    """
    Secondary indexes helper
    """

    withdraw = TransactionWithdrawIndex
    datetime = TransactionDatetimeIndex


class Transaction:
    table_name = "transaction"

    hash_key = "account_id"
    sort_key = "id"

    @classmethod
    def add(
        cls,
        account_id: str,
        value: d.Decimal,
        operation_date: dt.datetime,
    ):
        payload = {
            cls.sort_key: str(uuid.uuid4()),
            cls.hash_key: account_id,
            "created_at": operation_date.isoformat(),
            "value": value,
        }
        if value < 0:
            payload["withdraw_date"] = operation_date.strftime(date_format)
        DynamoResource().add(cls.table_name, payload)
        return payload["id"]

    @classmethod
    def paginated_query(cls, table, key_expression, index_name: str):
        kwarsgs = {"KeyConditionExpression": key_expression}
        if index_name:
            kwarsgs["IndexName"] = index_name
        result = table.query(**kwarsgs)
        for item in result["Items"]:
            yield item

        while "LastEvaluatedKey" in result:
            args = {
                "KeyConditionExpression": key_expression,
                "ExclusiveStartKey": result["LastEvaluatedKey"],
            }
            if index_name:
                args["IndexName"] = index_name
            result = table.query(**args)
            for item in result["Items"]:
                yield item

    @classmethod
    def find_by_account_id(
        cls,
        account_id: str,
        begin_date: dt.datetime = None,
        end_date: dt.datetime = None,
        next_cursor: str = None,
    ):
        dynamodb_resource = DynamoResource()
        try:
            index = TransactionIndex.datetime
            key_expression = Key(index.hash_key).eq(account_id)
            if begin_date and end_date:
                key_expression = key_expression & Key(index.sort_key).between(
                    begin_date.isoformat(), end_date.isoformat()
                )
            elif begin_date:
                key_expression = key_expression & Key(index.sort_key).gte(
                    begin_date.isoformat()
                )
            elif end_date:
                key_expression = key_expression & Key(index.sort_key).lt(
                    end_date.isoformat()
                )

            return dynamodb_resource.table_resource(cls.table_name).query(
                KeyConditionExpression=key_expression,
                IndexName=index.name
            )
        except botocore.exceptions.ClientError as error:
            dynamodb_resource.handle_error(error)

    @classmethod
    def find_withdraw_limit_available(cls, account_id: str):
        dynamodb_resource = DynamoResource()
        try:
            index = TransactionIndex.withdraw
            key_expression = Key(index.hash_key).eq(account_id) & Key(
                index.sort_key
            ).eq(dt.datetime.now().strftime(date_format))
            table = dynamodb_resource.table_resource(cls.table_name)
            return sum(
                i["value"]
                for i in cls.paginated_query(
                    table,
                    key_expression,
                    index.name,
                )
            )
        except botocore.exceptions.ClientError as error:
            dynamodb_resource.handle_error(error)


class Person:
    """
    Not a column of account with the excuse that a person my have multiple accounts
    """

    table_name = "person"

    @classmethod
    def add(cls, name: str, cpf: str, birth: dt.date):
        payload = {
            "id": str(uuid.uuid4()),
            "name": name,
            "cpf": cpf,
            "birth": str(birth),
        }
        DynamoResource().add(cls.table_name, payload)
        return payload["id"]
