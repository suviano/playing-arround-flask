from flask import Flask


from app.account.views import bp as account


def create_app():
    app = Flask("account management")
    app.register_blueprint(account, url_prefix="/account")

    return app
