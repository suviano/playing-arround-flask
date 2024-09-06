from dataclasses import dataclass
from typing import Literal

Status = Literal["UP", "DOWN"]


@dataclass
class Check:
    database: Status


@dataclass
class HealthCheck:
    status: Status
    uptime: int
    checks: Check
