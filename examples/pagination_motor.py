from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from faker import Faker
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate

faker = Faker()


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    _id: int

    class Config:
        orm_mode = True


@asynccontextmanager
async def lifespan(_: Any) -> None:
    global client
    client = AsyncIOMotorClient("mongodb://localhost:27017")

    await client.test.users.insert_many([{"name": faker.name(), "email": faker.email()} for _ in range(100)])
    yield


app = FastAPI(lifespan=lifespan)
client: AsyncIOMotorClient


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    result = await client.test.users.insert_one(jsonable_encoder(user_in))
    return await client.test.users.find_one({"_id": result.inserted_id})


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return await paginate(client.test.users)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_motor:app")
