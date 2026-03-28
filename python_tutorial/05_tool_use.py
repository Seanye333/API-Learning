"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 5: Tool Use (Function Calling)                  ║
║                                                          ║
║   Learn:                                                 ║
║   • How to define tools with JSON Schema                 ║
║   • The agentic loop (request → tool_use → result)       ║
║   • Handling multiple tool calls                         ║
║   • Error handling in tool results                       ║
╚══════════════════════════════════════════════════════════╝

Run: python 05_tool_use.py
"""

import os
import json
import math
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1: Define your tools (JSON Schema format)
# ══════════════════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Returns temperature, condition, and humidity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Tokyo', 'Paris', 'New York'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit (default: celsius)"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression. Supports basic math, sqrt, pow, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression, e.g. '2 + 2', 'sqrt(16)', '15 * 1.15'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "lookup_word",
        "description": "Look up the definition of an English word.",
        "input_schema": {
            "type": "object",
            "properties": {
                "word": {
                    "type": "string",
                    "description": "The word to define"
                }
            },
            "required": ["word"]
        }
    }
]


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2: Implement the actual tool functions
# ══════════════════════════════════════════════════════════════════════════════

# Simulated weather data (in a real app, call a weather API)
WEATHER_DATA = {
    "tokyo":     {"temp_c": 18, "condition": "Partly cloudy", "humidity": 65},
    "paris":     {"temp_c": 14, "condition": "Overcast", "humidity": 78},
    "new york":  {"temp_c": 22, "condition": "Sunny", "humidity": 45},
    "london":    {"temp_c": 11, "condition": "Rainy", "humidity": 85},
    "sydney":    {"temp_c": 26, "condition": "Clear", "humidity": 55},
}

# Simulated dictionary
DICTIONARY = {
    "serendipity": "The occurrence of events by chance in a happy way.",
    "ephemeral": "Lasting for a very short time.",
    "ubiquitous": "Present, appearing, or found everywhere.",
    "eloquent": "Fluent or persuasive in speaking or writing.",
}


def execute_tool(name: str, input_data: dict) -> str:
    """Execute a tool and return the result as a string."""

    if name == "get_weather":
        city = input_data["city"].lower()
        unit = input_data.get("unit", "celsius")

        data = WEATHER_DATA.get(city)
        if not data:
            return f"Error: No weather data available for '{input_data['city']}'. Available cities: {', '.join(WEATHER_DATA.keys())}"

        temp = data["temp_c"]
        if unit == "fahrenheit":
            temp = round(temp * 9 / 5 + 32)
            temp_str = f"{temp}°F"
        else:
            temp_str = f"{temp}°C"

        return f"Weather in {input_data['city']}: {temp_str}, {data['condition']}, Humidity: {data['humidity']}%"

    elif name == "calculate":
        expression = input_data["expression"]
        try:
            # Safe-ish math evaluation with limited builtins
            allowed = {"sqrt": math.sqrt, "pow": pow, "abs": abs, "round": round,
                       "floor": math.floor, "ceil": math.ceil, "pi": math.pi, "e": math.e}
            result = eval(expression, {"__builtins__": {}}, allowed)
            return str(result)
        except Exception as e:
            return f"Error: Could not evaluate '{expression}' — {e}"

    elif name == "lookup_word":
        word = input_data["word"].lower()
        definition = DICTIONARY.get(word)
        if definition:
            return f"{input_data['word']}: {definition}"
        return f"Error: No definition found for '{input_data['word']}'."

    return f"Error: Unknown tool '{name}'"


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3: The Agentic Loop
# ══════════════════════════════════════════════════════════════════════════════

def run_agentic_loop(client: anthropic.Anthropic, user_query: str) -> str:
    """
    Run the full agentic loop:
    1. Send user query + tool definitions
    2. If Claude returns tool_use → execute tools, send results back
    3. Repeat until Claude returns end_turn
    """
    messages = [{"role": "user", "content": user_query}]
    iteration = 0

    print(f"\n  🔄 Starting agentic loop...")

    while iteration < 10:  # Safety limit
        iteration += 1

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        # ── Check stop reason ──────────────────────────────────────────────
        print(f"\n  ─ Iteration {iteration} (stop_reason: {response.stop_reason})")

        # Extract text blocks (Claude's thinking/explanation)
        for block in response.content:
            if block.type == "text" and block.text:
                print(f"    💬 Claude says: \"{block.text[:120]}{'...' if len(block.text) > 120 else ''}\"")

        # If Claude is done, extract final answer
        if response.stop_reason == "end_turn":
            print(f"  ✅ Loop complete in {iteration} iteration(s)")
            final = next((b.text for b in response.content if b.type == "text"), "")
            return final

        # ── Handle tool calls ──────────────────────────────────────────────
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            # No tools and not end_turn — unexpected, break
            break

        # Append Claude's full response to messages (preserves tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})

        # Execute each tool and collect results
        tool_results = []
        for tool_block in tool_use_blocks:
            print(f"    🔧 Tool call: {tool_block.name}({json.dumps(tool_block.input)})")

            result = execute_tool(tool_block.name, tool_block.input)
            print(f"    📥 Result: {result}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,     # Must match the tool_use block's id!
                "content": result
            })

        # Send all tool results back
        messages.append({"role": "user", "content": tool_results})

    return "Error: max iterations reached"


def main():
    print("\n🔧 LESSON 5: Tool Use (Function Calling)\n" + "─" * 40)

    client = anthropic.Anthropic()

    # ── Demo 1: Single tool call ───────────────────────────────────────────
    print("\n📋 Demo 1: Single Tool Call")
    print('  Query: "What is the weather in Tokyo?"')
    result = run_agentic_loop(client, "What is the weather in Tokyo?")
    print(f"\n  Final answer: {result}")

    # ── Demo 2: Multiple tool calls ────────────────────────────────────────
    print("\n\n📋 Demo 2: Multiple Tool Calls")
    print('  Query: "Compare the weather in Paris and Sydney."')
    result = run_agentic_loop(client, "Compare the weather in Paris and Sydney in celsius.")
    print(f"\n  Final answer: {result}")

    # ── Demo 3: Mixed tools ────────────────────────────────────────────────
    print("\n\n📋 Demo 3: Different Tools in One Query")
    query = "What's the weather in London? Also calculate 20% tip on $85.50. And define 'serendipity'."
    print(f'  Query: "{query}"')
    result = run_agentic_loop(client, query)
    print(f"\n  Final answer: {result}")

    # ── Demo 4: Error handling ─────────────────────────────────────────────
    print("\n\n📋 Demo 4: Tool Error Handling")
    print('  Query: "What is the weather in Atlantis?"')
    result = run_agentic_loop(client, "What is the weather in Atlantis?")
    print(f"\n  Final answer: {result}")

    # ── Key Concepts ───────────────────────────────────────────────────────
    print("\n\n💡 Key Concepts:")
    print("  • Define tools with: name, description, input_schema (JSON Schema)")
    print("  • stop_reason='tool_use' → Claude wants you to run a function")
    print("  • Loop until stop_reason='end_turn' → this is the 'agentic loop'")
    print("  • Always match tool_use_id when returning tool_results")
    print("  • Set is_error=True on tool results when a tool fails")
    print("  • Write DETAILED descriptions — Claude uses them to pick the right tool")

    print("\n" + "─" * 40)
    print("🎯 YOUR TURN — Exercises:")
    print("  1. Add a new tool (e.g., translate, unit_convert)")
    print("  2. Try setting tool_choice={'type': 'tool', 'name': 'calculate'}")
    print("  3. Add human confirmation before executing tools")
    print("  4. Make a tool return is_error=True and see how Claude adapts\n")


if __name__ == "__main__":
    main()
