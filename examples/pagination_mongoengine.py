from typing import Any, Generator

import uvicorn
from bson.objectid import ObjectId
from faker import Faker
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from mongoengine import Document, connect, fields
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.mongoengine import paginate

faker = Faker()


class PydanticObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v: ObjectId) -> str:
        return str(v)


class User(Document):
    name = fields.StringField()
    email = fields.EmailField()


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    _id: PydanticObjectId

    class Config:
        orm_mode = True


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    connect(host="mongodb://localhost:27017")
    User.objects().insert([User(name=faker.name(), email=faker.email()) for i in range(100)])


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    result = User.objects().insert(User(**jsonable_encoder(user_in)))
    return User.objects().get(id=result.id).to_mongo()


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return paginate(User)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_mongoengine:app")
