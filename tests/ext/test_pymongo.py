from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import pytest
from bson import ObjectId
from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from fastapi import HTTPException
from pymongo import AsyncMongoClient, MongoClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import Page, Params, set_page, set_params
from fastapi_pagination.cursor import CursorParams
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal
from fastapi_pagination.ext.pymongo import apaginate, apaginate_aggregate, paginate, paginate_aggregate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import maybe_async

from .utils import mongodb_test


async def _replace(collection, documents) -> None:
    """Replace the collection's contents with ``documents``."""
    await maybe_async(collection.delete_many({}))
    if documents:
        await maybe_async(collection.insert_many(documents))


async def _paginate_all(paginate_func, collection, *, size, **kwargs) -> list[Any]:
    """Fetch every page forward via ``next_page`` and return the documents seen."""
    seen, cursor = [], None
    while True:
        page = await maybe_async(paginate_func(collection, params=CursorParams(size=size, cursor=cursor), **kwargs))
        seen.extend(page.items)
        cursor = page.next_page
        if cursor is None:
            return seen


@pytest.fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@async_sync_testsuite
class _BasePymongoSuite:
    @async_fixture(scope="session")
    async def db_client(self, database_url, is_async_db):
        if is_async_db:
            async with AsyncMongoClient(database_url) as client:
                yield client
        else:
            with MongoClient(database_url) as client:
                yield client


