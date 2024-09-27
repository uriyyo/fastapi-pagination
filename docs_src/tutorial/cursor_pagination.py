from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage
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


@asynccontextmanager
async def lifespan(_: Any) -> AsyncIterator[None]:
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

    yield


app = FastAPI(lifespan=lifespan)
add_pagination(app)


# req: GET /users
@app.get("/users")
def get_users() -> CursorPage[UserOut]:
    with Session(engine) as session:
        return paginate(session, select(User).order_by(User.id))
