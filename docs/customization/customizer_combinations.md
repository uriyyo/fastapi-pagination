from examples.pagination_databases import UsersIt's possible to combine multiple customizers in a single `CustomizedPage` call.

Here is an example:


```py
from typing import TypeVar

from fastapi import FastAPI, Query
from fastapi_pagination import Page, paginate, add_pagination
from fastapi_pagination.customization import (
    CustomizedPage,
    UseParamsFields,
    UseFieldsAliases,
    UseExcludedFields,
    UseIncludeTotal,
    UseName,
)

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseName("CustomPage"),
    UseIncludeTotal(False),
    UseExcludedFields("total", "pages"),
    UseParamsFields(
        size=Query(10, ge=1, le=1000, alias="pageSize"),
        page=Query(1, ge=1, alias="pageNumber"),
    ),
    UseFieldsAliases(
        items="content",
        size="pageSize",
        page="pageNumber",
    ),
]

# req: GET /nums
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```
