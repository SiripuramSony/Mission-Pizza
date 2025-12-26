from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SizeEnum(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class StatusEnum(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"


class Pizza(BaseModel):
    """Pizza menu item"""
    id: int
    name: str
    description: str = "Delicious pizza"
    price: float
    ingredients: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Margherita",
                "description": "Classic tomato, mozzarella, and basil",
                "price": 300.0,
                "ingredients": ["tomato", "mozzarella", "basil"]
            }
        }


class OrderRequest(BaseModel):
    """Request model for placing an order"""
    pizza_id: int
    size: SizeEnum
    quantity: int = Field(default=1, ge=1, le=10)
    address: str
    customer_name: str
    phone: str

    class Config:
        json_schema_extra = {
            "example": {
                "pizza_id": 1,
                "size": "large",
                "quantity": 1,
                "address": "123 Main Street, City",
                "customer_name": "John Doe",
                "phone": "9876543210"
            }
        }


class OrderResponse(BaseModel):
    """Response model for order creation"""
    order_id: str
    status: StatusEnum
    prep_time: str
    total_price: float
    estimated_delivery_time: str


class Order(BaseModel):
    """Complete order model"""
    order_id: str
    pizza_id: int
    pizza_name: str
    size: SizeEnum
    quantity: int
    address: str
    customer_name: str
    phone: str
    status: StatusEnum
    total_price: float
    created_at: datetime
    estimated_delivery_time: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD001",
                "pizza_id": 1,
                "pizza_name": "Margherita",
                "size": "large",
                "quantity": 1,
                "address": "123 Main Street",
                "customer_name": "John Doe",
                "phone": "9876543210",
                "status": "preparing",
                "total_price": 400.0,
                "created_at": "2025-12-25T20:00:00",
                "estimated_delivery_time": "2025-12-25T20:30:00"
            }
        }
