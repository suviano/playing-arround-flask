import pytest

from src.account import wsgi


@pytest.fixture
def application():
    application = wsgi.create_app()
    with application.app_context():
        yield application


@pytest.fixture
def client(request, application):
    request.cls.client = application.test_client()
