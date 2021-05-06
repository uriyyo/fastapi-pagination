from typing import Any, Mapping, Optional

from pydantic import BaseModel, Field
from starlette.requests import URL

from ..api import request

_link_field = Field(example="/api/v1/users?limit=1&offset1")


class Links(BaseModel):  # type: ignore
    first: str = _link_field
    last: str = _link_field
    self: str = _link_field
    next: Optional[str] = _link_field
    prev: Optional[str] = _link_field


def _only_path(url: URL) -> str:
    if not url.query:
        return str(url.path)

    return f"{url.path}?{url.query}"


def _update_path(url: URL, to_update: Optional[Mapping[str, Any]]) -> Optional[str]:
    if to_update is None:
        return None

    return _only_path(url.include_query_params(**to_update))


def create_links(
    first: Mapping[str, Any],
    last: Mapping[str, Any],
    next: Optional[Mapping[str, Any]],
    prev: Optional[Mapping[str, Any]],
) -> Links:
    req = request()
    url = req.url

    return Links(
        self=_only_path(url),
        first=_update_path(url, first),
        last=_update_path(url, last),
        next=_update_path(url, next),
        prev=_update_path(url, prev),
    )


__all__ = ["Links", "create_links"]
