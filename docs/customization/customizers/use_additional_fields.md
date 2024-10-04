`UseAdditionalFields` allows you to add additional fields to a `Page` class.

```py
from typing import TypeVar

from fastapi import FastAPI
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields

app = FastAPI()
add_pagination(app)

T = TypeVar("T")

CustomPage = CustomizedPage[
    Page[T],
    UseAdditionalFields(
        # add a field `user` with type `str`
        user=str,
        # add a field `is_admin` with type `bool`
        # and default value `False`
        is_admin=(bool, False),
    ),
]

# req: GET /nums?size=5&page=2
# req: GET /nums?size=5&page=2&is_admin=true
@app.get("/nums")
async def get_nums(is_admin: bool = False) -> CustomPage[int]:
    return paginate(
        range(1_000),
        additional_data={
            "user": "Tony Stark",
            "is_admin": is_admin,
        }
    )
```
