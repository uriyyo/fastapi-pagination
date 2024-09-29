## Own Page Model

First you need to implement your own `Page` model. This model should inherit from `fastapi_pagination.bases.AbstractPage`.
You will need to implement `create` abstract classmethod.

Also,you need to create your own `Params` model or to use one of the existing ones.

```py
from __future__ import annotations
from typing import TypeVar, Generic, Any, Sequence, Optional

from fastapi_pagination import Params
from fastapi_pagination.bases import AbstractPage, AbstractParams

T = TypeVar("T")


class MyPage(AbstractPage[T], Generic[T]):
    results: list[T]
    totalResults: int

    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any
    ) -> MyPage[T]:
        assert total is not None, "total must be provided"

        return cls(
            results=items,
            totalResults=total,
        )

page = MyPage[int].create(range(10), Params(), total=100)
print(page.model_dump_json(indent=4))
```

## Own Params Model

You can create your own `Params` model. In order to do that, you need to inherit from
`fastapi_pagination.bases.AbstractParams` and implement `to_raw_params` abstract method.

`to_raw_params` method should return an instance of `BaseRawParams` class. There are two types of `BaseRawParams`
`limit-offset` (`RawParams`) and `cursor` (`CursorRawParams`). Also, you can control if total value should 
be calculated by passing `include_total` attribute to `True` or `False`.


Here if example of `Params` model for `limit-offset` pagination:
```python
from typing import Annotated

from fastapi import Query
from fastapi_pagination.bases import AbstractParams, RawParams

class MyParams(AbstractParams):
    pageNumber: Annotated[int, Query(..., ge=1)]
    pageSize: Annotated[int, Query(..., ge=1, le=100)]

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.pageSize,
            offset=(self.pageNumber - 1) * self.pageSize,
            include_total=False,  # skip total calculation
        )
```

Here is an example of `Params` model for `cursor` pagination:
```python
from typing import Annotated

from fastapi import Query
from fastapi_pagination.bases import AbstractParams, CursorRawParams

class MyCursorParams(AbstractParams):
    cursor: Annotated[str, Query(...)]
    pageSize: Annotated[int, Query(..., ge=1, le=100)]

    def to_raw_params(self) -> CursorRawParams:
        return CursorRawParams(
            cursor=self.cursor,
            size=self.pageSize,
            include_total=False,  # skip total calculation
        )
```
