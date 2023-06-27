import os
from contextlib import asynccontextmanager
from itertools import count
from pathlib import Path
from typing import Any

import uvicorn
from faker import Faker
from fastapi import FastAPI
from piccolo.columns import Integer, Text
from piccolo.conf.apps import AppConfig, AppRegistry
from piccolo.engine import SQLiteEngine, engine_finder
from piccolo.table import Table
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.piccolo import paginate

os.environ["PICCOLO_CONF"] = __name__

_counter = count().__next__

faker = Faker()


class _User(Table):
    id = Integer(default=_counter, primary_key=True)
    name = Text(required=False, null=True)
    email = Text(required=False, null=True)


class UserIn(BaseModel):
    name: str
    email: str


class UserOut(UserIn):
    id: int

    class Config:
        orm_mode = True


DB = SQLiteEngine()
APP_REGISTRY = AppRegistry()

APP_CONFIG = AppConfig(
    app_name="example",
    migrations_folder_path=None,
    table_classes=[_User],
)


@asynccontextmanager
async def lifespan(_: Any) -> None:
    engine: SQLiteEngine = engine_finder()

    p = Path(engine.path)
    if p.exists():
        p.unlink()

    await engine.prep_database()
    await _User.create_table().run()

    for _ in range(100):
        await _User(
            name=faker.name(),
            email=faker.email(),
        ).save()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    return await _User(**user_in.dict()).save()


@app.get("/users/default", response_model=Page[UserOut])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserOut])
async def get_users() -> Any:
    return await paginate(_User)


add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("pagination_piccolo:app")
