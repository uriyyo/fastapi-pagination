from typing import Any

import sqlalchemy
import uvicorn
from databases import Database
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from fastapi_pagination import Page, PaginationParams
from fastapi_pagination.ext.databases import paginate

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


app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    engine = sqlalchemy.create_engine(str(db.url))
    metadata.drop_all(engine)
    metadata.create_all(engine)

    await db.connect()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await db.disconnect()


@app.post("/users", response_model=UserOut)
async def create_user(user_in: UserIn) -> Any:
    id_ = await db.execute(Users.insert(), user_in.dict())

    return {**user_in.dict(), "id": id_}


@app.get("/users", response_model=Page[UserOut])
async def get_users(params: PaginationParams = Depends()) -> Any:
    return await paginate(db, Users.select(), params)


if __name__ == "__main__":
    uvicorn.run("pagination_databases:app")
