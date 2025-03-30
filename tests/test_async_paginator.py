import pytest

from fastapi_pagination.async_paginator import apaginate

from .base import BasePaginationTestSuite, SuiteBuilder


async def _len_func(seq):
    return len(seq)


class TestAsyncPaginationParams(BasePaginationTestSuite):
    @pytest.fixture(
        scope="session",
        params=[len, _len_func],
        ids=["sync", "async"],
    )
    def len_function(self, request):
        return request.param

    @pytest.fixture(scope="session")
    def builder(self, len_function) -> SuiteBuilder:
        return self.create_builder()

    @pytest.fixture(scope="session")
    def app(self, builder, entities, len_function):
        @builder.both.default.optional
        async def route():
            return await apaginate(entities, length_function=len_function)

        return builder.build()
