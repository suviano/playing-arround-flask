from http import HTTPStatus

from flask import Blueprint
from marshmallow.exceptions import ValidationError

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(ValidationError)
def handle_error(error):
    return {"error": error.messages}, HTTPStatus.BAD_REQUEST
