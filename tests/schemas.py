from typing import List

from pydantic import BaseModel


class OrderOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class UserOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class UserWithOrderOut(BaseModel):
    id: int
    name: str

    orders: List[OrderOut]

    class Config:
        orm_mode = True


__all__ = [
    "OrderOut",
    "UserOut",
    "UserWithOrderOut",
]
