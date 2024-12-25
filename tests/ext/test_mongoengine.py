import pytest
from mongoengine import Document, connect, fields

from fastapi_pagination.ext.mongoengine import paginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_connect(database_url):
    connect(host=database_url)


@pytest.fixture(scope="session")
def user(db_connect):
    class User(Document):
        name = fields.StringField()

        meta = {
            "collection": "users",
            "strict": False,
            "id_field": "id",
        }

    return User


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, user):
    if request.param:
        return user

    return user.objects.all()


@mongodb_test
class TestMongoEngine(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db_connect, query):
        @builder.both.default
        def route():
            return paginate(query)

        return builder.build()
