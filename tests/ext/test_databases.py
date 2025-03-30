import pytest
from databases import Database

from fastapi_pagination.ext.databases import apaginate
from tests.base import BasePaginationTestSuite

from .utils import sqlalchemy20


@pytest.fixture(scope="session")
def db(database_url):
    return Database(database_url)


@sqlalchemy20
class TestDatabases(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db, sa_user):
        builder.lifespan(db)

        @builder.both.default
        async def route():
            return await apaginate(db, sa_user.__table__.select())

        return builder.build()
