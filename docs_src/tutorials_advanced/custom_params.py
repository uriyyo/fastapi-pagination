from typing import List

from fastapi import FastAPI, Query
from pydantic import BaseModel, EmailStr

from fastapi_pagination import Page, add_pagination, paginate

Page = Page.with_custom_options(
    size=Query(100, ge=1, le=500),
)

app = FastAPI()
add_pagination(app)


class UserOut(BaseModel):
    name: str
    email: EmailStr


users: List[UserOut] = []


@app.get("/users")
def get_users() -> Page[UserOut]:
    return paginate(users)
