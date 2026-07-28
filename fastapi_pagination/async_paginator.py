from collections.abc import Awaitable, Callable, Sequence
from typing import Any, TypeVar

__all__ = ["apaginate"]

from .bases import AbstractParams
from .config import Config
from .flow import flow_expr, run_async_flow
from .flows import generic_flow
from .types import AdditionalData, ItemsTransformer
from .utils import check_installed_extensions

T = TypeVar("T")


# same as default paginator, but allow to use async transformer
async def apaginate(
    sequence: Sequence[T],
    params: AbstractParams | None = None,
    length_function: Callable[[Sequence[T]], int | Awaitable[int]] | None = None,
    *,
    safe: bool = False,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
) -> Any:
    if not safe:
        check_installed_extensions()

    if length_function is None:
        length_function = len

    return await run_async_flow(
        generic_flow(
            limit_offset_flow=flow_expr(lambda r: sequence[r.as_slice()]),
            total_flow=flow_expr(lambda: length_function(sequence)),  # type: ignore[ty:invalid-argument-type]
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
            async_=True,
        )
    )
