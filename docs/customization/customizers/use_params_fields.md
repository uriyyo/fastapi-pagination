`UseParamsFields` allows you to change fields of `Page` `Params` class.

For instance, you can change the names of fields and change default `size`
you can do it by using `UseParamsFields` customizer:

```py
from typing import TypeVar

from fastapi import FastAPI, Query
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseParamsFields(
        size=Query(5, ge=1, le=100, alias="pageSize"),
        page=Query(1, ge=1, alias="pageNumber"),
    ),
]

# req: GET /nums?pageSize=5&pageNumber=2
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1_000))
```
