from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Dict
import uuid
from models import (
    Pizza, OrderRequest, OrderResponse, Order, 
    SizeEnum, StatusEnum
)

app = FastAPI(
    title="Mission-Pizza API",
    description="Pizza ordering system for AI agents",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PIZZAS: List[Pizza] = [
    Pizza(
        id=1,
        name="Margherita",
        description="Classic tomato, mozzarella, and fresh basil",
        price=300.0,
        ingredients=["tomato sauce", "mozzarella", "basil"]
    ),
    Pizza(
        id=2,
        name="Pepperoni",
        description="Tomato sauce, mozzarella, and pepperoni slices",
        price=400.0,
        ingredients=["tomato sauce", "mozzarella", "pepperoni"]
    ),
    Pizza(
        id=3,
        name="Vegetarian",
        description="Mixed vegetables with mozzarella and olive oil",
        price=350.0,
        ingredients=["tomato sauce", "mozzarella", "bell peppers", "mushrooms", "onions"]
    ),
    Pizza(
        id=4,
        name="Chicken Tikka",
        description="Indian style pizza with tandoori chicken",
        price=450.0,
        ingredients=["chicken tikka", "mozzarella", "onions", "cilantro"]
    ),
    Pizza(
        id=5,
        name="Paneer Masala",
        description="Spiced cottage cheese with Indian spices",
        price=380.0,
        ingredients=["paneer", "mozzarella", "tomato sauce", "spices"]
    ),
]

ORDERS: Dict[str, Order] = {}

# Size multipliers for pricing
SIZE_MULTIPLIERS = {
    SizeEnum.SMALL: 0.8,
    SizeEnum.MEDIUM: 1.0,
    SizeEnum.LARGE: 1.2,
}



@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Mission-Pizza API",
        "version": "1.0.0"
    }


@app.get("/api/pizzas", response_model=List[Pizza], tags=["Menu"])
async def list_pizzas():
    """
    List all available pizzas
    
    Returns:
        List of Pizza objects with id, name, description, price, and ingredients
    """
    return PIZZAS


@app.post("/api/orders", response_model=OrderResponse, tags=["Orders"], status_code=201)
async def place_order(order_request: OrderRequest):
    """
    Place a new pizza order
    
    Args:
        order_request: OrderRequest with pizza_id, size, quantity, address, customer_name, phone
        
    Returns:
        OrderResponse with order_id, status, prep_time, total_price, estimated_delivery_time
    """
    # Validate pizza exists
    pizza = next((p for p in PIZZAS if p.id == order_request.pizza_id), None)
    if not pizza:
        raise HTTPException(status_code=404, detail="Pizza not found")
    
    # Calculate total price
    base_price = pizza.price * order_request.quantity
    size_multiplier = SIZE_MULTIPLIERS.get(order_request.size, 1.0)
    total_price = base_price * size_multiplier
    
    # Create order
    order_id = f"ORD{str(uuid.uuid4())[:8].upper()}"
    created_at = datetime.utcnow()
    
    # Estimate times
    prep_time = "25 minutes"
    estimated_delivery_time = created_at + timedelta(minutes=35)
    
    # Store order
    order = Order(
        order_id=order_id,
        pizza_id=pizza.id,
        pizza_name=pizza.name,
        size=order_request.size,
        quantity=order_request.quantity,
        address=order_request.address,
        customer_name=order_request.customer_name,
        phone=order_request.phone,
        status=StatusEnum.CONFIRMED,
        total_price=round(total_price, 2),
        created_at=created_at,
        estimated_delivery_time=estimated_delivery_time
    )
    
    ORDERS[order_id] = order
    
    return OrderResponse(
        order_id=order_id,
        status=StatusEnum.CONFIRMED,
        prep_time=prep_time,
        total_price=round(total_price, 2),
        estimated_delivery_time=estimated_delivery_time.isoformat()
    )


@app.get("/api/orders", response_model=List[Order], tags=["Orders"])
async def list_orders():
    """
    List all orders in the system
    
    Returns:
        List of all Order objects
    """
    return list(ORDERS.values())


@app.get("/api/orders/{order_id}", response_model=Order, tags=["Orders"])
async def track_order(order_id: str):
    """
    Track a specific order by ID
    
    Args:
        order_id: The order ID to track
        
    Returns:
        Order object with current status and details
        
    Raises:
        HTTPException: If order not found
    """
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@app.put("/api/orders/{order_id}/status", response_model=Order, tags=["Orders"])
async def update_order_status(order_id: str, status: StatusEnum):
    """
    Update order status (for testing)
    
    Args:
        order_id: The order ID to update
        status: New status
        
    Returns:
        Updated Order object
    """
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    return order



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mock_pizza_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
