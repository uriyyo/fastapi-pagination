`fastapi_pagination.ext.peewee.paginate` allows you to paginate `peewee` queries.
It can work for both `sync` and `async` peewee databases.

!!! note
    Async pagination (`apaginate`) requires peewee >= 4.0.0 with `playhouse.pwasyncio` and `greenlet`.
    Install with: `uv pip install fastapi-pagination[peewee]`.
    See [Peewee Async Documentation](https://docs.peewee-orm.com/en/latest/peewee/asyncio.html) for more details.

!!! note
    Cursor pagination is not currently supported, [as it is only available via the Playhouse Postgresql extension](https://docs.peewee-orm.com/en/2.10.2/peewee/playhouse.html#server-side-cursors).

## Example: FastAPI

```py
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from peewee import Model, TextField, IntegerField, SqliteDatabase

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.peewee import paginate

db = SqliteDatabase("example.db")


class User(BaseModel):
    name: str
    age: int


class UserModel(Model):
    name = TextField()
    age = IntegerField()

    class Meta:
        database = db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.create_tables([UserModel])
    for name, age in [("John", 25), ("Jane", 30), ("Bob", 20)]:
        UserModel.get_or_create(name=name, age=age)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/users", response_model=Page[User])
async def get_users(params: Params = Depends()):
    set_page(Page[User])
    return paginate(UserModel.select(), params)
```

## Details

`paginate` accepts the following `peewee` related arguments:

* `db` - Database instance. Required for raw SQL queries, optional otherwise (extracted from query's model).
* `query` - is the query that you want to paginate, it can be either a Peewee query or a raw SQL string.
* `prefetch` - A tuple of queries for eager loading related records (avoids N+1 query problems).

### Sync Usage

```py
from peewee import Model, TextField, IntegerField, SqliteDatabase

from fastapi_pagination import set_params, set_page, Page, Params
from fastapi_pagination.ext.peewee import paginate

db = SqliteDatabase(":memory:")


class User(Model):
    name = TextField()
    age = IntegerField()

    class Meta:
        database = db


db.create_tables([User])

for name, age in [("John", 25), ("Jane", 30), ("Bob", 20)]:
    User.create(name=name, age=age)

set_page(Page[User])
set_params(Params(page=1, size=10))

page = paginate(User.select().order_by(User.id))
print(page)
```

### Async Usage

```py
from peewee import Model, TextField, IntegerField
from playhouse.pwasyncio import AsyncSqliteDatabase, greenlet_spawn

from fastapi_pagination import set_params, set_page, Page, Params
from fastapi_pagination.ext.peewee import apaginate

db = AsyncSqliteDatabase(":memory:")


class User(Model):
    name = TextField()
    age = IntegerField()

    class Meta:
        database = db


async def get_users():
    await greenlet_spawn(db.create_tables, [User])
    for name, age in [("John", 25), ("Jane", 30), ("Bob", 20)]:
        await greenlet_spawn(User.create, name=name, age=age)

    set_page(Page[User])
    set_params(Params(page=1, size=10))

    page = await apaginate(User.select().order_by(User.id))
print(page)
```

### Prefetch Usage

```py
from peewee import Model, TextField, IntegerField, ForeignKeyField

from fastapi_pagination import set_params, set_page, Page, Params
from fastapi_pagination.ext.peewee import paginate

db = SqliteDatabase(":memory:")


class User(Model):
    name = TextField()

    class Meta:
        database = db


class Order(Model):
    user = ForeignKeyField(User, backref="orders")
    name = TextField()

    class Meta:
        database = db


db.create_tables([User, Order])

set_page(Page[User])
set_params(Params(page=1, size=10))

page = paginate(User.select(), prefetch=(Order.select(),))
for user in page.items:
    print(user.name, [order.name for order in user.orders])
```
