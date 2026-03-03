from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    stock: int = 0
    category: str

class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str
    created_at: datetime

    class Config:
        from_attributes = True
