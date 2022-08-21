# Integrations

When paginating data from an external source such as a database, it may be tempting to query all of the data you need, and pass the result into `fastapi_pagination.paginate`. However, for large datasets, this will result in a significantly slower response since a lot of un-necessary work is being done to query data that won't ever be returned.

In order to avoid this issue, fastapi_pagination provides several integrations with popular ORMs.

## SQLAlchemy

This integration provides support for the [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) ORM.

A minimal example of using the SQLAlchemy integration can be seen below:

```python
from typing import Iterator, Any

import faker
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=True, autoflush=True, bind=engine)

Base = declarative_base(bind=engine)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

Base.metadata.create_all()

class UserOut(BaseModel):
    name: str
    email: str
    id: int

    class Config:
        orm_mode = True

app = FastAPI()

@app.on_event("startup")
def on_startup() -> None:
    session = SessionLocal()

    session.add_all([User(name=faker.name(), email=faker.email()) for _ in range(100)])

    session.flush()
    session.close()

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/", response_model=Page[UserOut])
def get_users(db: Session = Depends(get_db)) -> Any:
    return paginate(db.query(User))

add_pagination(app)
```

When calling the paginate function, instead of passing in the raw data, instead an SQLAlchemy query is passed. Paginate then modifies the query to apply pagination to the query itself, preventing the overhead of the SQL engine from querying more results than necessary.

```python
@app.get("/users/", response_model=Page[UserOut])
def get_users(db: Session = Depends(get_db)) -> Any:
    return paginate(db.query(User))
```

A more complete example of SQLAlchemy integration can be seen [here](https://github.com/uriyyo/fastapi-pagination/blob/main/examples/pagination_sqlalchemy.py)

## GINO

This integration provides support for [GINO](https://github.com/python-gino/gino).

A complete example of the GINO integration can be seen [here](https://github.com/uriyyo/fastapi-pagination/blob/main/examples/pagination_gino.py)

## Databases

This integration provides support for [databases](https://github.com/encode/Databases).

A complete example of the Databases integration can be seen [here](https://github.com/uriyyo/fastapi-pagination/blob/main/examples/pagination_databases.py)

## Ormar

This integration provides support for the [ormar](http://github.com/collerek/ormar) ORM.

A complete example of the ormar integration can be seen [here](https://github.com/uriyyo/fastapi-pagination/blob/main/examples/pagination_ormar.py).

## ORM

This integration provides support for [ORM](https://github.com/encode/orm).

A complete example of this integration can be seen [here](https://github.com/uriyyo/fastapi-pagination/blob/main/examples/pagination_orm.py).

## Tortoise

This integration provides support for the [Tortoise ORM](https://github.com/tortoise/tortoise-orm).

A complete example of this integration can be seen [here](https://github.com/uriyyo/fastapi-pagination/blob/main/examples/pagination_tortoise.py)
