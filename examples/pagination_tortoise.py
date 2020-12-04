from typing import Any

import uvicorn
from faker import Faker
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from tortoise import Model
from tortoise.contrib.fastapi import register_tortoise
from tortoise.fields import IntField, TextField

from fastapi_pagination import Page, pagination_params
from fastapi_pagination.ext.tortoise import paginate

faker = Faker()


class User(Model):
    id = IntField(pk=True)
    name = TextField(null=False)
    email = TextField(null=False)


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


app = FastAPI()

register_tortoise(
    app,
    db_url="sqlite://:memory:",
    modules={"models": [__name__]},
    generate_schemas=True,
)


@app.on_event("startup")
async def on_startup() -> None:
    for _ in range(100):
        await User.create(
            name=faker.name(),
            email=faker.email(),
        )


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    return await User.create(**user_in.dict())


@app.get("/users", response_model=Page[UserOut], dependencies=[Depends(pagination_params)])
async def get_users() -> Any:
    return await paginate(User)


if __name__ == "__main__":
    uvicorn.run("pagination_tortoise:app")
