<h1 align="center">
<img alt="logo" src="https://raw.githubusercontent.com/uriyyo/fastapi-pagination/main/docs/img/logo.png">
</h1>

<div align="center">
<img alt="license" src="https://img.shields.io/badge/License-MIT-lightgrey">
<img alt="test" src="https://github.com/uriyyo/fastapi-pagination/workflows/Test/badge.svg">
<img alt="codecov" src="https://codecov.io/gh/uriyyo/fastapi-pagination/branch/main/graph/badge.svg?token=QqIqDQ7FZi">
<a href="https://pepy.tech/project/fastapi-pagination"><img alt="downloads" src="https://pepy.tech/badge/fastapi-pagination"></a>
<a href="https://pypi.org/project/fastapi-pagination"><img alt="pypi" src="https://img.shields.io/pypi/v/fastapi-pagination"></a>
<img alt="black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
</div>

## Introduction

`fastapi-pagination` is a library that provides pagination feature for [FastAPI](https://fastapi.tiangolo.com/)
applications.

----

For more information about library please see [documentation](https://uriyyo-fastapi-pagination.netlify.app/).

---

## Installation

```bash
pip install fastapi-pagination
```

## Quickstart

All you need to do is to use `Page` class as a return type for your endpoint and call `paginate` function
on data you want to paginate.

```py
from fastapi import FastAPI
from pydantic import BaseModel, Field

# import all you need from fastapi-pagination
from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()  # create FastAPI app


class UserOut(BaseModel):  # define your model
    name: str = Field(..., example="Steve")
    surname: str = Field(..., example="Rogers")


users = [  # create some data
    # ...
]


@app.get('/users', response_model=Page[UserOut])  # use Page[UserOut] as response model
async def get_users():
    return paginate(users)  # use paginate function to paginate your data


add_pagination(app)  # important! add pagination to your app
```

Please, be careful when you work with databases, because default `paginate` will require to load all data in memory.

For instance, if you use `SQLAlchemy` you can use `paginate` from `fastapi_pagination.ext.sqlalchemy` module.

```py
from fastapi_pagination.ext.sqlalchemy import paginate


@app.get('/users', response_model=Page[UserOut])
def get_users(db: Session = Depends(get_db)):
    return paginate(db.query(User).order_by(User.created_at))
```

For `SQLAlchemy 2.0 style` you can use `paginate` from `fastapi_pagination.ext.sqlalchemy_future` module.

```py
from sqlalchemy import select
from fastapi_pagination.ext.sqlalchemy_future import paginate


@app.get('/users', response_model=Page[UserOut])
def get_users(db: Session = Depends(get_db)):
    return paginate(db, select(User).order_by(User.created_at))
```

Currently, `fastapi-pagination` supports:

| Library                                                                                     | `paginate` function                                 | 
|---------------------------------------------------------------------------------------------|-----------------------------------------------------|
| [SQLAlchemy](https://docs.sqlalchemy.org/en/14/orm/quickstart.html)                         | `fastapi_pagination.ext.sqlalchemy.paginate`        |
| [SQLAlchemy 2.0 style](https://docs.sqlalchemy.org/en/14/changelog/migration_20.html)       | `fastapi_pagination.ext.sqlalchemy_future.paginate` |
| [Async SQLAlchemy 2.0 style](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html) | `fastapi_pagination.ext.async_sqlalchemy.paginate`  |
| [SQLModel](https://sqlmodel.tiangolo.com/)                                                  | `fastapi_pagination.ext.sqlmodel.paginate`          |
| [Async SQLModel](https://sqlmodel.tiangolo.com/)                                            | `fastapi_pagination.ext.async_sqlmodel.paginate`    |
| [AsyncPG](https://magicstack.github.io/asyncpg/current/)                                    | `fastapi_pagination.ext.asyncpg.paginate`           |
| [Databases](https://www.encode.io/databases/)                                               | `fastapi_pagination.ext.databases.paginate`         |
| [Django ORM](https://docs.djangoproject.com/en/3.2/topics/db/queries/)                      | `fastapi_pagination.ext.django.paginate`            |
| [GINO](https://python-gino.org/)                                                            | `fastapi_pagination.ext.gino.paginate`              |
| [ORM](https://www.encode.io/orm/)                                                           | `fastapi_pagination.ext.orm.paginate`               |
| [ormar](https://collerek.github.io/ormar/)                                                  | `fastapi_pagination.ext.ormar.paginate`             |
| [Piccolo](https://piccolo-orm.readthedocs.io/en/latest/)                                    | `fastapi_pagination.ext.piccolo.paginate`           |
| [Pony ORM](https://docs.ponyorm.org/)                                                       | `fastapi_pagination.ext.pony.paginate`              |
| [Tortoise ORM](https://tortoise-orm.readthedocs.io/en/latest/)                              | `fastapi_pagination.ext.tortoise.paginate`          |
| [Beanie](https://roman-right.github.io/beanie/)                                             | `fastapi_pagination.ext.beanie.paginate`            |
| [PyMongo](https://pymongo.readthedocs.io/en/stable/)                                        | `fastapi_pagination.ext.pymongo.paginate`           |
| [MongoEngine](https://docs.mongoengine.org/)                                                | `fastapi_pagination.ext.mongoengine.paginate`       |
| [Motor](https://motor.readthedocs.io/en/stable/)                                            | `fastapi_pagination.ext.motor.paginate`             |


---

Code from `Quickstart` will generate OpenAPI schema as bellow:

<div align="center">
<img alt="app-example" src="https://raw.githubusercontent.com/uriyyo/fastapi-pagination/main/docs/img/example.jpeg">
</div>
