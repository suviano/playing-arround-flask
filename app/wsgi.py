from flask import Flask


from app.account.views import bp as account

app = Flask("account management")
app.register_blueprint(account, url_prefix='/account')
