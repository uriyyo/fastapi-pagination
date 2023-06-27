from contextlib import asynccontextmanager
from typing import Any

import sqlalchemy
import uvicorn
from databases import Database
from faker import Faker
from fastapi import FastAPI
from orm import Integer, Model, String
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.orm import paginate

faker = Faker()

metadata = sqlalchemy.MetaData()
db = Database("sqlite:///.db")


class User(Model):
    __tablename__ = "users"
    __database__ = db
    __metadata__ = metadata

    id = Integer(primary_key=True)
    name = String(max_length=100)
    email = String(max_length=100)


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


@asynccontextmanager
async def lifespan(_: Any) -> None:
    engine = sqlalchemy.create_engine(str(db.url))
    metadata.drop_all(engine)
    metadata.create_all(engine)

    await db.connect()

    for _ in range(100):
        await User.objects.create(
            name=faker.name(),
            email=faker.email(),
        )
    yield
    await db.disconnect()


app = FastAPI(lifespan=lifespan)


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    return await User.objects.create(**user_in.dict())


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return await paginate(User.objects)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_orm:app")
