from pydantic import BaseModel


class BaseSchema(BaseModel):
    model_config = {
        "from_attributes": True,
    }


class OrderOut(BaseSchema):
    id: int
    name: str


class UserOut(BaseSchema):
    id: int
    name: str


class UserWithoutIDOut(BaseSchema):
    name: str


class UserWithOrderOut(BaseSchema):
    id: int
    name: str

    orders: list[OrderOut]


__all__ = [
    "OrderOut",
    "UserOut",
    "UserWithOrderOut",
    "UserWithoutIDOut",
]
