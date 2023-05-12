from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

from fastapi_pagination import add_pagination, paginate
from fastapi_pagination.links import Page

app = FastAPI()
add_pagination(app)


class UserOut(BaseModel):
    name: str
    email: EmailStr


users: List[UserOut] = [
    # ...
]


@app.get("/users")
def get_users() -> Page[UserOut]:
    return paginate(users)
