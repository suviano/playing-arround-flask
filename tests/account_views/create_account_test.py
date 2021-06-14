import unittest
import pytest
import decimal as d
import datetime as dt
from http import HTTPStatus
from unittest import mock


@pytest.mark.usefixtures("client")
class TestCreateAccountScenarios(unittest.TestCase):
    mock_models_path = "app.account.views.models"

    @mock.patch(mock_models_path)
    def test_not_call_create_person_when_id_informed(self, mock_models):
        mock_models.Person.add.return_value = "1"
        mock_models.Account.add.return_value = "2"

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
        mock_models.Person.add.assert_not_called()
        mock_models.Account.add.assert_called_once_with(
            **{
                "person_id": "665",
                "active": False,
                "account_type": 33,
                "daily_withdraw_limit": d.Decimal("444"),
                "balance": d.Decimal("3323.44551"),
            }
        )

    @mock.patch(mock_models_path)
    def test_must_call_create_person_when_id_not_exists(self, mock_models):
        mock_models.Person.add.return_value = "1"
        mock_models.Account.add.return_value = "2"

        resp = self.client.post(
            "/account",
            json={
                "saldo": 3323.44551,
                "flagAtivo": False,
                "limiteSaqueDiario": 444,
                "tipoConta": 33,
                "nome": "juaozin",
                "cpf": "113.874.497-29",
                "dataNascimento": "1900-04-04",
            },
        )

        self.assertEqual(resp.status_code, HTTPStatus.CREATED)
        self.assertEqual(resp.headers["Content-Location"], "/account/2")
        mock_models.Person.add.assert_called_once_with(
            **{
                "birth": dt.datetime(1900, 4, 4).date(),
                "cpf": "113.874.497-29",
                "name": "juaozin",
            }
        )
        mock_models.Account.add.assert_called_once_with(
            **{
                "person_id": "1",
                "active": False,
                "account_type": 33,
                "daily_withdraw_limit": d.Decimal("444"),
                "balance": d.Decimal("3323.44551"),
            }
        )

    @mock.patch(mock_models_path)
    def test_content_type_must_be_json(self, mock_models):
        resp = self.client.post(
            "/account", data=b"dasda", content_type="application/x-www-form-urlencoded"
        )
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(resp.json, {"error": "content-type must be application/json"})
        mock_models.Person.add.assert_not_called()
        mock_models.Account.add.assert_not_called()

    @mock.patch(mock_models_path)
    def test_problem_saving_the_account(self, mock_models):
        mock_models.Account.add.side_effect = Exception(
            "Someone dropped coffee in the machine now everything is broken because it is!"
        )
        resp = self.client.post(
            "/account",
            json={
                "saldo": 3323.44551,
                "flagAtivo": False,
                "limiteSaqueDiario": 444,
                "tipoConta": 33,
                "nome": "juaozin",
                "cpf": "113.874.497-29",
                "dataNascimento": "1900-04-04",
            },
        )
        self.assertEqual(resp.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.json, {"error": "Problem creating the account"})
