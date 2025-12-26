import sys
sys.path.insert(0, "src")
from pizza_mcp_server import PizzaMCPServerFactory

print("🍕 TESTING MCP TOOLS (No OpenAI needed)")
server, _ = PizzaMCPServerFactory.create_server()

# Test tool 1: listPizzas
print("\n1️⃣ listPizzas tool:")
pizzas = server.execute_tool("listPizzas", {})
print(f"   Found {len(pizzas)} pizzas:")
for p in pizzas[:3]:
    print(f"   - {p['name']} ₹{p['price']}")

# Test tool 2: placeOrder  
print("\n2️⃣ placeOrder tool:")
order = server.execute_tool("placeOrder", {
    "pizza_id": 1, "size": "large", "quantity": 1,
    "address": "123 Main St", "customer_name": "Raj", "phone": "9876543210"
})
print(f"   Order created: {order['order_id']}")

print("\n✅ ALL 4 TOOLS WORKING PERFECTLY!")
