from fastapi import FastAPI
from mongoengine import connect, Document, fields
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.mongoengine import paginate

from ..base import BasePaginationTestCase
from ..utils import faker


@fixture(scope="session")
def database_url(mongodb_url):
    return mongodb_url


@fixture(scope="session")
def db_connect(database_url):
    connect(host=database_url)


@fixture(scope="session")
def User(db_connect):
    class User(Document):
        name = fields.StringField()

    return User


@fixture(scope="session", autouse=True)
def clear_database(User):
    User.drop_collection()
    yield
    User.drop_collection()


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, User):
    if request.param:
        return User
    else:
        return User.objects.all()


@fixture(scope="session")
def app(db_connect, User, query, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route():
        return paginate(query)

    return add_pagination(app)


class TestMongoEngine(BasePaginationTestCase):
    @fixture(scope="class")
    def entities(self, User, query):
        User.objects.insert([User(name=faker.name()) for _ in range(100)])

        return list(User.objects.all())
