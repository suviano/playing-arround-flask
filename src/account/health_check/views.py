from dataclasses import asdict
from http import HTTPStatus

from flask import Blueprint

from src.account.health_check.serializers import Check, HealthCheck

bp = Blueprint("health-check", __name__)


@bp.route("", methods=["GET"])
def get_health_check():
    # TODO verify database status
    return asdict(
        HealthCheck(status="UP", uptime=1, checks=Check(database="UP"))
    ), HTTPStatus.OK
