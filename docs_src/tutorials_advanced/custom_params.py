from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field

from fastapi_pagination import Page, add_pagination, paginate

Page = Page.with_custom_options(
    size=Field(100, ge=1, le=500),
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
