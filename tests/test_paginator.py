import pytest

from fastapi_pagination import (
    Page,
    Params,
    paginate,
    set_page,
)
from fastapi_pagination.api import set_items_transformer
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields

from .base import BasePaginationTestSuite


class TestPaginationParams(BasePaginationTestSuite):
    add_pydantic_v1_suites = True

    @pytest.fixture(scope="session")
    def app(self, builder, entities):
        @builder.both.default.optional
        async def route():
            return paginate(entities)

        return builder.build()


CustomPage = CustomizedPage[
    Page,
    UseAdditionalFields(new_field=int),
]


def test_paginator_additional_data():
    with set_page(CustomPage):
        page = paginate([], Params(), additional_data={"new_field": 10})

    assert page == CustomPage(items=[], total=0, page=1, pages=0, size=50, new_field=10)


def test_explicit_params():
    page = paginate([], Params(page=2, size=10))

    assert page == Page(items=[], total=0, page=2, pages=0, size=10)


def test_explicit_items_transformer():
    def transformer(items):
        return [item * 2 for item in items]

    page = paginate([1, 2, 3], Params(), transformer=transformer)

    assert page == Page(items=[2, 4, 6], total=3, page=1, pages=1, size=50)


def test_implicit_items_transformer():
    def transformer(items):
        return [item * 2 for item in items]

    with set_items_transformer(transformer):
        page = paginate([1, 2, 3], Params())

    assert page == Page(items=[2, 4, 6], total=3, page=1, pages=1, size=50)
