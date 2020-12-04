# FastAPI Pagination

## Installation

```bash
# Basic version
pip install fastapi-pagination

# All available integrations
pip install fastapi-pagination[all]
```

Available integrations:
* [sqlalchemy](https://github.com/sqlalchemy/sqlalchemy)
* [gino](https://github.com/python-gino/gino)
* [databases](https://github.com/encode/databases)
* [orm](https://github.com/encode/orm)
* [tortoise](https://github.com/tortoise/tortoise-orm)


## Example

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

from fastapi_pagination import PaginationParams, Page
from fastapi_pagination.paginator import paginate

app = FastAPI()

class User(BaseModel):
    name: str
    surname: str

users = [
    User(name='Yurii', surname='Karabas'),
    # ...
]

@app.get('/users', response_model=Page[User])
async def get_users(params: PaginationParams = Depends()):
    return paginate(users, params)
```

## Example using implicit params

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

@app.get('/users', response_model=Page[User], dependencies=[Depends(pagination_params)])
async def get_users():
    return paginate(users)
```
