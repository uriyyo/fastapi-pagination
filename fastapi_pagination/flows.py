__all__ = [
    "CursorFlow",
    "CursorFlowFunc",
    "LimitOffsetFlow",
    "LimitOffsetFlowFunc",
    "TotalFlow",
    "TotalFlowFunc",
    "create_page_flow",
    "generic_flow",
]

from contextlib import ExitStack
from typing import Any, Callable, Optional

from typing_extensions import TypeAlias

from .api import apply_items_transformer, create_page, set_page
from .bases import AbstractParams, CursorRawParams, RawParams, is_cursor, is_limit_offset
from .config import Config
from .flow import AnyFlow, flow
from .types import AdditionalData, ItemsTransformer, ParamsType
from .utils import verify_params

LimitOffsetFlow: TypeAlias = AnyFlow
CursorFlow: TypeAlias = AnyFlow[tuple[Any, Optional[AdditionalData]]]
TotalFlow: TypeAlias = AnyFlow[Optional[int]]

LimitOffsetFlowFunc: TypeAlias = Callable[[RawParams], AnyFlow]
CursorFlowFunc: TypeAlias = Callable[[CursorRawParams], AnyFlow[tuple[Any, Optional[AdditionalData]]]]
TotalFlowFunc: TypeAlias = Callable[[], AnyFlow[Optional[int]]]


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
def generic_flow(  # noqa: C901
    *,
    limit_offset_flow: Optional[LimitOffsetFlowFunc] = None,
    cursor_flow: Optional[CursorFlowFunc] = None,
    total_flow: Optional[TotalFlowFunc] = None,
    params: Optional[AbstractParams] = None,
    inner_transformer: Optional[ItemsTransformer] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
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
    additional_data = additional_data or {}

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

        items, more_data = yield from cursor_flow(raw_params)
        additional_data.update(more_data or {})
    else:
        raise ValueError("Invalid params type")

    if inner_transformer:
        items = yield apply_items_transformer(  # type: ignore[call-overload]
            items,
            inner_transformer,
            async_=async_,
        )

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
