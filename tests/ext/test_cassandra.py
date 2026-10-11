from unittest.mock import MagicMock

import pytest
from cassandra.cluster import Cluster
from cassandra.cqlengine import columns, connection, models

from fastapi_pagination.cursor import CursorPage as BaseCursorPage
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal, UseParamsFields
from fastapi_pagination.ext import cassandra as cassandra_ext
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


@pytest.mark.skip
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


def test_paginate_does_not_mutate_additional_data(monkeypatch):
    cursor = MagicMock(current_rows=[{"id": 1}], paging_state=b"next")
    monkeypatch.setattr(
        connection, "get_connection", lambda: MagicMock(session=MagicMock(execute=lambda *a, **kw: cursor))
    )
    captured = {}
    monkeypatch.setattr(cassandra_ext, "create_page", lambda items, **kwargs: captured.update(kwargs))

    additional_data = {"x": 1}
    cassandra_ext.paginate(
        MagicMock(), params=CursorPage.__params_type__(size=10), additional_data=lambda items: additional_data
    )

    assert captured["next_"] == b"next"
    assert additional_data == {"x": 1}
