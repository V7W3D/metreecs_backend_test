from pydantic import BaseModel, field_validator
from typing import Literal


# Mapping for type storage
TYPE_TO_INT = {"in": 0, "out": 1}
INT_TO_TYPE = {0: "in", 1: "out"}


class MovementCreate(BaseModel):
    product_id: str
    quantity: int
    type: Literal["in", "out"]

    @field_validator("type", mode="before")
    @classmethod
    def lowercase_type(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v


class MovementResponse(BaseModel):
    id: int
    product_id: str
    quantity: int
    type: str
    created_at: str


class ProductStock(BaseModel):
    product_id: str
    current_stock: int