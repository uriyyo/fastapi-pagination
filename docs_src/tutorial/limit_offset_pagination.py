from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_pagination import LimitOffsetPage, add_pagination, paginate

app = FastAPI()
add_pagination(app)


class UserOut(BaseModel):
    name: str
    email: str


users: List[UserOut] = [
    UserOut(name="Steve", email="hello@world.com"),
    # ...
]


# req: GET /users
@app.get("/users")
def get_users() -> LimitOffsetPage[UserOut]:
    return paginate(users)
