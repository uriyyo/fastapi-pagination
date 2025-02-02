import pytest

from fastapi_pagination.ext.firestore import apaginate, paginate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import maybe_async


class _BaseFirestoreSuite:
    @pytest.fixture(scope="session")
    def firestore(self, firestore_project_id, is_async_db):
        from google.cloud import firestore as _firestore

        if is_async_db:
            return _firestore.AsyncClient(project=firestore_project_id)

        return _firestore.Client(project=firestore_project_id)

    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate if is_async_db else paginate

    @pytest.fixture(scope="session")
    def entities(self, entities):
        return sorted(entities, key=lambda x: x.name)


@async_sync_testsuite
class TestDefaultFirestore(_BaseFirestoreSuite, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, firestore, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route():
            return await maybe_async(paginate_func(firestore.collection("users").order_by("name")))

        return builder.build()


@async_sync_testsuite
class TestCursorFirestore(_BaseFirestoreSuite, BasePaginationTestSuite):
    def _prepare_cursor_entities(self, entities):
        return sorted(entities, key=lambda x: x.name)

    @pytest.fixture(scope="session")
    def app(self, builder, firestore, paginate_func):
        builder = builder.new()

        @builder.cursor.default
        async def route():
            return await maybe_async(paginate_func(firestore.collection("users").order_by("name")))

        return builder.build()
