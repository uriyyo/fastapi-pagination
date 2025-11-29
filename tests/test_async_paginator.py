import pytest

from fastapi_pagination.async_paginator import apaginate

from .base import BasePaginationTestSuite


async def _len_func(seq):
    return len(seq)


class TestAsyncPaginationParams(BasePaginationTestSuite):
    add_pydantic_v1_suites = True

    @pytest.fixture(
        scope="session",
        params=[len, _len_func, None],
        ids=["sync", "async", "default"],
    )
    def len_function(self, request):
        return request.param

    @pytest.fixture(scope="session")
    def app(self, builder, entities, len_function):
        builder = builder.new()

        @builder.both.default.optional
        async def route():
            return await apaginate(entities, length_function=len_function)

        return builder.build()
