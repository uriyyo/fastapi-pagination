__all__ = ["paginate"]

from copy import deepcopy
from typing import Optional, Type, Union, TypeVar, cast, List, Any

from piccolo.query import Select
from piccolo.query.methods.select import Count
from piccolo.table import Table

from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

T = TypeVar("T", bound=Table, covariant=True)


async def paginate(
    query: Union[Select[T], Type[T]],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if not isinstance(query, Select):
        query = query.select()

    # query object is mutable, so we need deepcopy of it
    query = deepcopy(query)

    # need another copy for count query
    count_query = deepcopy(query)
    count_query.columns_delegate.selected_columns = []

    total = 0
    if row := await count_query.columns(Count()).first():
        total = row["count"]

    items = await query.offset(raw_params.offset).limit(raw_params.limit)

    return create_page(cast(List[T], items), total, params, **(additional_data or {}))
