from typing import Any

import uvicorn
from faker import Faker
from fastapi import FastAPI
from gino_starlette import Gino
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.gino import paginate

faker = Faker()

db = Gino(
    dsn="postgresql://postgres:postgres@localhost:5432",
    use_connection_for_request=True,
)


class User(db.Model):  # type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


@asynccontextmanager
async def lifespan(_: Any) -> None:
    await db.gino.drop_all()
    await db.gino.create_all()

    for _ in range(100):
        await User.create(
            name=faker.name(),
            email=faker.email(),
        )
    yield


app = FastAPI(lifespan=lifespan)
db.init_app(app)


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    return await User.create(**user_in.dict())


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return await paginate(User.query)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_gino:app")
