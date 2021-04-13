# FastAPI Pagination

[![License](https://img.shields.io/badge/License-MIT-lightgrey)](/LICENSE)
[![codecov](https://github.com/uriyyo/fastapi-pagination/workflows/Test/badge.svg)](https://github.com/uriyyo/fastapi-pagination/actions)
[![codecov](https://codecov.io/gh/uriyyo/fastapi-pagination/branch/main/graph/badge.svg?token=QqIqDQ7FZi)](https://codecov.io/gh/uriyyo/fastapi-pagination)
[![Downloads](https://pepy.tech/badge/fastapi-pagination)](https://pepy.tech/project/fastapi-pagination)
[![PYPI](https://img.shields.io/pypi/v/fastapi-pagination)](https://pypi.org/project/fastapi-pagination/)
[![PYPI](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
* [ormar](http://github.com/collerek/ormar)
* [orm](https://github.com/encode/orm)
* [tortoise](https://github.com/tortoise/tortoise-orm)

## Example

```python
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()


class User(BaseModel):
    name: str
    surname: str


users = [
    User(name='Yurii', surname='Karabas'),
    # ...
]


@app.get('/users', response_model=Page[User])
async def get_users():
    return paginate(users)


add_pagination(app)
```
