# Account management

The project needs python 3.7+, virtualenv packages, docker and docker-compose (you can translate the localstack-infra.yml to a docker start if you don't want to run this way).

Flask is being used as the server framework.
Marhsmallow to serialize the input and output from the rest.
The database used was `dynamodb` (I was going to use postgres with sqlalchemy, but I saw you guys use a lot of thing from aws).

## Structure

The structure is in some ways inspired by django-rest, focusing mainly on being simple.

Each main resource has its folder and inside is as follows:
* models holds the queries and some business rules
* views has the route controllers and things used in the parsers
* serializers
* core some generic things used globally

The project has 3 tables `account` , `transaction` and `person` was planning to deploy the databases as a stack of cloudformation, but didn't work.

The transaction table has 2 additional indexes to accomplish the operations


For the project code control the lint, tests and formatter (and other things) are configured in `setup.cfg`

* flake8 used for lint
* `black` and `isort` for the formatter

---

## cmd execution (running everything locally)

### dynamodb

To start dynamodb install docker(do that thing to run without sudo) and docker-compose
1. Run `docker-compose -f localstack-infra.yml -d`
2. Run `docker-compose -f localstack-infra.yml logs -f` the message `aws-local-infra    | Ready.` should appear.

Later will be told how to create the database structures.
The volumes of the container are persistent and stored in `data`

> DISCLAIMER Amazon QLDB  should be better for a real application
> Also a version with postgresql may be more simple, and sqlalchemy is great

<!-- 3. TODO use the file cloudformation file `Account_cf_template.json` to created the database and indexes

> aws --endpoint-url=http://localhost:4566 cloudformation deploy --template-file Account_cf_template.json --stack-name  -->

1. Create a virtualenv and start it `virtualenv -p python3 venv` and activate it `source venv/bin/activate`
2. install de dependencies `pip install -r requirements.dev.txt`
3. To run on localhost new need some environment variables

```
FLASK_APP=app.wsgi.py
FLASK_ENV=development
CORS_ON=true
LOCALSTACK=1
```

4. After defining the variables just run `flask run` it will start the server in the post 5000

> I added the folder sample.vscode with configuration files to run and debug using vscode. The project also need python plugin from microsoft to run

## Run tests

Just run `pytest --cov-report html --cov-report term --cov app` omit the arguments just to run the tests without coverage

> **DISCLAIMER**: don't put these arguments on setup.cfg will make the debug not work on vscode for some reason, and also slows down the execution a bit 

## Creating the database structure with graphical interface

> It's being done that way because I failed to make it work with the cloudformation before the agreed day

To create the database structure you can download the [NoSQL Workbench(from aws)](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html) import the cloudformation file `Account_cf_template.json` and commit the changes to the dynamodb.

The port to connect in the dynamodb running on localstack is 4566
