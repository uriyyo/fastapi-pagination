import os
import sqlite3

import pytest
from django import setup
from django.conf import settings
from django.db import models

from fastapi_pagination.ext.django import paginate
from tests.base import BasePaginationTestSuite

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


class TestDjango(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db, user_cls, query):
        @builder.both.default
        def route():
            return paginate(query)

        return builder.build()
