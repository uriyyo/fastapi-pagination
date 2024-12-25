from contextlib import suppress
from typing import ClassVar

import pytest

from fastapi_pagination.iterables import LimitOffsetPage, Page, paginate

from .base import BasePaginationTestSuite, SuiteBuilder


class _IterablesSuiteMixin:
    with_total: ClassVar[bool]

    def _normalize_expected(self, result):
        if self.with_total:
            return result

        result.total = None

        with suppress(ValueError):
            result.pages = None

        return result

    @classmethod
    def create_builder(cls) -> SuiteBuilder:
        return SuiteBuilder.with_classes(
            page_size=Page,
            limit_offset=LimitOffsetPage,
        )

    @pytest.fixture(scope="session")
    def app(self, builder, entities):
        @builder.both.default
        async def route():
            kwargs = {"total": len(entities)} if self.with_total else {}
            return paginate((entity for entity in entities), **kwargs)

        return builder.build()


class TestIterablesPaginationNoTotal(_IterablesSuiteMixin, BasePaginationTestSuite):
    with_total = False


class TestIterablesPaginationWithTotal(_IterablesSuiteMixin, BasePaginationTestSuite):
    with_total = True
