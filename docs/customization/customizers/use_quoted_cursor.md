`UseQuotedCursor` is a customizer that allows you to specify whether the cursor should be quoted or not.

Here is an example of how to use it:

```py
from typing import TypeVar

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, Session, mapped_column

from fastapi_pagination import set_params, set_page
from fastapi_pagination.customization import CustomizedPage, UseQuotedCursor
from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///:memory:")


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(default=None, primary_key=True)
    name: Mapped[str] = mapped_column()


with Session(engine) as session:
    Base.metadata.create_all(session.bind)

    session.add_all([User(name=f"User-{i}") for i in range(1_000)])
    session.commit()

T = TypeVar("T")

CursorPageNotQuotedCursor = CustomizedPage[
    CursorPage[T],
    UseQuotedCursor(False),
]

set_page(CursorPageNotQuotedCursor[User])
cursor = None

for i in range(1, 6):
    print(f"Page {i}")
    set_params(CursorParams(size=2, cursor=cursor))
    page = paginate(session, select(User).order_by(User.id))
    cursor = page.next_page
    print(page.model_dump_json(indent=4))
    print()
```
