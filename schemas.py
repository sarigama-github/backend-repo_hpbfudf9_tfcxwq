"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class HerbalProduct(BaseModel):
    """
    Herbal products collection schema
    Collection: "herbalproduct"
    """
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Detailed description and benefits")
    price: float = Field(..., ge=0, description="Price in IDR")
    category: str = Field(..., description="Category, e.g., Teh, Suplemen, Minyak")
    in_stock: bool = Field(True, description="Stock availability")
    image: Optional[str] = Field(None, description="Image URL")
    ingredients: Optional[List[str]] = Field(default=None, description="Key herbal ingredients")
    usage: Optional[str] = Field(None, description="How to use / dosage")

class Article(BaseModel):
    """
    Educational articles about herbs and wellness
    Collection: "article"
    """
    title: str
    summary: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    tags: Optional[List[str]] = None

class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int = Field(..., ge=1)

class CustomerInfo(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: str

class Order(BaseModel):
    """
    Orders collection schema
    Collection: "order"
    """
    items: List[OrderItem]
    customer: CustomerInfo
    note: Optional[str] = None
    total: float = Field(..., ge=0)