@mongodb_test
class TestPymongo(_BasePymongoSuite, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate if is_async_db else paginate

    @pytest.fixture(scope="session")
    def app(self, builder, db_client, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route():
            return await maybe_async(paginate_func(db_client.test.users))

        @builder.cursor.default
        async def cursor_route():
            return await maybe_async(paginate_func(db_client.test.users, sort=[("id", 1)]))

        return builder.build()

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_previous_links(self, db_client, paginate_func, entities):
        entities = sorted(entities, key=lambda entity: entity.id)
        size = 7

        pages, cursor = [], None
        while True:
            page = await maybe_async(
                paginate_func(
                    db_client.test.users,
                    params=CursorParams(size=size, cursor=cursor),
                    sort=[("id", 1)],
                )
            )
            pages.append(page)
            cursor = page.next_page
            if cursor is None:
                break

        assert pages[0].previous_page is None
        assert pages[-1].next_page is None
        assert [[item["id"] for item in page.items] for page in pages] == [
            [entity.id for entity in entities[i : i + size]] for i in range(0, len(entities), size)
        ]

        # Going back with previous_page returns the preceding pages, in order.
        for current, expected in zip(reversed(pages[1:]), reversed(pages[:-1]), strict=True):
            back = await maybe_async(
                paginate_func(
                    db_client.test.users,
                    params=CursorParams(size=size, cursor=current.previous_page),
                    sort=[("id", 1)],
                )
            )
            assert [item["id"] for item in back.items] == [item["id"] for item in expected.items]

    @async_fixture(scope="function")
    async def cursor_collection(self, db_client):
        collection = db_client.test[f"cursor_{uuid4().hex}"]
        yield collection
        await maybe_async(collection.drop())

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_descending(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"id": i} for i in range(10)])
        docs = await _paginate_all(paginate_func, cursor_collection, size=3, sort=[("id", -1)])
        assert [d["id"] for d in docs] == list(range(9, -1, -1))

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_breaks_ties_on_id(self, cursor_collection, paginate_func):
        # Every document shares one sort value, so the _id tiebreaker is the only
        # thing keeping the pagination stable and complete.
        await _replace(cursor_collection, [{"group": "x"} for _ in range(5)])
        docs = await _paginate_all(paginate_func, cursor_collection, size=2, sort=[("group", 1)])
        ids = [d["_id"] for d in docs]
        assert len(ids) == 5
        assert len(set(ids)) == 5
        assert ids == sorted(ids)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_handles_null_sort_values(self, cursor_collection, paginate_func):
        # Nulls sort first ascending; pagination must not stop at the null boundary.
        await _replace(cursor_collection, [{"n": None}, {"n": 1}, {"n": None}, {"n": 2}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", 1)])
        assert [d["n"] for d in docs] == [None, None, 1, 2]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_descending_handles_null_sort_values(self, cursor_collection, paginate_func):
        # Nulls sort last descending, so they are still reached after every value.
        await _replace(cursor_collection, [{"n": None}, {"n": 1}, {"n": 3}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", -1)])
        assert [d["n"] for d in docs] == [3, 1, None]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_handles_missing_sort_field(self, cursor_collection, paginate_func):
        # Missing fields sort as null.
        await _replace(cursor_collection, [{"n": 2}, {"other": True}, {"n": 1}, {"other": True}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", 1)])
        assert [d.get("n") for d in docs] == [None, None, 1, 2]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_supports_dotted_sort_field(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"meta": {"rank": i}} for i in range(5)])
        docs = await _paginate_all(paginate_func, cursor_collection, size=2, sort=[("meta.rank", 1)])
        assert [d["meta"]["rank"] for d in docs] == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_descending_dotted_sort_field(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"meta": {"rank": i}} for i in range(4)])
        docs = await _paginate_all(paginate_func, cursor_collection, size=2, sort=[("meta.rank", -1)])
        assert [d["meta"]["rank"] for d in docs] == [3, 2, 1, 0]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_handles_mixed_type_ids(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"_id": 1, "n": 5}, {"_id": "x", "n": 5}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", 1)])
        assert {d["_id"] for d in docs} == {1, "x"}

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_supports_bson_sort_values(self, cursor_collection, paginate_func):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        await _replace(cursor_collection, [{"at": base + timedelta(days=i)} for i in range(4)])
        docs = await _paginate_all(paginate_func, cursor_collection, size=2, sort=[("at", 1)])
        # Default codec options read datetimes back as naive UTC.
        expected = [(base + timedelta(days=i)).replace(tzinfo=None) for i in range(4)]
        assert [d["at"] for d in docs] == expected

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_supports_uuid_sort_values(self, db_client, paginate_func):
        options = CodecOptions(uuid_representation=UuidRepresentation.STANDARD)
        collection = db_client.test.get_collection(f"cursor_{uuid4().hex}", codec_options=options)
        try:
            await _replace(collection, [{"n": i, "u": uuid4()} for i in range(4)])
            docs = await _paginate_all(paginate_func, collection, size=2, sort=[("u", 1)])
            values = [d["u"] for d in docs]
            assert len(values) == 4
            assert len(set(values)) == 4
        finally:
            await maybe_async(collection.drop())

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_empty_collection(self, cursor_collection, paginate_func):
        page = await maybe_async(paginate_func(cursor_collection, params=CursorParams(size=5), sort=[("id", 1)]))
        assert page.items == []
        assert page.next_page is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_exact_multiple_stops_cleanly(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"id": i} for i in range(6)])
        first = await maybe_async(paginate_func(cursor_collection, params=CursorParams(size=3), sort=[("id", 1)]))
        second = await maybe_async(
            paginate_func(
                cursor_collection,
                params=CursorParams(size=3, cursor=first.next_page),
                sort=[("id", 1)],
            )
        )
        assert [d["id"] for d in first.items] == [0, 1, 2]
        assert first.next_page is not None
        assert [d["id"] for d in second.items] == [3, 4, 5]
        assert second.next_page is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_invalid_cursor(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"id": i} for i in range(3)])
        with pytest.raises(HTTPException) as exc_info:
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(cursor="not-a-cursor"),
                    sort=[("id", 1)],
                )
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_sort_field_traversing_array(self, cursor_collection, paginate_func):
        # A dotted path crossing an array is ordered by the array's minimum
        # element, which the seek cannot reproduce, so it is rejected.
        await _replace(cursor_collection, [{"tags": [{"rank": i}]} for i in range(3)])
        with pytest.raises(ValueError, match="traverses an array"):
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(size=2),
                    sort=[("tags.rank", 1)],
                )
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_sort_mismatch(self, cursor_collection, paginate_func):
        # A cursor created under one sort must not be replayed against a different
        # sort, even when both resolve to the same number of keys.
        await _replace(cursor_collection, [{"a": i, "b": i} for i in range(4)])
        first = await maybe_async(paginate_func(cursor_collection, params=CursorParams(size=2), sort=[("a", 1)]))
        with pytest.raises(HTTPException) as exc_info:
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(cursor=first.next_page),
                    sort=[("b", 1)],
                )
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_direction_mismatch(self, cursor_collection, paginate_func):
        # The same field with a different direction is a different ordering, so a
        # cursor created under one direction must not be replayed under the other.
        await _replace(cursor_collection, [{"a": i} for i in range(4)])
        first = await maybe_async(paginate_func(cursor_collection, params=CursorParams(size=2), sort=[("a", 1)]))
        with pytest.raises(HTTPException) as exc_info:
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(cursor=first.next_page),
                    sort=[("a", -1)],
                )
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_accepts_id_plus_exclusion_projection(self, cursor_collection, paginate_func):
        # ``{"_id": 1, "secret": 0}`` is an exclusion projection (everything but
        # ``secret``); the sort field still comes back whole, so accept it.
        await _replace(cursor_collection, [{"n": i, "secret": "hidden"} for i in range(4)])
        docs = await _paginate_all(
            paginate_func,
            cursor_collection,
            size=2,
            sort=[("n", 1)],
            filter_fields={"_id": 1, "secret": 0},
        )
        assert [d["n"] for d in docs] == [0, 1, 2, 3]
        assert all("secret" not in d for d in docs)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_accepts_slice_projection_on_unrelated_field(self, cursor_collection, paginate_func):
        # A standalone $slice is an exclusion projection: unrelated fields,
        # including the sort field, still come back whole.
        await _replace(cursor_collection, [{"n": i, "comments": [i, i + 1, i + 2]} for i in range(4)])
        docs = await _paginate_all(
            paginate_func,
            cursor_collection,
            size=2,
            sort=[("n", 1)],
            filter_fields={"comments": {"$slice": 1}},
        )
        assert [d["n"] for d in docs] == [0, 1, 2, 3]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_accepts_sort_field_nested_under_included_id(self, cursor_collection, paginate_func):
        # ``{"_id": 1}`` returns a document-valued _id whole, so a sort field
        # nested under it is present and the projection is valid.
        await _replace(cursor_collection, [{"_id": {"rank": i}, "n": i} for i in range(4)])
        docs = await _paginate_all(
            paginate_func,
            cursor_collection,
            size=2,
            sort=[("_id.rank", 1)],
            filter_fields={"_id": 1},
        )
        assert [d["_id"]["rank"] for d in docs] == [0, 1, 2, 3]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_sorts_by_subdocument_when_returned_whole(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"meta": {"rank": i, "other": i}} for i in range(5)])
        docs = await _paginate_all(
            paginate_func,
            cursor_collection,
            size=2,
            sort=[("meta", 1)],
            filter_fields={"meta": 1},
        )
        assert [d["meta"]["rank"] for d in docs] == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_operator_projection_on_sort_field(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"n": [i, i + 1]} for i in range(4)])
        with pytest.raises(ValueError, match="filter_fields must return"):
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(size=2),
                    sort=[("n", 1)],
                    filter_fields={"n": {"$slice": 1}},
                )
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_computed_literal_projection(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"n": i} for i in range(4)])
        with pytest.raises(ValueError, match="filter_fields must return"):
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(size=2),
                    sort=[("n", 1)],
                    filter_fields={"n": [1, 2]},
                )
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_numeric_string_projection(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"n": i} for i in range(4)])
        with pytest.raises(ValueError, match="filter_fields must return"):
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(size=2),
                    sort=[("n", 1)],
                    filter_fields={"n": "1"},
                )
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_partial_subdocument_projection(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"meta": {"rank": i, "other": i}} for i in range(5)])
        with pytest.raises(ValueError, match="filter_fields must return"):
            await maybe_async(
                paginate_func(
                    cursor_collection,
                    params=CursorParams(size=2),
                    sort=[("meta", 1)],
                    filter_fields={"meta.rank": 1},
                )
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_respects_query_filter(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"n": i, "keep": i % 2 == 0} for i in range(6)])
        docs = await _paginate_all(
            paginate_func,
            cursor_collection,
            size=2,
            sort=[("n", 1)],
            query_filter={"keep": True},
        )
        assert [d["n"] for d in docs] == [0, 2, 4]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_preserves_or_query_filter(self, cursor_collection, paginate_func):
        # A filter whose top-level key ($or) collides with the seek condition must
        # survive, or unfiltered rows leak onto later pages.
        await _replace(cursor_collection, [{"n": i, "keep": i % 2 == 0} for i in range(6)])
        docs = await _paginate_all(
            paginate_func,
            cursor_collection,
            size=2,
            sort=[("n", 1)],
            query_filter={"$or": [{"keep": True}, {"n": 999}]},
        )
        assert [d["n"] for d in docs] == [0, 2, 4]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_honors_compound_sort(self, cursor_collection, paginate_func):
        # A second sort key must order the page and participate in the seek.
        await _replace(
            cursor_collection,
            [{"a": 1, "b": 2}, {"a": 1, "b": 1}, {"a": 2, "b": 9}, {"a": 1, "b": 3}],
        )
        docs = await _paginate_all(paginate_func, cursor_collection, size=2, sort=[("a", 1), ("b", 1)])
        assert [(d["a"], d["b"]) for d in docs] == [(1, 1), (1, 2), (1, 3), (2, 9)]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_honors_mixed_direction_compound_sort(self, cursor_collection, paginate_func):
        await _replace(
            cursor_collection,
            [{"a": 1, "b": 2}, {"a": 1, "b": 1}, {"a": 2, "b": 9}, {"a": 1, "b": 3}],
        )
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("a", 1), ("b", -1)])
        assert [(d["a"], d["b"]) for d in docs] == [(1, 3), (1, 2), (1, 1), (2, 9)]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_rejects_array_sort_field_off_the_page_boundary(self, cursor_collection, paginate_func):
        # The array document sorts first, so each page ends on a scalar; every
        # returned document must still be validated.
        await _replace(
            cursor_collection,
            [
                {"tags": [{"rank": 1}, {"rank": 10}]},
                {"tags": {"rank": 2}},
                {"tags": {"rank": 3}},
                {"tags": {"rank": 4}},
            ],
        )
        with pytest.raises(ValueError, match="traverses an array"):
            await maybe_async(paginate_func(cursor_collection, params=CursorParams(size=2), sort=[("tags.rank", 1)]))

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_handles_null_id(self, cursor_collection, paginate_func):
        # _id may be null (at most one document). With equal sort values, an
        # ascending pagination must not drop the rows that follow the null _id.
        await _replace(
            cursor_collection,
            [{"_id": None, "n": 1}, {"_id": ObjectId(), "n": 1}, {"_id": ObjectId(), "n": 1}],
        )
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", 1)])
        assert len(docs) == 3
        assert len({d["_id"] for d in docs}) == 3

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_default_id_sort_handles_null_id(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"_id": None, "n": 0}, {"_id": ObjectId(), "n": 1}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1)
        assert len(docs) == 2

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_descending_handles_null_id_tiebreaker(self, cursor_collection, paginate_func):
        await _replace(
            cursor_collection,
            [{"_id": None, "n": 1}, {"_id": ObjectId(), "n": 1}, {"_id": ObjectId(), "n": 1}],
        )
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", -1)])
        assert len(docs) == 3
        assert len({d["_id"] for d in docs}) == 3

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_default_id_sort_descending_handles_null_id(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"_id": None, "n": 0}, {"_id": ObjectId(), "n": 1}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("_id", -1)])
        assert len(docs) == 2

    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_descending_handles_mixed_type_ids(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"_id": 1, "n": 5}, {"_id": "x", "n": 5}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", -1)])
        assert {d["_id"] for d in docs} == {1, "x"}

    @pytest.mark.xfail(strict=True, reason="the seek compares within one BSON type")
    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_mixed_sort_types_stop_early(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"n": 1}, {"n": "a"}, {"n": 2}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=1, sort=[("n", 1)])
        assert len(docs) == 3

    @pytest.mark.xfail(strict=True, reason="arrays sort by min element, the seek compares lexicographically")
    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_array_sort_values_duplicate(self, cursor_collection, paginate_func):
        await _replace(cursor_collection, [{"tags": [5, 1]}, {"tags": [2]}, {"tags": [3, 9]}])
        docs = await _paginate_all(paginate_func, cursor_collection, size=2, sort=[("tags", 1)])
        assert len(docs) == 3


