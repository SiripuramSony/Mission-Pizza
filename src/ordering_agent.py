import json
from typing import Any, Dict, List

from openai import OpenAI

from pizza_mcp_server import (
    PizzaMCPServerFactory,
    execute_mcp_tool,
    format_tools_for_llm,
)


class PizzaOrderingAgent:
    """
    AI agent that understands natural language pizza orders
    and interacts with the Pizza MCP-style server.

    Flow:
    1. User: "I want a large Margherita"
    2. Agent calls LLM with available tools
    3. LLM decides which tools to call (listPizzas, placeOrder, etc.)
    4. Agent executes tools
    5. LLM generates final response for the user
    """

    def __init__(self, mcp_server, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.mcp_server = mcp_server

        self.llm_tools = format_tools_for_llm(mcp_server)

        self.conversation_history: List[Dict[str, Any]] = []

        # System prompt to guide the agent's behavior
        self.system_prompt = (
            "You are a helpful pizza ordering assistant for Mission-Pizza.\n\n"
            "Your responsibilities:\n"
            "1. Understand customer's pizza order requests.\n"
            "2. Ask for missing details (size, address, name, phone) if needed.\n"
            "3. Use tools to:\n"
            "   - listPizzas: see available pizzas\n"
            "   - placeOrder: place the customer's order\n"
            "   - listOrders / trackOrder: check existing orders\n"
            "4. Always confirm details before placing an order.\n"
            "5. Reply clearly with order id, total price and estimated delivery time.\n"
        )

    def process_request(self, user_message: str) -> str:
        """
        Main entrypoint: handle a user's message and return agent reply.
        """
        # 1. Add user message to chat history
        self.conversation_history.append({"role": "user", "content": user_message})

        # 2. First LLM call - may decide to call tools
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
            ],
            tools=self.llm_tools,
            tool_choice="auto",
            temperature=0.4,
            max_tokens=700,
        )

        message = response.choices[0].message

        # 3. If LLM wants to call tools, execute them
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments or "{}")

                # Execute on MCP server
                tool_result = execute_mcp_tool(self.mcp_server, tool_name, tool_args)

                # Add tool call and result to history
                self.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args),
                                },
                            }
                        ],
                    }
                )
                self.conversation_history.append(
                    {
                        "role": "tool",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(tool_result),
                    }
                )

            # 4. Second LLM call - use tool results to form final reply
            followup = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history,
                ],
                tools=self.llm_tools,
                temperature=0.4,
                max_tokens=700,
            )
            final_message = followup.choices[0].message
            final_text = final_message.content or ""
            self.conversation_history.append(
                {"role": "assistant", "content": final_text}
            )
            return final_text

        # 5. If no tools were called, just return the text reply
        final_text = message.content or ""
        self.conversation_history.append({"role": "assistant", "content": final_text})
        return final_text

    def reset_conversation(self) -> None:
        """Clear history for a fresh interaction."""
        self.conversation_history = []


def demo_ordering_agent() -> None:
    """
    Simple demo:
    - Assumes FastAPI backend is running on :8000
    - Assumes OpenAPI spec exists in openapi/pizza_openapi_spec.json
    """
    print("\n" + "=" * 70)
    print("🤖 PIZZA ORDERING AGENT DEMO")
    print("=" * 70 + "\n")

    # Create MCP server
    mcp_server, _ = PizzaMCPServerFactory.create_server()
    agent = PizzaOrderingAgent(mcp_server)

    # Example conversation
    user_msgs = [
        "Hi, I want a large Margherita pizza.",
        "My address is 123 Main Street, Hyderabad. My name is Raj and phone number is 9876543210.",
    ]

    for msg in user_msgs:
        print(f"👤 User: {msg}")
        reply = agent.process_request(msg)
        print(f"🤖 Agent: {reply}\n")

    print("=" * 70)
    print("Demo finished.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo_ordering_agent()
