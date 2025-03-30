import databases
import pytest
import sqlalchemy
from ormar import Integer, Model, OrmarConfig, String
from sqlalchemy.engine.create import create_engine

from fastapi_pagination.ext.ormar import apaginate
from tests.base import BasePaginationTestSuite


@pytest.fixture(scope="session")
def db(database_url):
    return databases.Database(database_url)


@pytest.fixture(scope="session")
def meta(database_url):
    return sqlalchemy.MetaData()


@pytest.fixture(scope="session")
def engine(database_url):
    return create_engine(database_url)


@pytest.fixture(scope="session")
def user_cls(meta, db, engine):
    class User(Model):
        ormar_config = OrmarConfig(
            metadata=meta,
            database=db,
            engine=engine,
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
