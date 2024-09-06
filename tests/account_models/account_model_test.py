import datetime as dt
import decimal as d
import unittest
import uuid
from http import HTTPStatus
from unittest import mock

import pytest
from botocore.exceptions import ClientError
from werkzeug.exceptions import HTTPException

from src.account.account.models import Account


@pytest.mark.usefixtures("client")
class TestAccountBalanceScenarios(unittest.TestCase):
    mock_resource_path = "src.account.account.models.DynamoResource"
    mock_uuid_path = "src.account.account.models.uuid"
    mock_datetime_path = "src.account.account.models.dt"

    @mock.patch(mock_resource_path)
    @mock.patch(mock_uuid_path)
    @mock.patch(mock_datetime_path)
    def test_add_account(self, mock_datetime, mock_uuid, mock_resource):
        newid = uuid.uuid4()
        mock_uuid.uuid4.return_value = str(newid)
        mock_resource_instance = mock_resource.return_value

        current_date = dt.datetime.now(dt.timezone.utc)
        mock_datetime.datetime.now.return_value = current_date

        account_id = Account.add("321", d.Decimal("54551"), d.Decimal("500"), True, 33)

        self.assertEqual(account_id, str(newid))
        mock_resource_instance.add.assert_called_once_with(
            Account.table_name,
            {
                "id": str(newid),
                "person_id": "321",
                "created_at": current_date.isoformat(),
                "balance": d.Decimal("54551"),
                "blocked": False,
                "daily_withdraw_limit": d.Decimal("500"),
                "active": True,
                "account_type": 33,
            },
        )

    @mock.patch(mock_resource_path)
    def test_find_one_by_id(self, mock_resource):
        mock_resource_instance = mock_resource.return_value

        Account.find_one_by_id("333")

        mock_resource_instance.find_one_by_id.assert_called_once_with(
            Account.table_name,
            {"hash_key": "id", "hash_value": "333"},
        )

    @mock.patch(mock_resource_path)
    def test_deposit_into(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value

        Account.deposit_into("3433", d.Decimal("33.42"))

        mock_table_instance.update_item.assert_called_once_with(
            Key={"id": "3433"},
            UpdateExpression="SET #balance = #balance + :balance",
            ExpressionAttributeNames={
                "#balance": "balance",
                "#blocked": "blocked",
            },
            ExpressionAttributeValues={
                ":balance": d.Decimal("33.42"),
                ":blocked": False,
            },
            ConditionExpression="#blocked = :blocked",
        )

    @mock.patch(mock_resource_path)
    def test_deposit_into_launches_fail_condition_error(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value

        mock_table_instance.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "Everything fails dramatically! And you get sad!",
                }
            },
            "walking without looking",
        )

        with self.assertRaises(HTTPException) as err:
            Account.deposit_into("3433", d.Decimal("33.42"))

        self.assertEqual(err.exception.response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(
            err.exception.response.json,
            {"error": "Account got blocked before the deposit execution"},
        )

    @mock.patch(mock_resource_path)
    def test_deposit_into_launches_fail_error_not_handled(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value

        mock_table_instance.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InternalServerError",
                    "Message": "Everything fails dramatically! And you get sad!",
                }
            },
            "walking without looking",
        )

        Account.deposit_into("3433", d.Decimal("33.42"))
        mock_resource_instance.handle_error.assert_called_once()

    @mock.patch(mock_resource_path)
    def test_withdraw(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value

        Account.withdraw("3433", d.Decimal("33.42"))

        mock_table_instance.update_item.assert_called_once_with(
            Key={"id": "3433"},
            UpdateExpression="SET #balance = #balance - :balance",
            ExpressionAttributeNames={
                "#balance": "balance",
                "#blocked": "blocked",
            },
            ExpressionAttributeValues={
                ":balance": d.Decimal("33.42"),
                ":blocked": False,
            },
            ConditionExpression="#blocked = :blocked And #balance > :balance",
        )

    @mock.patch(mock_resource_path)
    def test_block_account(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value

        Account.block("3433", True)

        mock_table_instance.update_item.assert_called_once_with(
            Key={"id": "3433"},
            UpdateExpression="SET #blocked = :blocked",
            ExpressionAttributeNames={
                "#blocked": "blocked",
            },
            ExpressionAttributeValues={
                ":blocked": True,
            },
        )

    @mock.patch(mock_resource_path)
    def test_block_validation_exception(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value
        mock_table_instance.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Cryptic ",
                }
            },
            "walking without looking",
        )

        with self.assertRaises(HTTPException) as err:
            Account.block("3433", True)

        self.assertEqual(err.exception.response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(
            err.exception.response.json,
            {"error": "Account not found"},
        )

    @mock.patch(mock_resource_path)
    def test_block_exception_dynamo_not_handled(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        mock_table_instance = mock_resource_instance.table_resource.return_value
        mock_table_instance.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InternalServerError",
                    "Message": "Cryptic ",
                }
            },
            "walking without looking",
        )

        Account.block("3433", True)
        mock_resource_instance.handle_error.assert_called_once()
