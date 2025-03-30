import pytest
from databases import Database, __version__
from orm import Integer, Model, ModelRegistry, String

from fastapi_pagination.ext.orm import apaginate
from tests.base import BasePaginationTestSuite

if tuple(map(int, __version__.split("."))) >= (0, 9, 0):  # noqa: RUF048
    raise ImportError("This test is only for databases<0.9.0")


@pytest.fixture(scope="session")
def db(database_url):
    return Database(database_url)


@pytest.fixture(scope="session")
def user(db):
    models = ModelRegistry(database=db)

    class User(Model):
        tablename = "users"
        registry = models
        fields = {
            "id": Integer(primary_key=True),
            "name": String(max_length=100),
        }

    return User


@pytest.mark.orm
class TestORM(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db, user):
        builder.lifespan(db)

        @builder.both.default
        async def route():
            return await apaginate(user.objects)

        return builder.build()
