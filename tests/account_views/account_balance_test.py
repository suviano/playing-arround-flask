import unittest
from http import HTTPStatus
from unittest import mock

import pytest


@pytest.mark.usefixtures("client")
class TestAccountBalanceScenarios(unittest.TestCase):
    mock_models_path = "src.account.account.views.models"

    request_path = "/v1/account/{}/balance"

    @mock.patch("src.account.account.views.models")
    def test_balance_account_not_found(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = None
        resp = self.client.get(self.request_path.format("3333"))

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(resp.json, {"error": "Account not found"})

    @mock.patch("src.account.account.views.models")
    def test_balance_withdraw_limit_positive(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {
            "daily_withdraw_limit": 33,
            "balance": "44.554554",
            "blocked": False,
        }
        mock_models.Transaction.find_withdraw_limit_available.return_value = 2
        resp = self.client.get(self.request_path.format("3333"))

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(
            resp.json,
            {
                "bloqueado": False,
                "limiteSaqueDisponivel": 31,
                "saldo": 44.554554,
            },
        )

    @mock.patch("src.account.account.views.models")
    def test_balance_withdraw_limit_reached(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {
            "daily_withdraw_limit": 400,
            "balance": "44.554554",
            "blocked": False,
        }
        mock_models.Transaction.find_withdraw_limit_available.return_value = (
            400
        )
        resp = self.client.get(self.request_path.format("3333"))

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(
            resp.json,
            {
                "bloqueado": False,
                "limiteSaqueDisponivel": 0,
                "saldo": 44.554554,
            },
        )

    @mock.patch("src.account.account.views.models")
    def test_balance_withdraw_limit_reached_and_surpassed(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {
            "daily_withdraw_limit": 400,
            "balance": "44.554554",
            "blocked": False,
        }
        mock_models.Transaction.find_withdraw_limit_available.return_value = (
            500
        )
        resp = self.client.get(self.request_path.format("3333"))

        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(
            resp.json,
            {
                "bloqueado": False,
                "limiteSaqueDisponivel": 0,
                "saldo": 44.554554,
            },
        )
