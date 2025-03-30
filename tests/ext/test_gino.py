import pytest
from gino_starlette import Gino
from sqlalchemy import Column, Integer, String

from fastapi_pagination.ext.gino import apaginate
from tests.base import BasePaginationTestSuite


@pytest.fixture(scope="session")
def db_type():
    return "postgres"


@pytest.fixture(scope="session")
def db(database_url):
    return Gino(dsn=database_url)


@pytest.fixture(scope="session")
def user_cls(db):
    class User(db.Model):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

    return User


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, user_cls):
    if request.param:
        return user_cls

    return user_cls.query


@pytest.mark.gino
class TestGino(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db, query):
        builder = builder.new()

        @builder.both.default
        async def route():
            return await apaginate(query)

        app = builder.build()
        db.init_app(app)

        return app
