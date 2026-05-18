__all__ = [
    "CreatePageFactory",
    "CursorFlow",
    "CursorFlowFunc",
    "LimitOffsetFlow",
    "LimitOffsetFlowFunc",
    "TotalFlow",
    "TotalFlowFunc",
    "create_page_flow",
    "generic_flow",
]

from collections.abc import Callable, Sequence
from contextlib import ExitStack
from typing import Any, Protocol, TypeAlias

from .api import apply_items_transformer, create_page, set_page
from .bases import AbstractParams, CursorRawParams, RawParams, is_cursor, is_limit_offset
from .config import Config
from .flow import AnyFlow, flow
from .types import AdditionalData, AdditionalDataResult, ItemsTransformer, ParamsType
from .utils import is_additional_data_callable, verify_params

LimitOffsetFlow: TypeAlias = AnyFlow
CursorFlow: TypeAlias = AnyFlow[tuple[Any, dict[str, Any] | None]]
TotalFlow: TypeAlias = AnyFlow[int | None]

LimitOffsetFlowFunc: TypeAlias = Callable[[RawParams], AnyFlow]
CursorFlowFunc: TypeAlias = Callable[[CursorRawParams], AnyFlow[tuple[Any, dict[str, Any] | None]]]
TotalFlowFunc: TypeAlias = Callable[[], AnyFlow[int | None]]


class CreatePageFactory(Protocol):
    def __call__(
        self,
        items: Sequence[Any],
        /,
        total: int | None = None,
        params: AbstractParams | None = None,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover
        pass


@flow
def create_page_flow(
    items: Any,
    params: AbstractParams,
    /,
    total: int | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: dict[str, Any] | None = None,
    config: Config | None = None,
    async_: bool = False,
    create_page_factory: CreatePageFactory | None = None,
) -> Any:
    with ExitStack() as stack:
        if config and config.page_cls:
            stack.enter_context(set_page(config.page_cls))

        t_items = yield apply_items_transformer(  # type: ignore[ty:no-matching-overload]
            items,
            transformer,
            async_=async_,
        )

        if create_page_factory is None:
            create_page_factory = create_page

        page = yield create_page_factory(
            t_items,
            total=total,
            params=params,
            **(additional_data or {}),
        )

        return page


@flow
def additional_data_flow(
    items: Sequence[Any],
    additional_data: AdditionalData | None = None,
) -> AnyFlow[AdditionalDataResult]:
    if is_additional_data_callable(additional_data):
        resolved = yield additional_data(items)
        return resolved

    return additional_data or {}


@flow
def generic_flow(  # noqa: C901, PLR0912
    *,
    limit_offset_flow: LimitOffsetFlowFunc | None = None,
    cursor_flow: CursorFlowFunc | None = None,
    total_flow: TotalFlowFunc | None = None,
    params: AbstractParams | None = None,
    inner_transformer: ItemsTransformer | None = None,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
    async_: bool = False,
    create_page_factory: CreatePageFactory | None = None,
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

    cursor_data: dict[str, Any] | None = None
    if is_limit_offset(raw_params):
        if limit_offset_flow is None:
            raise ValueError("limit_offset_flow is required for 'limit-offset' params")

        items = yield from limit_offset_flow(raw_params)
    elif is_cursor(raw_params):
        if cursor_flow is None:
            raise ValueError("cursor_flow is required for 'cursor' params")

        items, cursor_data = yield from cursor_flow(raw_params)
    else:
        raise ValueError("Invalid params type")

    if inner_transformer:
        items = yield apply_items_transformer(  # type: ignore[ty:no-matching-overload]
            items,
            inner_transformer,
            async_=async_,
        )

    resolved_data = yield from additional_data_flow(
        items,
        additional_data,
    )

    if cursor_data:
        resolved_data.update(cursor_data)

    page = yield from create_page_flow(
        items,
        params,
        total=total,
        transformer=transformer,
        additional_data=resolved_data,
        config=config,
        async_=async_,
        create_page_factory=create_page_factory,
    )

    return page
