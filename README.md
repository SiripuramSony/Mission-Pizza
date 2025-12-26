# Mission‑Pizza: Multi‑Agent Ordering System

This project implements a complete multi‑agent system using the Model Context Protocol (MCP). It demonstrates how an OpenAPI specification can be automatically converted into executable MCP tools and then used by AI agents to interact with an external REST API.

## Overview

The system is divided into three phases:

1. **Phase 1 – MCP Generation:**  
   Converts the pizza ordering OpenAPI specification into four MCP tools (`listPizzas`, `placeOrder`, `listOrders`, `trackOrder`).

2. **Phase 2 – Ordering Agent:**  
   Uses the generated MCP tools to interpret natural or interactive inputs for pizza ordering.

3. **Phase 3 – Scheduling Agent:**  
   Demonstrates agent‑to‑agent (A2A) communication where an order is passed to a scheduling agent for delivery planning.

An additional interactive CLI application allows users to order pizzas step by step without requiring an OpenAI API key.

## Features

- Automatically generates and registers MCP tools from an OpenAPI file  
- REST API built with FastAPI serving menu and order endpoints  
- Interactive step‑by‑step pizza ordering interface  
- Modular, type‑safe Python code following good design practices  
- Ready integration points for OpenAI GPT models and calendar APIs  
- Two‑agent orchestration code (ordering → scheduling)

## Quick Start

**Requirements:**  
Python 3.10 or later

git clone https://github.com/SiripuramSony/Mission-Pizza.git
cd mission‑pizza
python -m venv venv
venv\Scripts\activate # Windows
pip install -r requirements.txt


**Run the FastAPI service (Terminal 1):**
cd src
python mock_pizza_api.py

**Run the interactive demo (Terminal 2):**
cd ..
python main.py

The API runs on `http://localhost:8000` and the documentation is available at `http://localhost:8000/docs`.

## Project Structure

mission‑pizza/
├── src/
│ ├── models.py
│ ├── mock_pizza_api.py
│ ├── mcp_generator.py
│ ├── pizza_mcp_server.py
│ ├── ordering_agent.py
│ └── scheduling_agent.py
├── openapi/
│ └── pizza_openapi_spec.json
├── main.py
├── requirements.txt
└── .env

## Example Usage
Step 1: menu
Displays the list of available pizzas

Step 2: 4
Selects Chicken Tikka pizza

Step 3: s
Chooses small size

Step 4: 2
Requests quantity of 2

Step 5: 123 Road, Alex
Confirms address and places order

Result:
Order confirmed | 2x Chicken Tikka | Total ₹900 | Delivery in 35 minutes

## Troubleshooting

- **ModuleNotFoundError:** Ensure the virtual environment is activated and run `python main.py` from the project root.  
- **Connection Error:** Confirm that the API server (mock_pizza_api.py) is running on port 8000.  
- **429 Quota Error:** This occurs when the OpenAI API key has no remaining quota; the interactive demo does not require an API key.

## License

MIT License. Free for personal and educational use.
