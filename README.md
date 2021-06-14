# Gestao de contas

The project need python 3.7+, virtualenv packages, docker and docker-compose (you can translate the localstack-infra.yml to a docker start if you don't want to run this way).

Flask is being used as the server framework.
Marhsmallow to serialize the inputs from the rest.
The database used was `dynamodb` (I was going to use postgres with sqlalchemy, but I saw you guys use alot of thing from aws).

For the project code control the lint, tests and formatter (and other things) are configured in `setup.cfg`

* flake8 used for lint
* `black` and `isort` for the formatter

## cmd execution (running everything locally)

To start dynamodb install docker(do that thing to run without sudo) and docker-compose
1. Run `docker-compose -f localstack-infra.yml -d`
2. Run `docker-compose -f localstack-infra.yml logs -f` the message `aws-local-infra    | Ready.` should appear.
3. TODO use the file cloudformation file `Account_cf_template.json` to created the database and indexes

> TODO `aws --endpoint-override=http://localhost:4566 cloudformation ??? Account_cf_template.json`

1. Create a virtualenv and start it `virtualenv -p python3 venv` and activate it `source venv/bin/activate`
2. install de dependencies `pip install -r requirements.dev.txt`
3. To run on localmode new need some environment variables

```
FLASK_APP=app.wsgi.py
FLASK_ENV=development
CORS_ON=true
LOCALSTACK=1
```

4. After defining the variables just run `flask run --host 0.0.0.0` it will start the server in the post 5000

> I am using the project in the vscode with the python plugin from microsoft

> DISCLAIMER Amazon QLDB  should be better for a real application
> Also a version with postgresql may be more simple, and sqlalchemy is great

## Run tests

Just run `pytest --cov-report html --cov-report term --cov app` omit the arguments just to run the tests without coverage

> **DISCLAIMER**: don't put these arguments on setup.cfg will make the debug not work on vscode for some reason, and also slows down the execution a bit 
