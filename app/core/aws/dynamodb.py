import logging
import os

import boto3
import botocore
from boto3.dynamodb.conditions import Key
from flask import abort


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
        self.client = boto3.client("dynamodb", **kwargs)

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

    def table_resource(self, table_name):
        return self.resource.Table(table_name)

    def add(self, table_name: str, data: dict):
        table = self.resource.Table(table_name)
        try:
            table.put_item(Item=data)
        except botocore.exceptions.ClientError as error:
            self.handle_error(error)

    def __handle_key_expression(self, keys_map: dict):
        hash_expression = Key(keys_map["hash_key"]).eq(keys_map["hash_value"])
        sort_key = keys_map.get("sort_key")
        keys_expression = hash_expression
        if sort_key:
            sort_expression = Key(sort_key).eq(keys_map["sort_value"])
            keys_expression = hash_expression & sort_expression
        return keys_expression

    def find_by_id(self, table_name: str, keys: dict):
        table = self.resource.Table(table_name)

        keys_expression = self.__handle_key_expression(keys)
        try:
            return table.query(KeyConditionExpression=keys_expression)
        except botocore.exceptions.ClientError as error:
            self.handle_error(error)

    def find_one_by_id(self, table_name: str, keys: dict):
        resp = self.find_by_id(table_name, keys)
        # raise exception if found more than one
        return resp["Items"][0] if resp["Items"] else None

    def update_item(
        self,
        table_name: str,
        keys: dict,
        update_expression: str,
        expression_attr_name,
        expression_attr_value,
    ):
        table = self.resource.Table(table_name)
        try:
            table.update_item(
                Key=keys,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attr_name,
                ExpressionAttributeValues=expression_attr_value,
                ReturnValues="UPDATED_NEW",
            )
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "ValidationException":
                abort(500)
