import os
import sqlite3

from django import setup
from django.conf import settings
from django.db import models
from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.django import paginate

from ..base import BasePaginationTestCase

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
            db_table = "users"

    return User


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, User):
    if request.param:
        return User

    return User.objects.all()


@fixture(scope="session")
def app(db, User, query, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route():
        return paginate(query)

    return add_pagination(app)


class TestDjango(BasePaginationTestCase):
    pass
