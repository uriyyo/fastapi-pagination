`fastapi_pagination.ext.peewee.paginate` allows you to paginate `peewee` queries easily.
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

* `query` - is the query that you want to paginate, it can be either a select query or a Model class.
* `subquery_count` - is a boolean that indicates if the count query should be executed as a subquery or not.
* `count_query` - is a query that will be used to count the total number of rows, if not provided, it will be generated automatically.
* `unique` - is a boolean indicates if `unique` should be called on result rows or not.
* `unwrap_mode` - indicates how to unwrap the result rows, it can be either `auto`, `legacy`, `unwrap`, `no-unwrap`.

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

### `subquery_count` param

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
User.create(name="John", age=25)

set_page(Page[User])
set_params(Params(page=1, size=10))

print("subquery_count=False")
paginate(User.select(), subquery_count=False)

print("subquery_count=True")
paginate(User.select(), subquery_count=True)
```

### `count_query` param

```py
from peewee import Model, TextField, IntegerField, SqliteDatabase, fn

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

page = paginate(
    User.select().order_by(User.id),
    count_query=User.select(fn.COUNT()).where(User.age > 20),
)
print(page)
```

### `unwrap_mode` param

`peewee` `unwrap_mode` allows you to control how to unwrap result rows before passing them to items transformer and page creation.

`unwrap_mode` can be set to one of the following values:

* `None` - will use `auto` mode for default queries.
* `"auto"` - will unwrap only in case if you are selecting single model.
* `"legacy"` - will use old behavior, where row will be unwrapped if it contains only one element.
* `"unwrap"` - will always unwrap row, even if it contains multiple elements.
* `"no-unwrap"` - will never unwrap row, even if it contains only one element.

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
User.create(name="John", age=25)

set_params(Params(page=1, size=10))

print('unwrap_mode="auto"')
set_page(Page[User])
page = paginate(User.select(), unwrap_mode="auto")
print(page)

print('unwrap_mode="no-unwrap"')
set_page(Page[User])
page = paginate(User.select(), unwrap_mode="no-unwrap")
print(page)
```

### `unique` param

When using `joinedload` or similar eager loading, you may get duplicate rows. The `unique` parameter ensures duplicate rows are removed while preserving order.

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
User.create(name="John", age=25)

set_page(Page[User])
set_params(Params(page=1, size=10))

print("unique=True (default)")
page = paginate(User.select(), unique=True)
print(page)

print("unique=False")
page = paginate(User.select(), unique=False)
print(page)
```
