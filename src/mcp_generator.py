import json
from typing import Any, Dict, List, Callable
import httpx


class MCPToolDefinition:
    """Represents a single MCP-style tool."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_dict(self) -> Dict:
        """Convert to dictionary (similar to MCP tool definition)."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class OpenAPIMCPTransformer:
    """
    Transforms OpenAPI specifications to MCP-compatible tool definitions.

    This is the core of Phase 1: automatically generating tools
    from an OpenAPI spec instead of manually writing wrappers.
    """

    def __init__(self, openapi_spec: Dict[str, Any]):
        self.openapi_spec = openapi_spec
        self.tools: Dict[str, MCPToolDefinition] = {}

    def transform(self, api_handlers: Dict[str, Callable]) -> List[MCPToolDefinition]:
        """
        Main transformation function:
        Takes OpenAPI spec + API handlers → Returns tool definitions.

        api_handlers: maps operationId -> Python function
        """
        paths = self.openapi_spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue

                tool = self._create_tool_from_operation(
                    path=path,
                    method=method,
                    operation=operation,
                    api_handlers=api_handlers,
                )

                if tool:
                    self.tools[tool.name] = tool

        return list(self.tools.values())

    def _create_tool_from_operation(
        self,
        path: str,
        method: str,
        operation: Dict,
        api_handlers: Dict[str, Callable],
    ) -> MCPToolDefinition | None:
        """
        Convert a single OpenAPI operation to a tool definition.
        """
        operation_id = operation.get("operationId")
        if not operation_id:
            return None

        description = operation.get("summary", operation.get("description", ""))

        input_schema = self._extract_input_schema(operation)

        handler = api_handlers.get(operation_id)
        if not handler:
            print(f"Warning: No handler found for operationId={operation_id}")
            return None

        return MCPToolDefinition(
            name=operation_id,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    def _extract_input_schema(self, operation: Dict) -> Dict:
        """
        Build JSON schema for tool inputs from an OpenAPI operation.

        Handles:
        - parameters (path/query)
        - requestBody (JSON)
        """
        properties: Dict[str, Any] = {}
        required: List[str] = []

      
        for param in operation.get("parameters", []):
            param_name = param.get("name")
            param_schema = param.get("schema", {"type": "string"})
            properties[param_name] = {
                "type": param_schema.get("type", "string"),
                "description": param.get("description", ""),
            }
            if param.get("required", False):
                required.append(param_name)

        
        request_body = operation.get("requestBody")
        if request_body:
            content = request_body.get("content", {}).get("application/json", {})
            schema = content.get("schema", {})

            
            if "$ref" in schema:
                schema = self._resolve_schema_ref(schema["$ref"])

            body_properties = schema.get("properties", {})
            properties.update(body_properties)
            body_required = schema.get("required", [])
            required.extend(body_required)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _resolve_schema_ref(self, ref: str) -> Dict:
        """
        Resolve $ref references like '#/components/schemas/OrderRequest'
        into the actual schema definition.
        """
        parts = ref.split("/")
        schema: Dict[str, Any] = self.openapi_spec

        for part in parts:
            if part == "#":
                continue
            schema = schema.get(part, {})

        return schema


class PizzaMCPServer:
    """
    Simple in-memory 'MCP-style' server wrapper.

    It stores tool definitions and lets you execute them by name.
    """

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.tools: Dict[str, MCPToolDefinition] = {}

    def register_tools(self, tools: List[MCPToolDefinition]) -> None:
        """Register transformed tools."""
        for tool in tools:
            self.tools[tool.name] = tool

    def get_tools(self) -> List[Dict]:
        """Return tools in dict form (for LLM function-calling)."""
        return [tool.to_dict() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, input_params: Dict[str, Any]) -> Any:
        """Execute a registered tool by name."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")

        return tool.handler(**input_params)


# HANDLERS: CONNECT TO FASTAPI BACKEND 

def create_handlers(api_client: httpx.Client) -> Dict[str, Callable]:
    """
    Create handler functions that call your FastAPI pizza backend.
    These map OpenAPI operationId → Python function.
    """

    def list_pizzas_handler() -> List[Dict]:
        """Handle GET /api/pizzas"""
        resp = api_client.get("http://localhost:8000/api/pizzas")
        resp.raise_for_status()
        return resp.json()

    def place_order_handler(
        pizza_id: int,
        size: str,
        address: str,
        customer_name: str,
        phone: str,
        quantity: int = 1,
    ) -> Dict:
        """Handle POST /api/orders"""
        payload = {
            "pizza_id": pizza_id,
            "size": size,
            "quantity": quantity,
            "address": address,
            "customer_name": customer_name,
            "phone": phone,
        }
        resp = api_client.post("http://localhost:8000/api/orders", json=payload)
        resp.raise_for_status()
        return resp.json()

    def list_orders_handler() -> List[Dict]:
        """Handle GET /api/orders"""
        resp = api_client.get("http://localhost:8000/api/orders")
        resp.raise_for_status()
        return resp.json()

    def track_order_handler(order_id: str) -> Dict:
        """Handle GET /api/orders/{order_id}"""
        resp = api_client.get(f"http://localhost:8000/api/orders/{order_id}")
        resp.raise_for_status()
        return resp.json()

    return {
        "listPizzas": list_pizzas_handler,
        "placeOrder": place_order_handler,
        "listOrders": list_orders_handler,
        "trackOrder": track_order_handler,
    }


if __name__ == "__main__":
    """
    Quick manual test for the transformer.
    You can run:  python -m src.mcp_generator   (after package setup)
    """
    import os

    spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi", "pizza_openapi_spec.json")
    with open(spec_path, "r", encoding="utf-8") as f:
        openapi_spec = json.load(f)

    client = httpx.Client(timeout=30.0)
    transformer = OpenAPIMCPTransformer(openapi_spec)
    handlers = create_handlers(client)
    tools = transformer.transform(handlers)

    print(f"Generated tools: {[t.name for t in tools]}")
