from typing import Any

import sqlalchemy
import uvicorn
from databases import Database
from fastapi import Depends, FastAPI
from orm import Integer, Model, String
from pydantic import BaseModel

from fastapi_pagination import Page, PaginationParams
from fastapi_pagination.ext.orm import paginate

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


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    engine = sqlalchemy.create_engine("sqlite:///.db")
    metadata.drop_all(engine)
    metadata.create_all(engine)

    await db.connect()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await db.disconnect()


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    return await User.objects.create(**user_in.dict())


@app.get("/users", response_model=Page[UserOut])
async def get_users(params: PaginationParams = Depends()) -> Any:
    return await paginate(User.objects, params)


if __name__ == "__main__":
    uvicorn.run("pagination_orm:app")
