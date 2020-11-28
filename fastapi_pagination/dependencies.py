from typing import Awaitable, Callable, Type, Union

from fastapi import Depends

from .params import (
    CurrentPaginationParamsValue,
    LimitOffsetPaginationParams,
    PaginationParams,
    PaginationParamsType,
)


def using_pagination_params(
    params_type: Union[Type[PaginationParams], Type[LimitOffsetPaginationParams]]
) -> Callable[[PaginationParamsType], Awaitable[PaginationParamsType]]:
    async def _pagination_params(params: params_type = Depends()) -> params_type:  # type: ignore
        CurrentPaginationParamsValue.set(params)
        return params

    return _pagination_params


pagination_params = using_pagination_params(PaginationParams)


__all__ = ["using_pagination_params", "pagination_params"]
