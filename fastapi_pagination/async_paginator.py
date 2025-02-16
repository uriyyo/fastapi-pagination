from collections.abc import Awaitable, Sequence
from typing import Any, Callable, Optional, TypeVar, Union

__all__ = ["paginate"]

from .bases import AbstractParams
from .config import Config
from .flow import flow_expr, run_async_flow
from .flows import generic_flow
from .types import AdditionalData, ItemsTransformer
from .utils import check_installed_extensions

T = TypeVar("T")


# same as default paginator, but allow to use async transformer
async def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Optional[Callable[[Sequence[T]], Union[int, Awaitable[int]]]] = None,
    *,
    safe: bool = False,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    if not safe:
        check_installed_extensions()

    length_function = length_function or len

    return await run_async_flow(
        generic_flow(
            limit_offset_flow=flow_expr(lambda r: sequence[r.as_slice()]),
            total_flow=flow_expr(lambda: length_function(sequence)),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
            async_=True,
        )
    )
