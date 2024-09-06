from dotenv import load_dotenv
from flask import Flask

from src.account.account.views import bp as account
from src.account.health_check.views import bp as health_check
from src.account.core.hooks import errors

load_dotenv()


def create_app():
    app = Flask("account management")
    app.register_blueprint(account, url_prefix="/v1/account")
    app.register_blueprint(health_check, url_prefix="/v1/health-check")
    app.register_blueprint(errors)

    return app
