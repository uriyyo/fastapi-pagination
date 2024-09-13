from contextlib import asynccontextmanager
from typing import Any, Iterator

import uvicorn
from faker import Faker
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, Session, mapped_column

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

faker = Faker()

engine = create_engine("sqlite:///.db")


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    name: Mapped[str]
    email: Mapped[str]

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, default=None)


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


@asynccontextmanager
async def lifespan(_: Any) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = Session(engine)

    with session.begin():
        session.add_all([User(name=faker.name(), email=faker.email()) for _ in range(100)])
    yield


app = FastAPI(lifespan=lifespan)
add_pagination(app)


def get_db() -> Iterator[Session]:
    with Session(engine) as db, db.begin():
        yield db


@app.post("/users")
def create_user(user_in: UserIn, db: Session = Depends(get_db)) -> UserOut:
    user = User(name=user_in.name, email=user_in.email)
    db.add(user)
    db.commit()

    return UserOut.from_orm(user)


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
def get_users(db: Session = Depends(get_db)) -> Any:
    return paginate(db, select(User))


if __name__ == "__main__":
    uvicorn.run(app)
