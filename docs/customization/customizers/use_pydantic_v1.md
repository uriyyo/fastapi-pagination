`UsePydanticV1` is a customizer that allows  you to convert Pydantic v2 models to Pydantic v1 models
for compatibility purposes. This is useful when you still have parts of your codebase that rely on Pydantic v1
and you want to use FastAPI Pagination without migrating everything to Pydantic v2 at once

```py
from random import random
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UsePydanticV1

from pydantic.v1 import BaseModel


class Item(BaseModel):
    id: int
    score: float = 0.0


app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UsePydanticV1(),
]


# req: GET /items?size=5&page=2
@app.get("/items")
async def get_items() -> CustomPage[Item]:
    return paginate(
        [Item(id=id_, score=random()) for id_ in range(1_000)]
    )
```
