`fastapi_pagination.ext.sqlalchemy.paginate` allows you to paginate `sqlalchemy` queries easily.
It can work for both `sync` and `async` SQLAlchemy engines.

`paginate` accepts the following `sqlalchemy` related arguments:

* `conn` - can be either a `Connection` or `Session` object that allows you to execute the query.
* `query` - is the query that you want to paginate, it can be either a default select query, raw text query, or a from statement construction.
* `subquery_count` - is a boolean that indicates if the count query should be executed as a subquery or not.
* `count_query` - is a query that will be used to count the total number of rows, if not provided, it will be generated automatically.
* `unique` - is a boolean indicates if `unique` should be called on a result rows or not, might be required when you have `joinedload` relationships.
* `unwrap_mode` - indicates how to unwrap the result rows, it can be either `auto`, `legacy`, `unwrap`, `no-unwrap`.

## `subquery_count` param

```py
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, Session, mapped_column

from fastapi_pagination import set_params, set_page, Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///:memory:")


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(default=None, primary_key=True)

    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()


with Session(engine) as session:
    Base.metadata.create_all(session.bind)

    session.add_all(
        [
            User(name="John", age=25),
            User(name="Jane", age=30),
            User(name="Bob", age=20),
        ],
    )
    session.commit()

set_page(Page[User])
set_params(Params(size=10))

print("subquery_count=False")
paginate(session, select(User), subquery_count=False)

print("subquery_count=True")
paginate(session, select(User), subquery_count=True)
```

## `count_query` param

```py
from sqlalchemy import create_engine, select, literal
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, Session, mapped_column

from fastapi_pagination import set_params, set_page, Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///:memory:")


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(default=None, primary_key=True)

    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()


with Session(engine) as session:
    Base.metadata.create_all(session.bind)

    session.add_all(
        [
            User(name="John", age=25),
            User(name="Jane", age=30),
            User(name="Bob", age=20),
        ],
    )
    session.commit()

set_page(Page[User])
set_params(Params(size=10))

page = paginate(
    session,
    select(User),
    count_query=select(literal(1_000)),
)
print(page.model_dump_json(indent=4))
```

## `unwrap_mode` param

`sqlalchemy` `unwrap_mode` allows you to control how to unwrap result rows before passing them to items transformer
and page creation.

`unwrap_mode` can be set to one of the following values:

* `None` - will use `auto` mode for default queries, and `legacy` for `text` and `from_statement` queries.
* `"auto"` - will unwrap only in case if you are selecting single model.
* `"legacy"` - will use old behavior, where row will be unwrapped if it contains only one element.
* `"unwrap"` - will always unwrap row, even if it contains multiple elements.
* `"no-unwrap"` - will never unwrap row, even if it contains only one element.

```py
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, Session, mapped_column

from fastapi_pagination import set_params, set_page, Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///:memory:")


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(default=None, primary_key=True)
    name: Mapped[str] = mapped_column()


class UserName(BaseModel):
    name: str


with Session(engine) as session:
    Base.metadata.create_all(session.bind)
    session.add(User(name="John"))
    session.commit()

set_params(Params(size=10))

print('unwrap_mode="auto"')
set_page(Page[UserName])
page = paginate(
    session,
    select(User.name),
    unwrap_mode="auto",
)
print(page.model_dump_json(indent=4))
print()

print('unwrap_mode="legacy"')
set_page(Page[str])
page = paginate(
    session,
    select(User.name),
    unwrap_mode="legacy",
)
print(page.model_dump_json(indent=4))
print()

print('unwrap_mode="unwrap"')
set_page(Page[str])
page = paginate(
    session,
    select(User.name),
    unwrap_mode="unwrap",
)
print(page.model_dump_json(indent=4))
print()

print('unwrap_mode="no-unwrap"')
set_page(Page[UserName])
page = paginate(
    session,
    select(User.name),
    unwrap_mode="no-unwrap",
)
print(page.model_dump_json(indent=4))
print()
```