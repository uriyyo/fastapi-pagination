from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar, TypeAlias

import pytest

from fastapi_pagination import LimitOffsetPage, LimitOffsetParams, Page, Params, paginate, set_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.cursor import CursorParams
from fastapi_pagination.pydantic import IS_PYDANTIC_V2
from tests.utils import normalize, parse_obj

from .builder import SuiteBuilder
from .reflect import collect_case_types, collect_pagination_types
from .types import MakeOptionalPage, PaginationCaseType, PaginationType

_default_params = [
    Params(page=1),
    Params(page=2),
    Params(page=3),
    Params(size=100),
    Params(page=1, size=10),
    Params(page=9, size=10),
    Params(page=10, size=10),
    Params(page=2, size=25),
    Params(size=31),
]
_limit_offset_params = [
    LimitOffsetParams(limit=50),
    LimitOffsetParams(limit=50, offset=50),
    LimitOffsetParams(limit=50, offset=100),
    LimitOffsetParams(limit=100),
    LimitOffsetParams(limit=10),
    LimitOffsetParams(limit=10, offset=80),
    LimitOffsetParams(limit=10, offset=90),
    LimitOffsetParams(limit=25, offset=25),
    LimitOffsetParams(limit=31),
]
_params_desc = [
    "first",
    "second",
    "third-empty",
    "full-page",
    "first-10-items",
    "last-10-items",
    "after-last-10-items-empty",
    "second-25-items",
    "31-items",
]

SuiteDecl: TypeAlias = tuple[
    AbstractParams,
    PaginationType,
    PaginationCaseType,
    bool,
    str,
]


@pytest.mark.usefixtures("db_type")
class BasePaginationTestSuite:
    pagination_types: ClassVar[set[PaginationType]] = {}
    case_types: ClassVar[set[PaginationCaseType]] = {}
    include_total: ClassVar[bool] = True
    add_pydantic_v1_suites: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.__module__ == __name__:
            return

        if not cls.case_types:
            cls.case_types = collect_case_types(cls)
        if not cls.pagination_types:
            cls.pagination_types = collect_pagination_types(cls)

        suites = [pytest.param(*values, id=id_) for *values, id_ in cls._add_pydantic_v1_suites(cls.generate_suites())]

        if suites:
            marker = pytest.mark.parametrize(
                ("params", "pagination_type", "pagination_case_type", "pydantic_v1"),
                suites,
            )

            @marker
            @pytest.mark.asyncio(loop_scope="session")
            async def _run_pagination(
                self,
                client,
                params,
                pagination_type,
                pagination_case_type,
                pydantic_v1,
                entities,
                builder,
            ):
                await self.run_pagination_test(
                    client,
                    params,
                    pagination_type,
                    pagination_case_type,
                    pydantic_v1,
                    entities,
                    builder,
                )

            cls.test_pagination = _run_pagination

        cursor_suites = [
            pytest.param(*values, id=id_) for *values, id_ in cls._add_pydantic_v1_suites(cls.generate_cursor_suites())
        ]

        if cursor_suites:
            marker = pytest.mark.parametrize(
                ("params", "pagination_type", "pagination_case_type", "pydantic_v1"),
                cursor_suites,
            )

            @marker
            @pytest.mark.asyncio(loop_scope="session")
            async def _run_cursor_pagination(
                self,
                client,
                params,
                pagination_type,
                pagination_case_type,
                pydantic_v1,
                entities,
                builder,
            ):
                await self.run_cursor_pagination_test(
                    client,
                    params,
                    pagination_type,
                    pagination_case_type,
                    pydantic_v1,
                    entities,
                    builder,
                )

            cls.test_cursor_pagination = _run_cursor_pagination

    @classmethod
    def _add_pydantic_v1_suites(cls, suites: Iterable[SuiteDecl]) -> Iterable[SuiteDecl]:
        for param, pagination_type, pagination_case_type, _, id_ in suites:
            yield param, pagination_type, pagination_case_type, False, id_

            if IS_PYDANTIC_V2 and cls.add_pydantic_v1_suites:
                yield param, pagination_type, pagination_case_type, True, f"{id_}-pydantic-v1-compatible"

    @classmethod
    def generate_suites(cls) -> Iterable[SuiteDecl]:
        if "page-size" in cls.pagination_types:
            for case in {*cls.case_types} - {"optional"}:
                for param, name in zip(_default_params, _params_desc, strict=False):
                    yield param, "page-size", case, False, f"page-size-{case}-{name}"

            if "optional" in cls.case_types:
                yield (
                    MakeOptionalPage[Page].__params_type__(),
                    "page-size",
                    "optional",
                    False,
                    "page-size-optional",
                )

        if "limit-offset" in cls.pagination_types:
            for case in {*cls.case_types} - {"optional"}:
                for param, name in zip(_limit_offset_params, _params_desc, strict=False):
                    yield param, "limit-offset", case, False, f"limit-offset-{case}-{name}"

            if "optional" in cls.case_types:
                yield (
                    MakeOptionalPage[LimitOffsetPage].__params_type__(),
                    "limit-offset",
                    "optional",
                    False,
                    "limit-offset-optional",
                )

    @classmethod
    def generate_cursor_suites(cls) -> Iterable[SuiteDecl]:
        if "cursor" not in cls.pagination_types:
            return
        if "default" not in cls.case_types:
            return

        yield CursorParams(size=22), "cursor", "default", False, "cursor-default"

    @classmethod
    def create_builder(cls) -> SuiteBuilder:
        return SuiteBuilder()

    @pytest.fixture(scope="session")
    def builder(self) -> SuiteBuilder:
        return self.create_builder()

    async def run_cursor_pagination_test(
        self,
        client,
        params,
        pagination_type,
        pagination_case_type,
        pydantic_v1,
        entities,
        builder,
    ):
        path = builder.get_route_path(pagination_type, pagination_case_type)
        entities = self._prepare_cursor_entities(entities)
        cursor = params.cursor
        size = params.size
        cls = builder.get_response_model_for(pagination_type, pagination_case_type, pydantic_v1)

        while entities:
            http_params = params.dict(exclude_none=True)
            if cursor:
                http_params["cursor"] = cursor

            response = await client.get(path, params=http_params)
            response.raise_for_status()

            data = response.json()
            page = parse_obj(cls, data)

            assert len(page.items) == min(len(entities), size)

            with set_page(cls):
                expected = self._normalize_expected(
                    cls.create(
                        entities[: len(page.items)],
                        params,
                        total=len(entities) if self.include_total else None,
                    ),
                )

            assert page.items == expected.items

            cursor = data.get("next_page")
            entities = entities[len(page.items) :]

    async def run_pagination_test(
        self,
        client,
        params,
        pagination_type,
        pagination_case_type,
        pydantic_v1,
        entities,
        builder,
    ):
        path = builder.get_route_path(pagination_type, pagination_case_type)

        response = await client.get(path, params=params.dict(exclude_none=True))
        response.raise_for_status()

        cls = builder.get_response_model_for(pagination_type, pagination_case_type, pydantic_v1)

        with set_page(cls):
            expected = self._normalize_expected(paginate(entities, params))

        a, b = normalize(cls, expected, response.json())
        assert a == b

    def _normalize_expected(self, result):
        return result

    def _prepare_cursor_entities(self, entities):
        return sorted(entities, key=lambda entity: entity.id)
