#!/usr/bin/env python
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator

import uvicorn
from faker import Faker
from fastapi import FastAPI
from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from tortoise import Model
from tortoise.contrib.fastapi import RegisterTortoise  # requires 'tortoise-orm>0.21.0'
from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator
from tortoise.fields import IntField, TextField

faker = Faker()


class User(Model):
    id = IntField(pk=True)
    name = TextField(null=False)
    email = TextField(null=False)


if TYPE_CHECKING:  # pragma: nocoverage

    class UserIn(User, PydanticModel):  # type:ignore[misc]
        pass

    class UserOut(User, PydanticModel):  # type:ignore[misc]
        pass
else:
    UserIn = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
    UserOut = pydantic_model_creator(User, name="User")


async def _initial_users() -> None:
    for _ in range(100):
        await User.create(
            name=faker.name(),
            email=faker.email(),
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with RegisterTortoise(
        app,
        db_url="sqlite://:memory:",
        modules={"models": [__name__]},
        generate_schemas=True,
    ):
        await _initial_users()
        add_pagination(app)
        yield


app = FastAPI(title="Tortoise ORM Pagination example", lifespan=lifespan)


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    return await User.create(**user_in.dict())


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return await paginate(User)


if __name__ == "__main__":
    uvicorn.run(f"{Path(__file__).stem}:app")
