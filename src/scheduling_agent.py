import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from openai import OpenAI


class SchedulingAgent:
    """
    Scheduling agent that receives order details and schedules delivery.

    For this project:
    - We simulate a calendar instead of using a real Google Calendar API.
    """

    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.conversation_history: List[Dict[str, Any]] = []
        self.scheduled_deliveries: Dict[str, Dict[str, Any]] = {}

        # Define tools the LLM can "call" (simulated calendar ops)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "schedule_delivery",
                    "description": "Schedule a pizza delivery time.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Order ID from pizza system.",
                            },
                            "delivery_time": {
                                "type": "string",
                                "description": "ISO 8601 datetime for delivery.",
                            },
                            "address": {
                                "type": "string",
                                "description": "Delivery address.",
                            },
                            "customer_name": {
                                "type": "string",
                                "description": "Customer name.",
                            },
                        },
                        "required": ["order_id", "delivery_time", "address", "customer_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_calendar_availability",
                    "description": "Check if a given time is available for delivery.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "delivery_time": {
                                "type": "string",
                                "description": "ISO 8601 datetime to check.",
                            }
                        },
                        "required": ["delivery_time"],
                    },
                },
            },
        ]

        self.system_prompt = (
            "You are a pizza delivery scheduling assistant.\n\n"
            "Your responsibilities:\n"
            "1. Receive order details (order_id, prep_time, address, customer_name).\n"
            "2. Choose a reasonable delivery time (typically prep_time + 10 minutes).\n"
            "3. Use tools to:\n"
            "   - check_calendar_availability\n"
            "   - schedule_delivery\n"
            "4. Respond with clear delivery time and confirmation.\n"
        )

    def process_order_for_scheduling(
        self,
        order_id: str,
        pizza_name: str,
        prep_time: str,
        address: str,
        customer_name: str,
    ) -> str:
        """
        Entry point called by the orchestrator (Agent-to-Agent).

        Builds a scheduling request message and calls the LLM.
        """
        now = datetime.utcnow()
        delivery_time = now + timedelta(minutes=35)  # 25 prep + 10 delivery
        delivery_time_iso = delivery_time.isoformat()

        request = (
            f"A pizza order has been placed.\n"
            f"- Order ID: {order_id}\n"
            f"- Pizza: {pizza_name}\n"
            f"- Prep time: {prep_time}\n"
            f"- Address: {address}\n"
            f"- Customer: {customer_name}\n"
            f"- Suggested delivery time (UTC): {delivery_time_iso}\n\n"
            f"Please schedule the delivery and confirm the delivery time."
        )

        return self._process_scheduling_request(request, order_id, address, customer_name, delivery_time_iso)

    def _process_scheduling_request(
        self,
        request: str,
        order_id: str,
        address: str,
        customer_name: str,
        delivery_time_iso: str,
    ) -> str:
        """Internal method: talk to LLM and simulate tool calls."""
        self.conversation_history.append({"role": "user", "content": request})

        # First LLM call
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": self.system_prompt}, *self.conversation_history],
            tools=self.tools,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=400,
        )

        message = response.choices[0].message

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")

                if tool_name == "schedule_delivery":
                    args.setdefault("order_id", order_id)
                    args.setdefault("delivery_time", delivery_time_iso)
                    args.setdefault("address", address)
                    args.setdefault("customer_name", customer_name)

                if tool_name == "check_calendar_availability":
                    args.setdefault("delivery_time", delivery_time_iso)

                tool_result = self._execute_calendar_tool(tool_name, args)

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
                                    "arguments": json.dumps(args),
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

            # Second LLM call: produce final text reply
            followup = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": self.system_prompt}, *self.conversation_history],
                temperature=0.3,
                max_tokens=400,
            )
            final_msg = followup.choices[0].message
            final_text = final_msg.content or ""
            self.conversation_history.append({"role": "assistant", "content": final_text})
            return final_text

        # If no tools called, just return the reply
        final_text = message.content or ""
        self.conversation_history.append({"role": "assistant", "content": final_text})
        return final_text

    def _execute_calendar_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate calendar operations."""
        if tool_name == "schedule_delivery":
            order_id = args["order_id"]
            self.scheduled_deliveries[order_id] = {
                "delivery_time": args["delivery_time"],
                "address": args["address"],
                "customer_name": args["customer_name"],
                "status": "scheduled",
            }
            return {
                "success": True,
                "order_id": order_id,
                "delivery_time": args["delivery_time"],
                "message": "Delivery scheduled successfully.",
            }

        if tool_name == "check_calendar_availability":
            # In this demo, always available
            return {
                "available": True,
                "time": args["delivery_time"],
                "message": "Time slot is available.",
            }

        return {"error": f"Unknown tool: {tool_name}"}

    def get_scheduled_deliveries(self) -> Dict[str, Dict[str, Any]]:
        return self.scheduled_deliveries

    def reset_conversation(self) -> None:
        self.conversation_history = []


class AgentOrchestrator:
    """
    Orchestrator that connects OrderingAgent and SchedulingAgent.

    It:
    - sends user request to ordering agent
    - extracts order ID from agent's text reply
    - sends details to scheduling agent
    - returns combined result
    """

    def __init__(self, ordering_agent, scheduling_agent: SchedulingAgent):
        self.ordering_agent = ordering_agent
        self.scheduling_agent = scheduling_agent

    def _extract_order_id(self, text: str) -> Optional[str]:
        """Very simple extraction: looks for pattern like 'ORDXXXX'."""
        import re

        match = re.search(r"ORD[A-Z0-9]{4,}", text)
        if match:
            return match.group(0)
        return None

    def execute_order_workflow(
        self,
        user_request: str,
        delivery_address: str,
        customer_name: str,
        customer_phone: str,
    ) -> Dict[str, Any]:
        """
        Execute the full flow:
        1. Ordering agent places order
        2. Orchestrator extracts order_id
        3. Scheduling agent schedules delivery
        """
        print("\n" + "=" * 70)
        print("🔄 STARTING END-TO-END WORKFLOW")
        print("=" * 70 + "\n")

        # Step 1: Let ordering agent handle the user's pizza request
        combined_request = (
            f"{user_request} My address is {delivery_address}. "
            f"My name is {customer_name}. My phone number is {customer_phone}."
        )
        print(f"👤 User → OrderingAgent: {combined_request}")
        order_reply = self.ordering_agent.process_request(combined_request)
        print(f"🤖 OrderingAgent reply:\n{order_reply}\n")

        # Step 2: Extract order_id from the reply text
        order_id = self._extract_order_id(order_reply)

        if not order_id:
            return {
                "success": False,
                "error": "Could not extract order_id from ordering agent reply.",
                "order_response": order_reply,
            }

        # Step 3: Ask scheduling agent to schedule delivery
        print(f"📦 Extracted order_id: {order_id}")
        print("📅 Sending to SchedulingAgent for delivery scheduling...\n")

        schedule_reply = self.scheduling_agent.process_order_for_scheduling(
            order_id=order_id,
            pizza_name="pizza",  # in a real impl we would parse exact pizza
            prep_time="25 minutes",
            address=delivery_address,
            customer_name=customer_name,
        )

        print(f"🤖 SchedulingAgent reply:\n{schedule_reply}\n")

        return {
            "success": True,
            "order_response": order_reply,
            "scheduling_response": schedule_reply,
            "order_id": order_id,
        }


def demo_complete_workflow() -> None:
    """
    Demonstrates full workflow:
    - assumes FastAPI backend running
    - assumes OpenAPI spec + MCP server working
    """
    from pizza_mcp_server import PizzaMCPServerFactory
    from ordering_agent import PizzaOrderingAgent

    # Create MCP server & agents
    mcp_server, _ = PizzaMCPServerFactory.create_server()
    ordering_agent = PizzaOrderingAgent(mcp_server)
    scheduling_agent = SchedulingAgent()

    orchestrator = AgentOrchestrator(ordering_agent, scheduling_agent)

    result = orchestrator.execute_order_workflow(
        user_request="I want a large Margherita pizza.",
        delivery_address="123 Main Street, Hyderabad",
        customer_name="Raj Kumar",
        customer_phone="9876543210",
    )

    print("=" * 70)
    print("✅ WORKFLOW RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=2))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo_complete_workflow()
