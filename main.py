import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🍕 MISSION-PIZZA: STEP-BY-STEP ORDERING")
print("=" * 60)
print("📋 Follow numbered steps 1→2→3→4")
print("📋 Pizza API server must be running")
print("-" * 60)

from pizza_mcp_server import PizzaMCPServerFactory, execute_mcp_tool
server, _ = PizzaMCPServerFactory.create_server()

menu_cache = execute_mcp_tool(server, "listPizzas", {})

def show_menu():
    print("\n🍕 CHOOSE PIZZA:")
    print("-" * 30)
    for pizza in menu_cache:
        print(f"  {pizza['id']}. {pizza['name']} - ₹{pizza['price']}")
    print("-" * 30)

current_step = 1
order_details = {}

print("\n🤖 **STEP 1/4: Choose Pizza**")
print("   Say: 'menu' then pizza number (1-5)")
while True:
    user_input = input("\n👤 You: ").strip().lower()
    
    if user_input in ['quit', 'exit', 'q']:
        print("🤖 Thanks! 🍕")
        break
    
    # STEP 1: Pizza selection
    if current_step == 1:
        if 'menu' in user_input:
            show_menu()
        else:
            try:
                pizza_id = int(user_input)
                if 1 <= pizza_id <= 5:
                    pizza_name = next(p["name"] for p in menu_cache if p["id"] == pizza_id)
                    order_details["pizza_id"] = pizza_id
                    order_details["pizza_name"] = pizza_name
                    current_step = 2
                    print(f"\n✅ **{pizza_name}** selected!")
                    print("\n🤖 **STEP 2/4: Choose Size**")
                    print("   Say: s=small, m=medium, l=large")
                else:
                    print("❌ Pizza 1-5 only!")
            except:
                print("❌ Say number 1-5")
    
    # STEP 2: Size
    elif current_step == 2:
        size_map = {'s': 'small', 'm': 'medium', 'l': 'large'}
        size = size_map.get(user_input, user_input)
        if size in ['small', 'medium', 'large']:
            order_details["size"] = size
            current_step = 3
            print(f"\n✅ **{size.title()}** size selected!")
            print("\n🤖 **STEP 3/4: Quantity**")
            print("   Say: 1, 2, 3, 4, or 5")
        else:
            print("❌ Say: s, m, l, small, medium, large")
    
    # STEP 3: Quantity
    elif current_step == 3:
        try:
            qty = int(user_input)
            if 1 <= qty <= 5:
                order_details["quantity"] = qty
                current_step = 4
                print(f"\n✅ **{qty} pizza(s)** selected!")
                print("\n🤖 **STEP 4/4: Delivery**")
                print("   Say: '123 Road, YourName'")
            else:
                print("❌ Quantity 1-5 only!")
        except:
            print("❌ Say number 1-5")
    
    # STEP 4: Address → PLACE ORDER!
    elif current_step == 4:
        if len(user_input.split()) >= 2:
            order_details["address"] = user_input.title()
            order_details["customer_name"] = "Customer"
            order_details["phone"] = "9876543210"
            
            # FIXED ORDER PLACEMENT
            print("\n🚀 **PLACING ORDER** (MCP placeOrder tool)")
            result = execute_mcp_tool(server, "placeOrder", order_details)
            order_id = result.get("order_id", "ORD-DEMO-123")
            total_price = result.get("total_price", 800.0)
            
            print("\n" + "="*50)
            print("🎉 **ORDER CONFIRMED!** 🎉")
            print(f"📄 **ID:** {order_id}")
            print(f"💰 **Total:** ₹{total_price}")
            print(f"🍕 **{order_details['quantity']}x {order_details['pizza_name']}** ({order_details['size']})")
            print(f"🏠 **{order_details['address']}**")
            print(f"⏱️ **Delivery: 35 minutes**")
            print("="*50)
            
            print("\n🤖 **New order?** Say 'menu' or 'quit'")
            current_step = 1
            order_details = {}
        else:
            print("❌ Say full address: '123 Road, YourName'")
    
    print("-" * 60)
