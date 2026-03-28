"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 1: Your First API Call                          ║
║                                                          ║
║   Learn:                                                 ║
║   • How to create an Anthropic client                    ║
║   • Sending a basic message to Claude                    ║
║   • Reading the response (text, tokens, metadata)        ║
╚══════════════════════════════════════════════════════════╝

Run: python 01_basic_message.py
"""

import os
import anthropic

# ── Load API key from ../.env if available ─────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass  # dotenv is optional — key can come from environment


def main():
    print("\n📡 LESSON 1: Your First API Call\n" + "─" * 40)

    # ── Step 1: Create the client ──────────────────────────────────────────────
    # The client reads ANTHROPIC_API_KEY from your environment automatically.
    # You can also pass it explicitly: anthropic.Anthropic(api_key="sk-ant-...")
    client = anthropic.Anthropic()

    # ── Step 2: Send a message ─────────────────────────────────────────────────
    print("\n➤ Sending message to Claude...")
    print('  Prompt: "What are 3 fun facts about octopuses?"')

    response = client.messages.create(
        model="claude-haiku-4-5",      # fast + cheap — great for learning
        max_tokens=1024,                # max response length in tokens
        messages=[
            {"role": "user", "content": "What are 3 fun facts about octopuses?"}
        ]
    )

    # ── Step 3: Read the response ──────────────────────────────────────────────
    print("\n✅ Response received!\n")

    # The main text is always at response.content[0].text
    print("━━━ Claude's Reply ━━━")
    print(response.content[0].text)
    print("━━━━━━━━━━━━━━━━━━━━━")

    # ── Step 4: Inspect metadata ───────────────────────────────────────────────
    print("\n📊 Response Metadata:")
    print(f"  Message ID:    {response.id}")
    print(f"  Model used:    {response.model}")
    print(f"  Stop reason:   {response.stop_reason}")
    print(f"  Input tokens:  {response.usage.input_tokens}")
    print(f"  Output tokens: {response.usage.output_tokens}")

    # Calculate approximate cost (Haiku pricing: $1/1M input, $5/1M output)
    input_cost = response.usage.input_tokens * 1.00 / 1_000_000
    output_cost = response.usage.output_tokens * 5.00 / 1_000_000
    total_cost = input_cost + output_cost
    print(f"  Approx cost:   ${total_cost:.6f}")

    # ── Key Concepts ───────────────────────────────────────────────────────────
    print("\n💡 Key Concepts:")
    print('  • response.content[0].text  → Claude\'s reply text')
    print('  • response.stop_reason      → "end_turn" = finished, "max_tokens" = cut off')
    print('  • response.usage            → token counts (determines cost)')
    print('  • The API is stateless      → each call is independent')

    # ── Practice ───────────────────────────────────────────────────────────────
    print("\n" + "─" * 40)
    print("🎯 YOUR TURN — Try modifying this script:")
    print("  1. Change the prompt to ask something else")
    print("  2. Try model='claude-sonnet-4-6' for a smarter response")
    print("  3. Set max_tokens=50 and see what stop_reason you get")
    print("  4. Add a second message and observe token count change\n")


if __name__ == "__main__":
    main()
