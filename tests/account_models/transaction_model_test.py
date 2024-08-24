import datetime as dt
import decimal as d
import unittest
import uuid
from unittest import mock

from botocore.exceptions import ClientError

from app.account.models import Transaction, date_format


class TestAccountBalanceScenarios(unittest.TestCase):
    mock_resource_path = "app.account.models.DynamoResource"
    mock_uuid_path = "app.account.models.uuid"

    @mock.patch(mock_resource_path)
    @mock.patch(mock_uuid_path)
    def test_add_deposit(self, mock_uuid, mock_resource):
        newid = uuid.uuid4()
        mock_uuid.uuid4.return_value = str(newid)
        mock_resource_instance = mock_resource.return_value

        current_date = dt.datetime.now(dt.timezone.utc)

        transaction_id = Transaction.add("321", d.Decimal("54551"), current_date)

        self.assertEqual(transaction_id, str(newid), None)
        mock_resource_instance.add.assert_called_once_with(
            Transaction.table_name,
            {
                Transaction.hash_key: "321",
                Transaction.sort_key: str(newid),
                "created_at": current_date.isoformat(),
                "value": d.Decimal("54551"),
            },
        )

    @mock.patch(mock_resource_path)
    @mock.patch(mock_uuid_path)
    def test_add_withdraw(self, mock_uuid, mock_resource):
        newid = uuid.uuid4()
        mock_uuid.uuid4.return_value = str(newid)
        mock_resource_instance = mock_resource.return_value

        current_date = dt.datetime.now(dt.timezone.utc)

        transaction_id = Transaction.add("321", d.Decimal("-54551"), current_date)

        self.assertEqual(transaction_id, str(newid), None)
        mock_resource_instance.add.assert_called_once_with(
            Transaction.table_name,
            {
                Transaction.hash_key: "321",
                Transaction.sort_key: str(newid),
                "created_at": current_date.isoformat(),
                "value": d.Decimal("-54551"),
                "withdraw_date": current_date.strftime(date_format),
            },
        )

    @mock.patch(mock_resource_path)
    def test_find_withdraw_limit_available(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        table_resource_instance = mock_resource_instance.table_resource.return_value
        table_resource_instance.query.side_effect = (
            {"Items": [{"value": 1}, {"value": 3}], "LastEvaluatedKey": "33"},
            {"Items": [{"value": 5}]},
        )

        withdraw_transactions = Transaction.find_withdraw_limit_available("321")

        self.assertEqual(withdraw_transactions, 9)
        self.assertEqual(table_resource_instance.query.call_count, 2)

    @mock.patch(mock_resource_path)
    def test_find_withdraw_limit_available_throws_exception(self, mock_resource):
        mock_resource_instance = mock_resource.return_value
        table_resource_instance = mock_resource_instance.table_resource.return_value
        table_resource_instance.query.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InternalServerError",
                    "Message": "Everything fails dramatically! And you get sad!",
                }
            },
            "walking without looking",
        )

        Transaction.find_withdraw_limit_available("321")

        mock_resource_instance.handle_error.assert_called_once()
