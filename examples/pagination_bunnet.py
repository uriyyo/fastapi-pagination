from typing import Any

import uvicorn
from bunnet import Document, init_bunnet
from faker import Faker
from fastapi import FastAPI
from pydantic import Field
from pymongo import MongoClient

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.bunnet import paginate

faker = Faker()


class UserIn(Document):
    name: str = Field(..., example=faker.name())
    email: str = Field(..., example=faker.email())

    class Settings:
        name = "users"


class UserOut(UserIn):
    _id: int


app = FastAPI()
client: MongoClient


@app.on_event("startup")
def on_startup() -> None:
    global client
    client = MongoClient("mongodb://localhost:27017")
    init_bunnet(client.test, document_models=[UserIn])

    users = [UserIn(name=faker.name(), email=faker.email()) for _ in range(100)]
    UserIn.insert_many(users)


@app.post("/users", response_model=UserOut)
def create_user(user_in: UserIn) -> Any:
    result = user_in.insert()
    return UserIn.find_one(UserIn.id == result.id).run()


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return paginate(UserIn)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_bunnet:app")
