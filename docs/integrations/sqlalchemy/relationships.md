Different relationship loading types can be used together with `fastapi-pagination` to paginate SQLAlchemy relationships.

Here is an example of how to use `joinedload`, `subqueryload`, and `selectinload` with `fastapi-pagination`:

```py
from __future__ import annotations

from typing import Any
from pydantic import BaseModel

from sqlalchemy import ForeignKey, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    Mapped,
    Session,
    mapped_column,
    relationship,
    joinedload,
    selectinload,
    subqueryload,
)

from fastapi_pagination import Page, set_params, set_page
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal
from fastapi_pagination.ext.sqlalchemy import paginate

engine = create_engine("sqlite:///:memory:")


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(default=None, primary_key=True)

    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()

    marks: Mapped[list[Mark]] = relationship(back_populates="user", default_factory=list)


class Mark(Base):
    __tablename__ = "marks"

    id: Mapped[int] = mapped_column(default=None, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), default=None)
    mark: Mapped[int] = mapped_column()

    user: Mapped[User] = relationship(back_populates="marks", default=None)

    
class MarkOut(BaseModel):
    id: int
    mark: int


class UserOut(BaseModel):
    id: int
    name: str
    age: int
    marks: list[MarkOut]


with Session(engine) as session:
    Base.metadata.create_all(session.bind)

    session.add_all(
        [
            User(
                name="John",
                age=25,
                marks=[
                    Mark(mark=10),
                    Mark(mark=20),
                ],
            ),
            User(
                name="Jane",
                age=30,
                marks=[
                    Mark(mark=30),
                    Mark(mark=40),
                    Mark(mark=50),
                ],
            ),
            User(
                name="Bob",
                age=20,
                marks=[
                    Mark(mark=60),
                ],
            ),
        ],
    )
    session.commit()

CustomPage = CustomizedPage[Page[UserOut], UseIncludeTotal(False)]

set_page(CustomPage)
set_params(CustomPage.__params_type__(size=1, page=2))

def run_pagination(type_: str, load: Any) -> None:
    print(f"relationship load type: {type_}")
    page = paginate(session, select(User).options(load(User.marks)))
    print(page.model_dump_json(indent=4))
    print()

run_pagination("joinedload", joinedload)
run_pagination("subqueryload", subqueryload)
run_pagination("selectinload", selectinload)
```