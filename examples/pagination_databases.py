from contextlib import asynccontextmanager
from typing import Any

import sqlalchemy
import uvicorn
from databases import Database
from faker import Faker
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.databases import paginate

faker = Faker()

metadata = sqlalchemy.MetaData()
Users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=False),
)

db = Database("sqlite:///.db")


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
        await db.execute(
            Users.insert(),
            {
                "name": faker.name(),
                "email": faker.email(),
            },
        )
    yield
    await db.disconnect()


app = FastAPI(lifespan=lifespan)


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    id_ = await db.execute(Users.insert(), user_in.dict())

    return {**user_in.dict(), "id": id_}


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return await paginate(db, Users.select())


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_databases:app")
