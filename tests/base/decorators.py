from __future__ import annotations

__all__ = [
    "async_sync_testsuite",
    "async_testsuite",
    "cases",
    "sync_testsuite",
]

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import Self

from .reflect import collect_case_types
from .types import PaginationCaseType

if TYPE_CHECKING:
    from .suite import BasePaginationTestSuite

    TBasePaginationTestSuite = TypeVar("TBasePaginationTestSuite", bound=type[BasePaginationTestSuite])


@dataclass
class _Cases:
    _cases: set[PaginationCaseType] = field(default_factory=set)

    def _add(self, case: PaginationCaseType) -> Self:
        return replace(self, _cases={*self._cases, case})

    @property
    def default(self) -> Self:
        return self._add("default")

    @property
    def non_scalar(self) -> Self:
        return self._add("non-scalar")

    @property
    def relationship(self) -> Self:
        return self._add("relationship")

    @property
    def optional(self) -> Self:
        return self._add("optional")

    @property
    def only(self) -> Self:
        return replace(self, _cases=set())

    def auto(self, cls: TBasePaginationTestSuite) -> TBasePaginationTestSuite:
        cls.case_types = collect_case_types(cls)
        return cls

    def __call__(self, cls: TBasePaginationTestSuite) -> TBasePaginationTestSuite:
        cls.case_types = {*self._cases}
        return cls


cases = _Cases({"default"})


def async_testsuite(cls: TBasePaginationTestSuite) -> TBasePaginationTestSuite:
    @pytest.fixture(scope="session")
    def is_async_db(self):
        return True

    cls.is_async_db = is_async_db
    return cls


def sync_testsuite(cls: TBasePaginationTestSuite) -> TBasePaginationTestSuite:
    @pytest.fixture(scope="session")
    def is_async_db(self):
        return False

    cls.is_async_db = is_async_db
    return cls


def async_sync_testsuite(cls: TBasePaginationTestSuite) -> TBasePaginationTestSuite:
    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["async", "sync"],
    )
    def is_async_db(self, request):
        return request.param

    cls.is_async_db = is_async_db
    return cls
