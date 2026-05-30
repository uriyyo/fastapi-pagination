`UseFlattenPage` transforms a page class into a Pydantic root model.

The original page is still created first, so pagination params and pagination logic work the same way.
After that, `UseFlattenPage` reads one attribute from the created page and uses it as the root value.
By default, it uses the `items` field.

For the default `Page`, it changes the response shape from a page object:

```json
{
  "items": [6, 7, 8, 9, 10],
  "total": 1000,
  "page": 2,
  "size": 5,
  "pages": 200
}
```

to a plain list:

```json
[6, 7, 8, 9, 10]
```

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseFlattenPage

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseFlattenPage(),
]


# req: GET /nums?size=5&page=2
# rsp: [6, 7, 8, 9, 10]
@app.get("/nums")
async def get_nums() -> CustomPage[int]:
    return paginate(range(1, 1_001))
```

You can also pass `field` explicitly. It must refer to a list-valued field from the generated page.

```py
CustomPage = CustomizedPage[
    Page[T],
    UseFlattenPage(field="items"),
]
```
