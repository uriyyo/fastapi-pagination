from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.sqlalchemy import paginate

app = FastAPI()
add_pagination(app)

engine = create_engine("sqlite:///.db", connect_args={"check_same_thread": False})


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

    class Config:
        orm_mode = True


@app.on_event("startup")
def on_startup():
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


@app.get("/users")
def get_users() -> CursorPage[UserOut]:
    with Session(engine) as session:
        return paginate(session, select(User))
