import pytest

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.async_paginator import apaginate
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields

from .base import BasePaginationTestSuite


async def _len_func(seq):
    return len(seq)


def _additional_data_func(items):
    return {"new_field": sum(items)}


async def _async_additional_data_func(items):
    return {"new_field": sum(items)}


CustomPage = CustomizedPage[
    Page,
    UseAdditionalFields(new_field=int),
]


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "additional_data",
    [_additional_data_func, _async_additional_data_func],
    ids=["sync", "async"],
)
async def test_apaginator_additional_data_callable(additional_data):
    with set_page(CustomPage):
        page = await apaginate(
            [1, 2, 3],
            Params(page=1, size=2),
            additional_data=additional_data,
        )

    assert page.items == [1, 2]
    assert page.new_field == 3
