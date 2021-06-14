from flask import Flask

from app.account.views import bp as account
from app.core.hooks import errors


def create_app():
    app = Flask("account management")
    app.register_blueprint(account, url_prefix="/account")
    app.register_blueprint(errors)

    return app
