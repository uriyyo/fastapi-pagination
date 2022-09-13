from typing import Optional, TypeVar, Union

from beanie import Document
from beanie.odm.queries.find import FindMany

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params

TDocument = TypeVar("TDocument", bound=Document)


async def paginate(
    query: Union[TDocument, FindMany[TDocument]],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[TDocument]:
    params = verify_params(params, "limit-offset")
    raw_params = params.to_raw_params().as_limit_offset()

    items = await query.find_many(limit=raw_params.limit, skip=raw_params.offset).to_list()
    total = await query.count()

    return create_page(items, total, params)


__all__ = [
    "paginate",
]