@mongodb_test
class TestPymongoAggregate(_BasePymongoSuite, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate_aggregate if is_async_db else paginate_aggregate

    @async_fixture(scope="session")
    async def entities(self, db_client):
        cursor = await maybe_async(
            db_client.test_agg.users.aggregate(
                [
                    {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                    {"$sort": {"name": 1}},
                ],
            )
        )
        return await maybe_async(cursor.to_list(length=None))

    @pytest.fixture(scope="session")
    def app(self, builder, db_client, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route():
            return await maybe_async(
                paginate_func(
                    db_client.test_agg.users,
                    [
                        {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                        {"$sort": {"name": 1}},
                    ],
                )
            )

        return builder.build()


@mongodb_test
class TestPymongoAggregateOptions(_BasePymongoSuite):
    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate_aggregate if is_async_db else paginate_aggregate

    @pytest.mark.asyncio(loop_scope="session")
    async def test_aggregation_filter_end_auto(self, db_client, paginate_func):
        pipeline = [
            {"$match": {"id": {"$gt": 50}}},
            {"$sort": {"id": 1}},
            {"$addFields": {"flag": True}},
        ]

        with set_page(Page[Any]):
            page = await maybe_async(
                paginate_func(
                    db_client.test.users,
                    pipeline,
                    Params(page=1, size=10),
                    aggregation_filter_end="auto",
                )
            )

        assert page.total == 50
        assert [item["id"] for item in page.items] == list(range(51, 61))
        assert all(item["flag"] for item in page.items)

    @pytest.mark.asyncio(loop_scope="session")
    async def test_include_total_false(self, db_client, paginate_func):
        NoTotalPage = CustomizedPage[Page[Any], UseIncludeTotal(False)]
        pipeline = [{"$sort": {"id": 1}}]

        with set_page(NoTotalPage), set_params(NoTotalPage.__params_type__(page=1, size=10)):
            page = await maybe_async(paginate_func(db_client.test.users, pipeline))

        assert page.total is None
        assert [item["id"] for item in page.items] == list(range(1, 11))
