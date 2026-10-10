import sqlite3
from contextlib import closing

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.bases import RawParams
from fastapi_pagination.ext.raw_sql import create_count_query_from_text, create_paginate_query_from_text
from fastapi_pagination.ext.sqlalchemy import paginate

QUERY = "SELECT id FROM items ORDER BY id"


@pytest.fixture
def connection():
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE items (id INTEGER)")
        conn.executemany("INSERT INTO items VALUES (?)", [(i,) for i in range(7)])
        conn.commit()
        yield conn


@pytest.mark.parametrize(
    "query",
    [
        QUERY,
        f"{QUERY} -- newest first",
        f"{QUERY}\r\n-- newest first",
        f"{QUERY} -- comment ending with ;",
        f"{QUERY};",
        f"{QUERY}; \n\t",
        "SELECT id FROM items WHERE '; --' = '; --' ORDER BY id",
        f"{QUERY} /* newest first */",
    ],
)
class TestRawSQL:
    @pytest.mark.parametrize(
        ("params", "expected"),
        [
            (RawParams(limit=2, offset=1), [(1,), (2,)]),
            (RawParams(limit=2, offset=0), [(0,), (1,)]),
            (RawParams(), [(i,) for i in range(7)]),
        ],
    )
    def test_page(self, connection, query, params, expected):
        result = connection.execute(create_paginate_query_from_text(query, params)).fetchall()

        assert result == expected

    def test_count(self, connection, query):
        result = connection.execute(create_count_query_from_text(query)).fetchone()

        assert result == (7,)

    def test_sqlalchemy_text(self, connection, query):
        engine = create_engine("sqlite://", creator=lambda: connection)
        try:
            with closing(Session(engine)) as session, set_page(Page[int]):
                page = paginate(session, text(query), params=Params(page=2, size=2), unwrap_mode="unwrap")
        finally:
            engine.dispose()

        assert page.items == [2, 3]
        assert page.total == 7
        assert page.pages == 4
