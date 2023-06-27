from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from typing import Any, Iterator

import uvicorn
from faker import Faker
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

faker = Faker()

engine = create_async_engine("sqlite+aiosqlite:///.db")


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
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session = AsyncSession(engine)

    async with session.begin():
        session.add_all([User(name=faker.name(), email=faker.email()) for _ in range(100)])
    yield


async def get_db() -> Iterator[AsyncSession]:
    db = AsyncSession(engine)
    async with db.begin():
        yield db

app = FastAPI(lifespan=lifespan)
add_pagination(app)


@app.post("/users")
async def create_user(user_in: UserIn, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = User(name=user_in.name, email=user_in.email)
    db.add(user)
    await db.commit()

    return UserOut.from_orm(user)


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users(db: AsyncSession = Depends(get_db)) -> Any:
    return await paginate(db, select(User))


if __name__ == "__main__":
    uvicorn.run("pagination_sqlalchemy:app")
