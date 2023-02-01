__all__ = ["paginate"]

from typing import Any, Dict, Mapping, Optional, Type, TypeVar

from cassandra.cluster import SimpleStatement
from cassandra.cqlengine import connection
from cassandra.cqlengine.models import Model

from ..api import create_page
from ..types import AdditionalData
from ..utils import TParams, verify_params

T = TypeVar("T", bound=Mapping[str, Any])


def paginate(
    model: Type[Model],
    query_filter: Optional[Dict[Any, Any]] = None,
    params: Optional[TParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "cursor")

    query_filter = query_filter or {}
    stmt = SimpleStatement(
        str(model.filter(**query_filter)),
        fetch_size=raw_params.size,
    )
    conn = connection.get_connection()

    cursor = conn.session.execute(
        stmt, parameters={str(i): v for i, v in enumerate(query_filter.values())}, paging_state=raw_params.cursor
    )
    items = cursor.current_rows

    return create_page(items, params=params, next_=cursor.paging_state, **(additional_data or {}))
