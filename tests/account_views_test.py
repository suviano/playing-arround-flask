import unittest
import pytest
import decimal as d
from http import HTTPStatus
from unittest import mock


@pytest.mark.usefixtures("client")
class TestAccountScenarios(unittest.TestCase):
    mock_models_path = "app.account.views.models"

    @mock.patch(mock_models_path)
    def test_not_call_create_person_when_id_informed(self, mock_models):
        mock_models.Person.save.return_value = "1"
        mock_models.Account.save.return_value = "2"

        resp = self.client.post(
            "/account",
            json={
                "saldo": 3323.44551,
                "flagAtivo": False,
                "limiteSaqueDiario": 444,
                "tipoConta": 33,
                "idPessoa": "665",
            },
        )

        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        self.assertEqual(resp.headers["Content-Location"], "/account/2")
        mock_models.Person.save.assert_not_called()
        mock_models.Account.save.assert_called_once_with(
            **{
                "person_id": 665,
                "active": False,
                "account_type": 33,
                "daily_withdraw_limit": d.Decimal("444"),
                "balance": d.Decimal("3323.44551"),
            }
        )
