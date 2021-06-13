import unittest
import uuid
from unittest import mock

from botocore.exceptions import ClientError

from app.core.aws.dynamodb import DynamoResource


class TestDynamodbResource(unittest.TestCase):
    mock_path = "app.core.aws.dynamodb"

    @mock.patch.dict(
        f"{mock_path}.os.environ", {"LOCALSTACK": "1", "FLASK_ENV": "development"}
    )
    @mock.patch(f"{mock_path}.boto3")
    @mock.patch(f"{mock_path}.uuid")
    def test_save_new_generate_uuid(self, uuid_mock, boto3_mock):
        expected_uuid = uuid.uuid4()
        uuid_mock.uuid4.return_value = expected_uuid
        resource_mock = boto3_mock.resource.return_value
        table_mock = resource_mock.Table.return_value

        table_name = "test-table"
        item_id = DynamoResource().save_new(
            table_name, {"just": "push the lets to see if will swing a bit"}
        )

        uuid_mock.uuid4.assert_called_once()
        self.assertEqual(str(expected_uuid), item_id)

        resource_mock.Table.assert_called_once_with(table_name)
        table_mock.put_item.assert_called_once_with(
            Item={
                "just": "push the lets to see if will swing a bit",
                "id": str(expected_uuid),
            }
        )

    @mock.patch.dict(
        f"{mock_path}.os.environ", {"LOCALSTACK": "1", "FLASK_ENV": "development"}
    )
    @mock.patch(f"{mock_path}.boto3")
    @mock.patch(f"{mock_path}.uuid")
    def test_save_new_id_predefined(self, uuid_mock, boto3_mock):
        resource_mock = boto3_mock.resource.return_value
        table_mock = resource_mock.Table.return_value

        table_name = "test-table"
        save_data = {"just": "push the lets to see if will swing a bit", "id": "test"}
        item_id = DynamoResource().save_new(
            table_name,
            {**save_data},
        )

        uuid_mock.uuid4.assert_not_called()
        self.assertEqual("test", item_id)

        resource_mock.Table.assert_called_once_with(table_name)
        table_mock.put_item.assert_called_once_with(Item={**save_data})

    @mock.patch(f"{mock_path}.logging")
    @mock.patch.dict(
        f"{mock_path}.os.environ", {"LOCALSTACK": "1", "FLASK_ENV": "development"}
    )
    @mock.patch(f"{mock_path}.boto3")
    def test_save_new_handle_error_properly(self, boto3_mock, logging_mock):
        resource_mock = boto3_mock.resource.return_value
        table_mock = resource_mock.Table.return_value
        table_mock.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InternalServerError",
                    "Message": "Everything fails dramatically! And you get sad!",
                }
            },
            "walking without looking",
        )

        save_data = {"just": "push the lets to see if will swing a bit", "id": "test"}
        with self.assertRaises(ClientError):
            DynamoResource().save_new(
                "test-table",
                {**save_data},
            )

        logging_mock.error.assert_called_once()
        table_mock.put_item.assert_called_once_with(Item={**save_data})

    @mock.patch(f"{mock_path}.logging")
    @mock.patch.dict(
        f"{mock_path}.os.environ", {"LOCALSTACK": "", "FLASK_ENV": "production"}
    )
    @mock.patch(f"{mock_path}.boto3")
    def test_save_new_handle_error_properly_not_in_local_environment(
        self, boto3_mock, logging_mock
    ):
        resource_mock = boto3_mock.resource.return_value
        table_mock = resource_mock.Table.return_value
        table_mock.put_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InternalServerError",
                    "Message": "Everything fails dramatically! And you get sad!",
                }
            },
            "walking without looking",
        )

        save_data = {"just": "push the lets to see if will swing a bit", "id": "test"}
        with self.assertRaises(Exception):
            DynamoResource().save_new(
                "test-table",
                {**save_data},
            )

        logging_mock.error.assert_called_once()
        table_mock.put_item.assert_called_once_with(Item={**save_data})
