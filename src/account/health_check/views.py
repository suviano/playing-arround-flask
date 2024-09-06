from http import HTTPStatus
from dataclasses import asdict

from flask import Blueprint

from src.account.health_check.serializers import HealthCheck, Check

bp = Blueprint("health-check", __name__)


@bp.route("", methods=["GET"])
def get_health_check():
    # TODO verify database status
    return asdict(
        HealthCheck(status="UP", uptime=1, checks=Check(database="UP"))
    ), HTTPStatus.OK
