from fastapi.testclient import TestClient
from pytest import fixture


@fixture
def client(app):
    with TestClient(app) as c:
        yield c
