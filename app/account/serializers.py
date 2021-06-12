import marshmallow as ma


class CreateAccountSchema(ma.Schema):
    balance = ma.fields.Decimal(required=True, data_key="saldo")
    active = ma.fields.Bool(required=True, data_key="flagAtivo")
    withdraw_limit = ma.fields.Decimal(required=True, data_key="limiteSaqueDiario")
    account_type = ma.fields.Integer(required=True, data_key="tipoConta")
    person_id = ma.fields.Int(data_key="idPessoa")
    name = ma.fields.Str(data_key="nome")
    cpf = ma.fields.Str()
    birth_date = ma.fields.Date(data_key="dataNascimento")
