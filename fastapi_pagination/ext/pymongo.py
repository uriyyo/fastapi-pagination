from __future__ import annotations

__all__ = [
    "apaginate",
    "apaginate_aggregate",
    "paginate",
    "paginate_aggregate",
]


from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypeVar

from bson import json_util
from bson.json_util import JSONOptions
from fastapi import HTTPException, status
from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.collection import Collection

from fastapi_pagination.bases import AbstractParams, CursorRawParams
from fastapi_pagination.config import Config
from fastapi_pagination.ext.mongo import AggrPipelineTransformer, _extract_total, _facet_stage
from fastapi_pagination.ext.utils import get_mongo_pipeline_filter_end
from fastapi_pagination.flow import flow, flow_expr, run_async_flow, run_sync_flow
from fastapi_pagination.flows import additional_data_flow, create_page_flow, generic_flow
from fastapi_pagination.types import AdditionalData, Cursor, ItemsTransformer, SyncAdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

T = TypeVar("T", bound=Mapping[str, Any])

_ID = "_id"


def _resolve_sort(sort: Sequence[Any] | str | None) -> list[tuple[str, int]]:
    """Resolve ``sort`` into ordered ``(field, direction)`` keys, appending ``_id`` ascending as the default unless
    already present.
    """
    keys: list[tuple[str, int]] = []
    if isinstance(sort, str):
        keys.append((sort, ASCENDING))
    elif sort:
        for entry in sort:
            if isinstance(entry, str):
                keys.append((entry, ASCENDING))
            else:
                field, direction = entry
                keys.append((field, direction))

    if not any(field == _ID for field, _ in keys):
        tie_direction = keys[-1][1] if keys else ASCENDING
        keys.append((_ID, tie_direction))

    return keys


def _sort_fingerprint(keys: Sequence[tuple[str, int]]) -> list[list[Any]]:
    """Return a JSON-comparable representation of the resolved sort keys."""
    return [[field, direction] for field, direction in keys]


def _encode_position(
    values: Sequence[Any],
    *,
    backwards: bool,
    keys: Sequence[tuple[str, int]],
    json_options: JSONOptions,
) -> str:
    """Encode a cursor position as Extended JSON, so BSON values round-trip."""
    return json_util.dumps(
        {
            "values": list(values),
            "backwards": backwards,
            "sort": _sort_fingerprint(keys),
        },
        json_options=json_options,
    )


