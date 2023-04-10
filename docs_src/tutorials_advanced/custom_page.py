from typing import TypeVar, Generic, Sequence, Optional, Any

from fastapi import Query
from pydantic import BaseModel
from typing_extensions import Self

from fastapi_pagination.bases import AbstractParams, AbstractPage, RawParams


class JSONAPIParams(BaseModel, AbstractParams):
    offset: int = Query(1, ge=1, alias="page[offset]")
    limit: int = Query(10, ge=1, le=100, alias="page[limit]")

    def to_raw_params(self) -> RawParams:
        return RawParams(limit=self.limit, offset=self.offset)


class JSONAPIPageInfoMeta(BaseModel):
    total: int


class JSONAPIPageMeta(BaseModel):
    page: JSONAPIPageInfoMeta


T = TypeVar("T")


class JSONAPIPage(AbstractPage[T], Generic[T]):
    data: Sequence[T]
    meta: JSONAPIPageMeta

    __params_type__ = JSONAPIParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> Self:
        assert isinstance(params, JSONAPIParams)
        assert total is not None

        return cls(
            data=items,
            meta={"page": {"total": total}},
            **kwargs,
        )
