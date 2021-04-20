import os
import sqlite3

from django import setup
from django.conf import settings
from django.db import connection, models
from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.django import paginate

from ..base import BasePaginationTestCase, SafeTestClient, UserOut
from ..utils import faker

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "True"


@fixture(scope="session")
def database_url(sqlite_url) -> str:
    *_, dbname = sqlite_url.split("/")
    return dbname


@fixture(scope="session")
def db(database_url):
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": database_url,
            }
        },
        INSTALLED_APPS=[],
    )
    setup()

    sqlite3.connect(database_url)


@fixture(scope="session")
def User(db):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.TextField()

        class Meta:
            app_label = "test"

    # TODO: find better way to create table
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS test_user;")
        cursor.execute("CREATE TABLE test_user (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL);")
        cursor.fetchall()

    return User


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
def app(db, User, query):
    app = FastAPI()

    @app.on_event("startup")
    def on_startup() -> None:
        for _ in range(100):
            User.objects.create(name=faker.name())

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    def route():
        return paginate(query)

    add_pagination(app)
    return app


class TestDjango(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    def entities(self, User, query):
        return [*User.objects.all()]