def _decode_position(cursor: Cursor, json_options: JSONOptions) -> tuple[list[Any], bool, list[Any]]:
    try:
        data = json_util.loads(cursor, json_options=json_options)
        values = data["values"]
        backwards = bool(data["backwards"])
        sort = data["sort"]
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor value") from exc
    if not isinstance(values, list) or not isinstance(sort, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor value")
    return values, backwards, sort


def _resolve_field(document: Mapping[str, Any], path: str) -> Any:
    """Return the value at dotted ``path`` in ``document``, or ``None``."""
    value: Any = document
    for part in path.split("."):
        if isinstance(value, Mapping):
            if part not in value:
                return None
            value = value[part]
        elif isinstance(value, list) and part.isdigit():
            index = int(part)
            if index >= len(value):
                return None
            value = value[index]
        elif isinstance(value, list):
            raise ValueError(
                f"sort field {path!r} traverses an array; array-valued sort fields are not supported",
            )
        else:
            return None
    if isinstance(value, list):
        raise ValueError(  # noqa: TRY004
            f"sort field {path!r} is array-valued; array-valued sort fields are not supported",
        )
    return value


def _is_whole_field_flag(value: Any) -> bool:
    """Return whether a projection entry includes its field in full."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return False


def _is_inclusion_entry(value: Any) -> bool:
    """Return whether a projection entry selects inclusion mode."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, Mapping):
        return "$slice" not in value
    return True


def _projection_returns_fully(projection: Mapping[str, Any] | None, field: str) -> bool:
    """Return whether ``projection`` returns ``field`` in full."""
    if projection is None:
        return True
    others = {path: value for path, value in projection.items() if path != _ID}
    inclusion = (
        any(_is_inclusion_entry(value) for value in others.values())
        if others
        else _is_inclusion_entry(projection.get(_ID, 0))
    )
    # ``_id`` is included whole by default, so a field nested under it is present
    # unless the projection touches the ``_id`` subtree; model that with an
    # implicit ``{"_id": 1}``.
    paths = projection
    if not any(path == _ID or path.startswith(f"{_ID}.") for path in projection):
        paths = {**projection, _ID: 1}
    if inclusion:
        return any(
            (field == path or field.startswith(f"{path}.")) and _is_whole_field_flag(value)
            for path, value in paths.items()
        )
    return not any(
        field == path or field.startswith(f"{path}.") or path.startswith(f"{field}.")
        for path, value in paths.items()
        if not _is_whole_field_flag(value)
    )


def _id_seek(direction: int, last_id: Any) -> dict[str, Any]:
    """Build the ``_id`` tiebreaker seek past ``last_id``."""
    operator = "$gt" if direction == ASCENDING else "$lt"
    # ``$expr`` compares by BSON total order, so it handles ids of different types
    # and the null id (first ascending, last descending) without special cases.
    return {"$expr": {operator: [f"${_ID}", {"$literal": last_id}]}}


def _field_eq(field: str, value: Any) -> dict[str, Any]:
    """Condition for ``field`` equal to a cursor value."""
    if field == _ID:
        return {"$expr": {"$eq": [f"${_ID}", {"$literal": value}]}}
    if value is None:
        return {field: None}
    return {field: {"$eq": value}}


def _field_after(field: str, direction: int, value: Any) -> dict[str, Any] | None:
    """Condition for ``field`` sorting strictly after ``value``, or ``None`` if nothing does."""
    if field == _ID:
        return _id_seek(direction, value)
    if value is None:
        if direction == ASCENDING:
            # Nulls sort first ascending, so every non-null value follows.
            return {field: {"$ne": None}}
        return None
    operator = "$gt" if direction == ASCENDING else "$lt"
    after: list[dict[str, Any]] = [{field: {operator: value}}]
    if direction == DESCENDING:
        # Nulls sort after every non-null value, so they still follow.
        after.append({field: None})
    return after[0] if len(after) == 1 else {"$or": after}


def _seek_query(
    keys: Sequence[tuple[str, int]],
    directions: Sequence[int],
    values: Sequence[Any],
) -> dict[str, Any]:
    """Build the condition selecting documents strictly after a cursor position."""
    branches: list[dict[str, Any]] = []
    prefix: list[dict[str, Any]] = []
    for (field, _), direction, value in zip(keys, directions, values, strict=True):
        after = _field_after(field, direction, value)
        if after is not None:
            branches.append({"$and": [*prefix, after]} if prefix else after)
        prefix.append(_field_eq(field, value))
    return branches[0] if len(branches) == 1 else {"$or": branches}


def _build_page(
    documents: Sequence[Mapping[str, Any]],
    keys: Sequence[tuple[str, int]],
    size: int,
    *,
    backwards: bool,
    had_cursor: bool,
    json_options: JSONOptions,
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    """Slice a ``size + 1`` fetch into a page and its next/previous cursors."""
    has_more = len(documents) > size
    items = list(documents[:size])
    # Resolve every sort key for every returned document so an array traversal
    # anywhere in the page raises, since it makes the ordering unreproducible.
    resolved = [[_resolve_field(document, field) for field, _ in keys] for document in items]
    if backwards:
        items.reverse()
        resolved.reverse()

    cursor_data: dict[str, Any] = {}
    if items:
        if backwards or has_more:
            cursor_data["next_"] = _encode_position(
                resolved[-1],
                backwards=False,
                keys=keys,
                json_options=json_options,
            )
        if (had_cursor and not backwards) or (backwards and has_more):
            cursor_data["previous"] = _encode_position(
                resolved[0],
                backwards=True,
                keys=keys,
                json_options=json_options,
            )

    return items, cursor_data


@flow
def _cursor_flow(
    collection: Collection[T] | AsyncCollection[T],
    query_filter: dict[Any, Any],
    filter_fields: dict[Any, Any] | None,
    sort: Sequence[Any] | str | None,
    raw_params: CursorRawParams,
    **kwargs: Any,
) -> Any:
    keys = _resolve_sort(sort)
    size = raw_params.size
    json_options = JSONOptions(uuid_representation=collection.codec_options.uuid_representation)

    if filter_fields is not None:
        dropped = [
            field
            for field in dict.fromkeys(field for field, _ in keys)
            if not _projection_returns_fully(filter_fields, field)
        ]
        if dropped:
            raise ValueError(
                f"filter_fields must return {' and '.join(dropped)} in full to build the cursor",
            )

    query: dict[Any, Any] = dict(query_filter)
    backwards = False
    if raw_params.cursor:
        values, backwards, cursor_sort = _decode_position(raw_params.cursor, json_options)
        if len(values) != len(keys) or cursor_sort != _sort_fingerprint(keys):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cursor does not match the current sort",
            )
        directions = [-direction if backwards else direction for _, direction in keys]
        seek = _seek_query(keys, directions, values)
        query = {"$and": [query, seek]} if query else seek
    else:
        directions = [direction for _, direction in keys]

    cursor = yield collection.find(
        query,
        filter_fields,
        sort=[(field, direction) for (field, _), direction in zip(keys, directions, strict=True)],
        limit=size + 1,
        **kwargs,
    )
    documents = yield cursor.to_list(length=size + 1)

    return _build_page(
        documents,
        keys,
        size,
        backwards=backwards,
        had_cursor=bool(raw_params.cursor),
        json_options=json_options,
    )


def paginate(
    collection: Collection[T],
    query_filter: dict[Any, Any] | None = None,
    filter_fields: dict[Any, Any] | None = None,
    params: AbstractParams | None = None,
    sort: Sequence[Any] | None = None,
    *,
    transformer: SyncItemsTransformer | None = None,
    additional_data: SyncAdditionalData | None = None,
    config: Config | None = None,
    **kwargs: Any,
) -> Any:
    query_filter = query_filter or {}

    return run_sync_flow(
        generic_flow(
            total_flow=flow_expr(lambda: collection.count_documents(query_filter)),
            limit_offset_flow=flow_expr(
                lambda raw_params: collection.find(
                    query_filter,
                    filter_fields,
                    skip=raw_params.offset,
                    limit=raw_params.limit,
                    sort=sort,
                    **kwargs,
                ).to_list()
            ),
            cursor_flow=lambda raw_params: _cursor_flow(
                collection,
                query_filter,
                filter_fields,
                sort,
                raw_params,
                **kwargs,
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


async def apaginate(
    collection: AsyncCollection[T],
    query_filter: dict[Any, Any] | None = None,
    filter_fields: dict[Any, Any] | None = None,
    params: AbstractParams | None = None,
    sort: Sequence[Any] | None = None,
    *,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    config: Config | None = None,
    **kwargs: Any,
) -> Any:
    query_filter = query_filter or {}

    return await run_async_flow(
        generic_flow(
            total_flow=flow_expr(lambda: collection.count_documents(query_filter)),
            limit_offset_flow=flow_expr(
                lambda raw_params: collection.find(
                    query_filter,
                    filter_fields,
                    skip=raw_params.offset,
                    limit=raw_params.limit,
                    sort=sort,
                    **kwargs,
                ).to_list()
            ),
            cursor_flow=lambda raw_params: _cursor_flow(
                collection,
                query_filter,
                filter_fields,
                sort,
                raw_params,
                **kwargs,
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


@flow
def _aggregate_flow(
    is_async: bool,
    collection: Collection[T] | AsyncCollection[T],
    aggregate_pipeline: list[dict[Any, Any]] | None = None,
    params: AbstractParams | None = None,
    *,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    aggregation_filter_end: int | Literal["auto"] | None = None,
    aggregation_pipeline_transformer: AggrPipelineTransformer | None = None,
    config: Config | None = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")
    aggregate_pipeline = aggregate_pipeline or []

    paginate_data = []
    if raw_params.limit is not None:
        paginate_data.append({"$limit": raw_params.limit + (raw_params.offset or 0)})
    if raw_params.offset is not None:
        paginate_data.append({"$skip": raw_params.offset})

    if aggregation_filter_end is not None:
        if aggregation_filter_end == "auto":
            aggregation_filter_end = get_mongo_pipeline_filter_end(aggregate_pipeline)
        transform_part = aggregate_pipeline[aggregation_filter_end:]
        aggregate_pipeline = aggregate_pipeline[:aggregation_filter_end]
        paginate_data.extend(transform_part)

    pipeline = [
        *aggregate_pipeline,
        _facet_stage(paginate_data, raw_params.include_total),
    ]

    if aggregation_pipeline_transformer is not None:
        pipeline = aggregation_pipeline_transformer(pipeline)

    cursor = yield collection.aggregate(pipeline)

    data, *_ = yield cursor.to_list(length=None)

    items = data["data"]
    total = _extract_total(data) if raw_params.include_total else None

    resolved_additional_data = yield from additional_data_flow(items, additional_data)

    page = yield from create_page_flow(
        items,
        params,
        total=total,
        transformer=transformer,
        additional_data=resolved_additional_data,
        config=config,
        async_=is_async,
    )

    return page


async def apaginate_aggregate(
    collection: AsyncCollection[T],
    aggregate_pipeline: list[dict[Any, Any]] | None = None,
    params: AbstractParams | None = None,
    *,
    transformer: ItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    aggregation_filter_end: int | Literal["auto"] | None = None,
    aggregation_pipeline_transformer: AggrPipelineTransformer | None = None,
    config: Config | None = None,
) -> Any:
    return await run_async_flow(
        _aggregate_flow(
            is_async=True,
            collection=collection,
            aggregate_pipeline=aggregate_pipeline or [],
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            aggregation_filter_end=aggregation_filter_end,
            aggregation_pipeline_transformer=aggregation_pipeline_transformer,
            config=config,
        )
    )


def paginate_aggregate(
    collection: Collection[T],
    aggregate_pipeline: list[dict[Any, Any]] | None = None,
    params: AbstractParams | None = None,
    *,
    transformer: SyncItemsTransformer | None = None,
    additional_data: SyncAdditionalData | None = None,
    aggregation_filter_end: int | Literal["auto"] | None = None,
    aggregation_pipeline_transformer: AggrPipelineTransformer | None = None,
    config: Config | None = None,
) -> Any:
    return run_sync_flow(
        _aggregate_flow(
            is_async=False,
            collection=collection,
            aggregate_pipeline=aggregate_pipeline or [],
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            aggregation_filter_end=aggregation_filter_end,
            aggregation_pipeline_transformer=aggregation_pipeline_transformer,
            config=config,
        )
    )
