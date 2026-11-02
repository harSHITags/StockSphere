from pydantic import BaseModel,EmailStr,Field
from typing import List


class Product(BaseModel):
    id:int
    name:str
    description:str
    price:float
    quantity:int

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class DescriptionRequest(BaseModel):
    name: str
    category: str

class InventoryAdviceRequest(BaseModel):
    low_stock_threshold: int = 5


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_name: str
    items: List[OrderItemCreate]


class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)


class PurchaseCreate(BaseModel):
    supplier_name: str
    items: List[PurchaseItemCreate]