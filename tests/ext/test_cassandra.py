import pytest
from cassandra.cqlengine import columns, connection, management, models

from fastapi_pagination.cursor import CursorPage as BaseCursorPage
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from fastapi_pagination.ext.cassandra import paginate
from tests.base import BasePaginationTestSuite, SuiteBuilder

CursorPage = CustomizedPage[
    BaseCursorPage,
    UseParamsFields(str_cursor=False),
]


class User(models.Model):
    __keyspace__ = "ks"

    group = columns.Text(partition_key=True)
    id = columns.Integer(primary_key=True)
    name = columns.Text()


@pytest.fixture(scope="session", autouse=True)
def _setup_cassandra(cassandra_session, raw_data):
    connection.register_connection("cluster1", session=cassandra_session, default=True)
    management.sync_table(model=User, keyspaces=("ks",))

    users = [User(group="GC", id=user.get("id"), name=user.get("name")) for user in raw_data]
    for user in users:
        user.save()


class TestCasandra(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def builder(self) -> SuiteBuilder:
        return SuiteBuilder.with_classes(cursor=CursorPage)

    @pytest.fixture(scope="session")
    def app(self, builder):
        @builder.cursor.default
        def route():
            return paginate(
                User.objects().order_by("id").allow_filtering(),
                query_filter={"group": "GC"},
            )

        return builder.build()
