# Page-Based Pagination

## What is Page-Based Pagination?

Page-Based pagination divides the dataset into pages and allows navigation through these pages.
You specify the page number and the number of items per page. Usually, the first page is `1` 
and names `page` and `size` are used for the page number and the number of items per page, respectively.

## Advantages

- Intuitive for users as it mimics the concept of pages in a book.
- Easy to implement and understand.

## Disadvantages

- Can be inefficient for large datasets.
- May lead to inconsistent results if the data changes frequently.

Example:

```py
from fastapi_pagination import paginate, set_page, set_params
from fastapi_pagination.default import Page, Params

set_page(Page[int])
set_params(Params(page=2, size=10))

page = paginate([*range(100)])
print(page.model_dump_json(indent=4))
```

# Limit-Offset Pagination

## What is Limit-Offset Pagination?

Limit-Offset pagination is a technique where you specify the number of records retrieve `limit` and
the starting point `offset`. This method is straightforward and easy to implement.

## Advantages

- Simple to understand and implement.
- Works well for small datasets.

## Disadvantages

- Inefficient for large datasets as the offset increases.
- Can lead to inconsistent results if the data changes frequently.

Example:

```py
from fastapi_pagination import paginate, set_page, set_params
from fastapi_pagination.limit_offset import LimitOffsetParams, LimitOffsetPage

set_page(LimitOffsetPage[int])
set_params(LimitOffsetParams(limit=10, offset=5))

page = paginate([*range(100)])
print(page.model_dump_json(indent=4))
```

# Cursor-Based Pagination

## What is Cursor-Based Pagination?

Cursor-Based pagination uses a cursor (a unique identifier) to keep track of the current position in the dataset.
This method is more efficient for large datasets and provides consistent results.

## Advantages

- Efficient for large datasets.
- Provides consistent results even if the data changes.

## Disadvantages

- More complex to implement.
- Requires a unique and sequential field to act as the cursor.

```py
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fastapi_pagination import set_params, set_page
from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///:memory:")

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()


class UserOut(BaseModel):
    id: int
    name: str
    age: int


with engine.begin() as conn:
    Base.metadata.drop_all(conn)
    Base.metadata.create_all(conn)

with Session(engine) as session:
    session.add_all(
        [
            User(name="John", age=25),
            User(name="Jane", age=30),
            User(name="Bob", age=20),
        ],
    )
    session.commit()

set_page(CursorPage[UserOut])
set_params(CursorParams(size=10))

page = paginate(session, select(User).order_by(User.id))
print(page.model_dump_json(indent=4))
```

# Conclusion

Each pagination technique has its own advantages and disadvantages. The choice of technique depends on the specific requirements of your application, such as dataset size, performance needs, and consistency requirements.
