__all__ = [
    "create_page_flow",
    "generic_flow",
]

from contextlib import ExitStack
from typing import Any, Callable, Optional

from .api import apply_items_transformer, create_page, set_page
from .bases import AbstractParams, CursorRawParams, RawParams, is_cursor, is_limit_offset
from .config import Config
from .flow import AnyFlow, flow
from .types import ItemsTransformer, ParamsType
from .utils import verify_params


@flow
def create_page_flow(
    items: Any,
    params: AbstractParams,
    /,
    total: Optional[int] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[dict[str, Any]] = None,
    config: Optional[Config] = None,
    async_: bool = False,
) -> Any:
    with ExitStack() as stack:
        if config and config.page_cls:
            stack.enter_context(set_page(config.page_cls))

        t_items = yield apply_items_transformer(  # type: ignore[call-overload]
            items,
            transformer,
            async_=async_,
        )

        return create_page(
            t_items,
            total=total,
            params=params,
            **(additional_data or {}),
        )


@flow
def generic_flow(
    *,
    limit_offset_flow: Optional[Callable[[RawParams], AnyFlow]] = None,
    cursor_flow: Optional[Callable[[CursorRawParams], AnyFlow]] = None,
    total_flow: Optional[Callable[[], AnyFlow]] = None,
    params: Optional[AbstractParams] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[dict[str, Any]] = None,
    config: Optional[Config] = None,
    async_: bool = False,
) -> Any:
    types: list[ParamsType] = []
    if limit_offset_flow is not None:
        types.append("limit-offset")
    if cursor_flow is not None:
        types.append("cursor")

    if not types:
        raise ValueError("At least one flow must be provided")

    params, raw_params = verify_params(params, *types)

    total = None
    if raw_params.include_total:
        if total_flow is None:
            raise ValueError("total_flow is required when include_total is True")

        total = yield from total_flow()

    if is_limit_offset(raw_params):
        if limit_offset_flow is None:
            raise ValueError("limit_offset_flow is required for 'limit-offset' params")

        items = yield from limit_offset_flow(raw_params)
    elif is_cursor(raw_params):
        if cursor_flow is None:
            raise ValueError("cursor_flow is required for 'cursor' params")

        items = yield from cursor_flow(raw_params)
    else:
        raise ValueError("Invalid params type")

    page = yield from create_page_flow(
        items,
        params,
        total=total,
        transformer=transformer,
        additional_data=additional_data,
        config=config,
        async_=async_,
    )

    return page
