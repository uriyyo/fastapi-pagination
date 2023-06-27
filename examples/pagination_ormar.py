from contextlib import asynccontextmanager
from typing import Any

import sqlalchemy
import uvicorn
from databases import Database
from faker import Faker
from fastapi import FastAPI
from ormar import Integer, Model, String

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.ormar import paginate

faker = Faker()

metadata = sqlalchemy.MetaData()
db = Database("sqlite:///.db")


class User(Model):
    class Meta:
        tablename = "users"
        database = db
        metadata = metadata

    id = Integer(primary_key=True)
    name = String(max_length=100)
    email = String(max_length=100)


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


app = FastAPI(lifespan=lifespan)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await db.disconnect()


@app.post("/users", response_model=User)
async def create_user(user_in: User) -> Any:
    return await user_in.save()


@app.get("/users/default", response_model=Page[User])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[User])
async def get_users() -> Any:
    return await paginate(User.objects)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_ormar:app")
