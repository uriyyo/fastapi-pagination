__all__ = [
    "AggrPipelineTransformer",
]

from collections.abc import Callable
from typing import Any

AggrPipelineTransformer = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]


def _facet_stage(data: list[dict[str, Any]], include_total: bool) -> dict[str, Any]:
    facet: dict[str, Any] = {"data": data}
    if include_total:
        facet["metadata"] = [{"$count": "total"}]

    return {"$facet": facet}


def _extract_total(data: dict[str, Any]) -> int:
    try:
        return data["metadata"][0]["total"]
    except (KeyError, IndexError):
        return 0
