import pytest
from cassandra.cluster import Cluster
from cassandra.cqlengine import columns, connection, models

from fastapi_pagination.cursor import CursorPage as BaseCursorPage
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal, UseParamsFields
from fastapi_pagination.ext.cassandra import paginate
from tests.base import BasePaginationTestSuite, SuiteBuilder

CursorPage = CustomizedPage[
    BaseCursorPage,
    UseParamsFields(str_cursor=False),
    UseIncludeTotal(False),
]


class User(models.Model):
    __keyspace__ = "ks"

    group = columns.Text(partition_key=True)
    id = columns.Integer(primary_key=True)
    name = columns.Text()


@pytest.fixture(scope="session")
def cassandra_session(cassandra_address):
    with Cluster([cassandra_address]).connect() as session:
        connection.register_connection("cassandra-test", session=session, default=True)
        yield session
        connection.unregister_connection("cassandra-test")


@pytest.mark.usefixtures("cassandra_session")
class TestCasandra(BasePaginationTestSuite):
    include_total = False

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
