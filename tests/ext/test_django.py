import os
import sqlite3

import pytest
from django import setup
from django.conf import settings
from django.db import models
from fastapi import FastAPI

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.django import paginate
from tests.base import BasePaginationTestCase

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "True"


@pytest.fixture(scope="session")
def database_url(sqlite_url) -> str:
    *_, dbname = sqlite_url.split("/")
    return dbname


@pytest.fixture(scope="session")
def db(database_url):
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": database_url,
            },
        },
        INSTALLED_APPS=[],
    )
    setup()

    sqlite3.connect(database_url)


@pytest.fixture(scope="session")
def user_cls(db):
    class User(models.Model):
        id = models.IntegerField(primary_key=True)
        name = models.TextField()

        class Meta:
            app_label = "test"
            db_table = "users"

        def __str__(self):
            return self.name

    return User


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, user_cls):
    if request.param:
        return user_cls

    return user_cls.objects.all()


@pytest.fixture(scope="session")
def app(db, user_cls, query, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route():
        return paginate(query)

    return add_pagination(app)


class TestDjango(BasePaginationTestCase):
    pass
