import unittest
from http import HTTPStatus
from unittest import mock

import pytest


@pytest.mark.usefixtures("client")
class TestAccountBlockScenarios(unittest.TestCase):
    mock_models_path = "src.account.account.views.models"

    request_path = "/v1/account/{}/block"

    @mock.patch("src.account.account.views.models")
    def test_param_received_by_models(self, mock_models):
        mock_models.Account.block.return_value = None
        resp = self.client.patch(
            self.request_path.format("3333"), json={"bloquear": True}
        )

        self.assertEqual(resp.status_code, HTTPStatus.NO_CONTENT)
        mock_models.Account.block.assert_called_once_with("3333", True)
