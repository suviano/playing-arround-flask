import datetime as dt
import decimal as d

from app.core.aws.dynamodb import DynamoResource


class Account:
    table_name = "account"

    @classmethod
    def save(
        cls,
        person_id: str,
        balance: d.Decimal,
        daily_withdraw_limit: d.Decimal,
        active: bool,
        account_type: int,
    ):
        payload = {
            "person_id": person_id,
            "created_at": dt.datetime.now().isoformat(),
            "person_id": person_id,
            "balance": balance,
            "blocked": False,
            "daily_withdraw_limit": daily_withdraw_limit,
            "active": active,
            "account_type": account_type,
        }
        return DynamoResource().save_new(cls.table_name, payload)


class Person:
    """
    Not a column of account with the excuse that a person my have multiple accounts
    """

    table_name = "person"

    @classmethod
    def save(cls, name: str, cpf: str, birth: dt.date):
        payload = {
            "name": name,
            "cpf": cpf,
            "birth": str(birth),
        }
        return DynamoResource().save_new(cls.table_name, payload)
