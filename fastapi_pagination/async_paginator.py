from typing import Any, Awaitable, Callable, Optional, Sequence, TypeVar, Union

__all__ = ["paginate"]

from .api import apply_items_transformer, create_page
from .bases import AbstractParams
from .types import AdditionalData, ItemsTransformer
from .utils import await_if_async, check_installed_extensions, verify_params

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
) -> Any:
    if not safe:
        check_installed_extensions()

    params, raw_params = verify_params(params, "limit-offset")

    items = sequence[raw_params.as_slice()]
    t_items = await apply_items_transformer(items, transformer, async_=True)

    length_function = length_function or len

    total = None
    if raw_params.include_total:
        total = await await_if_async(length_function, sequence)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
