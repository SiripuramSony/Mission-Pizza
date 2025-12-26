import json
from typing import Any, Dict, List, Tuple

import httpx

from mcp_generator import (
    OpenAPIMCPTransformer,
    PizzaMCPServer,
    create_handlers,
)


class PizzaMCPServerFactory:
    """
    Factory that creates and initializes the Pizza MCP-style server.

    Steps:
    1. Load OpenAPI specification
    2. Create HTTP client for backend API
    3. Build handlers that call FastAPI endpoints
    4. Transform OpenAPI → tool definitions
    5. Register tools on PizzaMCPServer
    """

    @staticmethod
    def create_server(
        openapi_spec_path: str = "openapi/pizza_openapi_spec.json",
    ) -> Tuple[PizzaMCPServer, httpx.Client]:
        # Step 1: Load OpenAPI spec
        with open(openapi_spec_path, "r", encoding="utf-8") as f:
            openapi_spec = json.load(f)

        print("✓ Loaded OpenAPI specification")

        # Step 2: HTTP client
        api_client = httpx.Client(timeout=30.0)

        # Step 3: Create handlers → map operationId → function
        handlers = create_handlers(api_client)
        print(f"✓ Created {len(handlers)} API handlers")

        # Step 4: Transform OpenAPI → tool definitions
        transformer = OpenAPIMCPTransformer(openapi_spec)
        tools = transformer.transform(handlers)
        print(f"✓ Generated {len(tools)} tools from OpenAPI")
        print("  Tools:", [t.name for t in tools])

        # Step 5: Register tools on MCP-style server
        mcp_server = PizzaMCPServer()
        mcp_server.register_tools(tools)
        print(f"✓ MCP server ready with {len(mcp_server.get_tools())} tools")

        return mcp_server, api_client

    @staticmethod
    def get_server_tools(mcp_server: PizzaMCPServer) -> List[Dict[str, Any]]:
        """Return all tools in dict form."""
        return mcp_server.get_tools()


def execute_mcp_tool(
    mcp_server: PizzaMCPServer,
    tool_name: str,
    tool_input: Dict[str, Any],
) -> Any:
    """
    Helper to execute a tool safely.
    """
    try:
        return mcp_server.execute_tool(tool_name, tool_input)
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


def format_tools_for_llm(mcp_server: PizzaMCPServer) -> List[Dict[str, Any]]:
    """
    Convert tools to OpenAI-style function-calling schema.

    Output shape:
    [
      {
        "type": "function",
        "function": {
          "name": "...",
          "description": "...",
          "parameters": { ...json schema... }
        }
      },
      ...
    ]
    """
    raw_tools = mcp_server.get_tools()
    formatted: List[Dict[str, Any]] = []

    for t in raw_tools:
        formatted.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"],
                },
            }
        )

    return formatted


def print_mcp_server_info(mcp_server: PizzaMCPServer) -> None:
    """Print available tools and their schemas."""
    tools = mcp_server.get_tools()

    print("\n" + "=" * 60)
    print("🍕 PIZZA MCP SERVER INFORMATION")
    print("=" * 60)

    print(f"\nTotal Tools: {len(tools)}")
    print("-" * 60)

    for i, t in enumerate(tools, start=1):
        print(f"\n{i}. {t['name']}")
        print(f"   Description: {t['description']}")
        print(f"   Input schema: {json.dumps(t['inputSchema'], indent=2)}")

    print("\n" + "=" * 60 + "\n")


def test_mcp_tools(mcp_server: PizzaMCPServer) -> None:
    """Simple smoke test for tools."""
    print("\n" + "=" * 60)
    print("🧪 TESTING MCP TOOLS")
    print("=" * 60 + "\n")
    print("Test: listPizzas")
    try:
        pizzas = execute_mcp_tool(mcp_server, "listPizzas", {})
        print(f"✓ Got {len(pizzas)} pizzas")
        for p in pizzas[:3]:
            print(f"  - {p['name']} (₹{p['price']})")
    except Exception as e:
        print("✗ listPizzas failed:", e)

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    """
    Standalone test:
    - Assumes FastAPI backend is already running on :8000
    - Assumes openapi/pizza_openapi_spec.json exists
    """
    try:
        server, client = PizzaMCPServerFactory.create_server()
        print_mcp_server_info(server)
        test_mcp_tools(server)
        print("✅ Pizza MCP server is working.")
    except FileNotFoundError as e:
        print("❌ OpenAPI spec not found:", e)
    except Exception as e:
        print("❌ Unexpected error:", e)
