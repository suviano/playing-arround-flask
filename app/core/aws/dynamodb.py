import logging
import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key
import botocore


class DynamoResource:
    def __init__(self):
        localstack = os.environ["LOCALSTACK"]
        kwargs = {}
        if localstack:
            kwargs.update(
                {
                    "use_ssl": False,
                    "verify": False,
                    "endpoint_url": "http://localhost:4566",
                }
            )
        self.resource = boto3.resource("dynamodb", **kwargs)

    @classmethod
    def error_help_strings(cls, error_code):
        # Got this map from the NoSQL Workbench from aws (Shame it's not in already in the library)
        # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html
        return {
            "InternalServerError": "Internal Server Error, generally safe to retry with exponential back-off",
            "ProvisionedThroughputExceededException": (
                "Request rate is too high. If you're using a custom retry strategy "
                "make sure to retry with exponential back-off."
                "Otherwise consider reducing frequency of requests or increasing "
                "provisioned capacity for your table or secondary index"
            ),
            "ResourceNotFoundException": "One of the tables was not found, verify table exists before retrying",
            "ServiceUnavailable": "Had trouble reaching DynamoDB. generally safe to retry with "
            "exponential back-off",
            "ThrottlingException": "Request denied due to throttling, generally safe to retry with "
            "exponential back-off",
            "UnrecognizedClientException": "The request signature is incorrect most likely due to an invalid "
            "AWS access key ID or secret key, fix before retrying",
            "ValidationException": "The input fails to satisfy the constraints specified by DynamoDB"
            ", fix input before retrying",
            "RequestLimitExceeded": "Throughput exceeds the current throughput limit for your account"
            ", increase account level throughput before retrying",
        }[error_code]

    def handle_error(self, error):
        error_code = error.response["Error"]["Code"]
        error_message = error.response["Error"]["Message"]
        error_help_string = self.error_help_strings(error_code)
        logging.error(
            "[{error_code}] {help_string}. Error message: {error_message}".format(
                error_code=error_code,
                help_string=error_help_string,
                error_message=error_message,
            )
        )
        env_name = os.environ["FLASK_ENV"]
        if env_name == "development":
            raise error
        raise Exception()

    def save_new(self, table_name: str, data: dict, primary_key: str = "id"):
        table = self.resource.Table(table_name)
        if not data.get(primary_key):
            resource_id = str(uuid.uuid4())
            data[primary_key] = resource_id
        else:
            resource_id = data[primary_key]

        try:
            table.put_item(Item=data)
        except botocore.exceptions.ClientError as error:
            self.handle_error(error)
        return resource_id

    def find_by_id(self, table_name: str, keys: dict):
        table = self.resource.Table(table_name)

        hash_expression = Key(keys["hash_key"]).eq(keys["hash_value"])
        sort_key = keys.get("sort_key")
        keys_expression = hash_expression
        if sort_key:
            sort_expression = Key(sort_key).eq(keys["sort_value"])
            keys_expression = hash_expression & sort_expression

        try:
            return table.query(KeyConditionExpression=keys_expression)
        except botocore.exceptions.ClientError as error:
            self.handle_error(error)

    def find_one_by_id(self, table_name: str, keys: dict):
        resp = self.find_by_id(table_name, keys)
        # raise if found more than one
        return resp["Items"][0] if resp["Items"] else None

    def update_item(self, table_name: str, keys: dict, values: dict):
        table = self.resource.Table(table_name)
        table.update_item(Key=Key)
