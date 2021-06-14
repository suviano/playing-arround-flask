import unittest
import pytest
from http import HTTPStatus
from unittest import mock


@pytest.mark.usefixtures("client")
class TestAccountDepositScenarios(unittest.TestCase):
    mock_models_path = "app.account.views.models"

    request_path = "/account/{}/deposit"

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

    @mock.patch(mock_models_path)
    def test_depositing_negative_value(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {"blocked": False}
        resp = self.client.post(
            self.request_path.format("3333"),
            json={"valor": -333},
        )

        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(
            resp.json, {"error": "Depósito aceita penas valores positivos"}
        )

    @mock.patch(mock_models_path)
    def test_depositing_zero_value(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {"blocked": False}
        resp = self.client.post(
            self.request_path.format("3333"),
            json={"valor": 0},
        )

        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(
            resp.json, {"error": "Depósito aceita penas valores positivos"}
        )

    @mock.patch(mock_models_path)
    def test_depositing_returns_resource_location(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = {"blocked": False}
        mock_models.Account.deposit_into.return_value = "now"
        mock_models.Transaction.add.return_value = "123"
        resp = self.client.post(
            self.request_path.format("3333"),
            json={"valor": 44},
        )

        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        self.assertTrue("Content-Location" in resp.headers)
        self.assertEqual(
            resp.headers["Content-Location"],
            "/account/3333/transaction/123",
        )
        mock_models.Account.deposit_into.assert_called_once_with("3333", 44)
        mock_models.Transaction.add.assert_called_once_with("3333", 44, "now")

    @mock.patch(mock_models_path)
    def test_depositing_account_not_found(self, mock_models):
        mock_models.Account.find_one_by_id.return_value = None
        resp = self.client.post(
            self.request_path.format("3333"),
            json={
                "valor": 3323.44551,
            },
        )

        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(resp.json, {"error": "Account not found"})
