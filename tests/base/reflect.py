__all__ = [
    "collect_case_types",
    "collect_pagination_types",
]

import ast
import inspect
import textwrap
from collections.abc import Iterable
from typing import Any, cast, get_args

from .types import PaginationCaseType, PaginationType


def _iter_decorators(cls: type[Any]) -> Iterable[ast.expr]:
    root = ast.parse(textwrap.dedent(inspect.getsource(cls.app)))
    func_body = root.body[0].body

    for func in func_body:
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for dec in func.decorator_list:
            yield from ast.walk(dec)


def _iter_decorators_attrs(cls: type[Any]) -> Iterable[str]:
    for node in _iter_decorators(cls):
        if not isinstance(node, ast.Attribute):
            continue

        yield node.attr.replace("_", "-")


def collect_case_types(cls: type[Any]) -> set[PaginationCaseType]:
    _cases = {attr for attr in _iter_decorators_attrs(cls) if attr in get_args(PaginationCaseType)}

    assert _cases, f"No cases found in {cls}"
    return cast(set[PaginationCaseType], _cases)


def collect_pagination_types(cls: type[Any]) -> set[PaginationType]:
    _types = set()

    for attr in _iter_decorators_attrs(cls):
        if attr == "both":
            _types |= {"page-size", "limit-offset"}
        elif attr in get_args(PaginationType):
            _types.add(attr)

    assert _types, f"No types found in {cls}"
    return _types
