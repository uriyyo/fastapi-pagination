# FastAPI Pagination

FastAPI Pagination - easy to use pagination for FastAPI.

Example of code and generated OpenAPI specification.

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

from fastapi_pagination import Page, pagination_params
from fastapi_pagination.paginator import paginate

app = FastAPI()


class User(BaseModel):
    name: str
    surname: str


users = [
    User(name='Yurii', surname='Karabas'),
    # ...
]


@app.get(
    '/users',
    response_model=Page[User],
    dependencies=[Depends(pagination_params)],
)
async def get_users():
    return paginate(users) 
```

![OpenAPI](/images/openapi_example.png)

## Available integrations

* [sqlalchemy](https://github.com/sqlalchemy/sqlalchemy)
* [gino](https://github.com/python-gino/gino)
* [databases](https://github.com/encode/databases)
* [orm](https://github.com/encode/orm)
* [tortoise](https://github.com/tortoise/tortoise-orm)

To see fully working examples, please visit this
[link](https://github.com/uriyyo/fastapi-pagination/tree/main/examples).

## Installation

```bash
# Basic version
pip install fastapi-pagination

# All available integrations
pip install fastapi-pagination[all]
```