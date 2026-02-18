import pytest
import sqlalchemy
from ormar import DatabaseConnection, Integer, Model, OrmarConfig, String

from fastapi_pagination.ext.ormar import apaginate
from tests.base import BasePaginationTestSuite


@pytest.fixture(scope="session")
def is_async_db():
    return True


@pytest.fixture(scope="session")
def db(database_url):
    return DatabaseConnection(database_url)


@pytest.fixture(scope="session")
def meta(db_type):
    # Create separate metadata for each database type (postgres/sqlite)
    # The db_type parameter ensures pytest creates a distinct fixture instance per database
    return sqlalchemy.MetaData()


@pytest.fixture(scope="session")
def user_cls(meta, db):
    class User(Model):
        ormar_config = OrmarConfig(
            metadata=meta,
            database=db,
            tablename="users",
        )

        id: int = Integer(primary_key=True)
        name: str = String(max_length=100)

    return User


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, user_cls):
    if request.param:
        return user_cls

    return user_cls.objects


@pytest.mark.ormar
class TestOrmar(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db, meta, user_cls, query):
        builder.lifespan(db)

        @builder.both.default
        async def route():
            return await apaginate(query)

        return builder.build()
