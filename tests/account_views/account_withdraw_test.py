import decimal as d
import unittest
from http import HTTPStatus
from unittest import mock

import pytest


@pytest.mark.usefixtures("client")
class TestAccountWithdrawScenarios(unittest.TestCase):
    mock_models_path = "src.account.account.views.models"

    request_path = "/v1/account/{}/withdraw"

    @mock.patch(mock_models_path)
    def test_account_not_found(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = None
        resp = self.client.post(
            self.request_path.format("3333"),
            json={
                "valor": 3323.44551,
            },
        )

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(resp.json, {"error": "Account not found"})

    @mock.patch(mock_models_path)
    def test_account_blocked(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {"blocked": True}
        resp = self.client.post(
            self.request_path.format("3333"),
            json={
                "valor": "3323.44551",
            },
        )

        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)

    @mock.patch("src.account.account.views.models")
    def test_withdraw_bigger_than_balance(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {
            "balance": 33,
            "blocked": False,
        }
        resp = self.client.post(
            self.request_path.format("3333"), json={"valor": "3551.332"}
        )

        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)
        self.assertDictEqual(
            resp.json,
            {"error": "withdrawa value greater than available in the account"},
        )

    @mock.patch("src.account.account.views.models")
    def test_single_withdraw_bigger_than_daily_limit(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {
            "balance": 100,
            "blocked": False,
            "daily_withdraw_limit": 55,
        }
        mock_models.Transaction.find_withdraw_limit_available.return_value = 55
        resp = self.client.post(
            self.request_path.format("3333"), json={"valor": "56"}
        )

        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)
        self.assertDictEqual(
            resp.json,
            {
                "error": "It is not possible to carry out the withdraw. Limit reached."
            },
        )

    @mock.patch("src.account.account.views.models")
    def test_withdraw_smaller_than_daily_but_smaller_than_available(
        self, mock_models
    ):
        mock_models.Account.find_one_by_id.return_value = {
            "balance": 100,
            "blocked": False,
            "daily_withdraw_limit": 55,
        }
        mock_models.Transaction.find_withdraw_limit_available.return_value = 33
        resp = self.client.post(
            self.request_path.format("3333"), json={"valor": "54"}
        )

        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)
        self.assertDictEqual(
            resp.json,
            {
                "error": "It is not possible to carry out the withdraw. Withdraw available is R$ 22"
            },
        )

    @mock.patch("src.account.account.views.models")
    def test_withdraw_executed_success_fully(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {
            "balance": 100,
            "blocked": False,
            "daily_withdraw_limit": 55,
        }
        mock_models.Transaction.find_withdraw_limit_available.return_value = 2
        mock_models.Account.withdraw.return_value = "now"
        mock_models.Transaction.add.return_value = "123"
        resp = self.client.post(
            self.request_path.format("3333"), json={"valor": "10"}
        )

        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        self.assertTrue("Content-Location" in resp.headers)
        self.assertEqual(
            resp.headers["Content-Location"],
            "/account/3333/transaction/123",
        )

        mock_models.Transaction.find_withdraw_limit_available.assert_called_once_with(
            "3333"
        )
        mock_models.Account.withdraw.assert_called_once_with(
            "3333", d.Decimal(10)
        )
        mock_models.Transaction.add.assert_called_once_with(
            "3333", d.Decimal(-10), "now"
        )
