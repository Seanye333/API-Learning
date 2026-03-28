"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 3: Multi-Turn Conversations                     ║
║                                                          ║
║   Learn:                                                 ║
║   • The API is stateless — you must send full history    ║
║   • How to build and maintain conversation history       ║
║   • Role alternation rules (user → assistant → user)     ║
║   • Building an interactive chatbot                      ║
╚══════════════════════════════════════════════════════════╝

Run: python 03_conversations.py
"""

import os
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


def demo_stateless():
    """Demonstrate that the API has no memory between calls."""
    print("\n📋 Demo: The API is Stateless\n")

    client = anthropic.Anthropic()

    # Call 1: Tell Claude our name
    print("  Call 1: 'My name is Alice.'")
    r1 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "My name is Alice."}]
    )
    print(f"  Claude: {r1.content[0].text}\n")

    # Call 2: Ask Claude our name — WITHOUT history
    print("  Call 2 (no history): 'What's my name?'")
    r2 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "What's my name?"}]
    )
    print(f"  Claude: {r2.content[0].text}")
    print("  ❌ Claude doesn't know — each call is independent!\n")

    # Call 3: Ask again — WITH full history
    print("  Call 3 (with history): sending all previous messages")
    r3 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": r1.content[0].text},
            {"role": "user", "content": "What's my name?"}
        ]
    )
    print(f"  Claude: {r3.content[0].text}")
    print("  ✅ Claude remembers because we sent the full history!")


def demo_conversation_class():
    """Reusable conversation manager pattern."""
    print("\n\n📋 Demo: Conversation Manager\n")

    client = anthropic.Anthropic()

    class Conversation:
        """Manages multi-turn conversation history."""

        def __init__(self, system: str = None):
            self.client = client
            self.system = system
            self.messages: list[dict] = []

        def send(self, user_message: str) -> str:
            """Send a message and return Claude's reply."""
            self.messages.append({"role": "user", "content": user_message})

            response = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=512,
                **({"system": self.system} if self.system else {}),
                messages=self.messages
            )

            reply = response.content[0].text
            self.messages.append({"role": "assistant", "content": reply})

            return reply

        @property
        def turn_count(self):
            return len(self.messages) // 2

        @property
        def token_estimate(self):
            """Rough token estimate (1 token ≈ 4 chars)."""
            total_chars = sum(len(m["content"]) for m in self.messages)
            return total_chars // 4

    # Use the conversation manager
    chat = Conversation(system="You are a helpful Python tutor. Be concise.")

    exchanges = [
        "What is a list comprehension?",
        "Show me an example with filtering.",
        "Can I nest them?"
    ]

    for msg in exchanges:
        print(f"  You:    {msg}")
        reply = chat.send(msg)
        print(f"  Claude: {reply[:200]}{'...' if len(reply) > 200 else ''}")
        print(f"  (Turn {chat.turn_count}, ~{chat.token_estimate} tokens)\n")


def demo_interactive_chat():
    """Interactive chat loop — the user types messages live."""
    print("\n\n📋 Demo: Interactive Chat")
    print("  Type messages below. Commands: 'quit', 'history', 'clear'\n")

    client = anthropic.Anthropic()
    messages: list[dict] = []
    system_prompt = "You are a helpful assistant. Keep answers under 3 sentences."

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("  Goodbye!")
            break

        if user_input.lower() == "history":
            print(f"\n  📜 Conversation history ({len(messages)} messages):")
            for m in messages:
                role = "You" if m["role"] == "user" else "Claude"
                print(f"    [{role}] {m['content'][:80]}...")
            print()
            continue

        if user_input.lower() == "clear":
            messages.clear()
            print("  🗑️  History cleared.\n")
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=512,
                system=system_prompt,
                messages=messages
            )

            reply = response.content[0].text
            messages.append({"role": "assistant", "content": reply})

            print(f"  Claude: {reply}")
            print(f"  ({response.usage.input_tokens} in / {response.usage.output_tokens} out tokens)\n")

        except anthropic.APIError as e:
            print(f"  ⚠️ Error: {e}\n")
            messages.pop()  # Remove the failed user message


def main():
    print("\n🔄 LESSON 3: Multi-Turn Conversations\n" + "─" * 40)

    # Part 1: Show stateless nature
    demo_stateless()

    # Part 2: Conversation manager pattern
    demo_conversation_class()

    # Part 3: Interactive chat
    print("\n" + "─" * 40)
    print("💡 Key Concepts:")
    print("  • API is STATELESS — send full history every time")
    print("  • Messages must alternate: user → assistant → user")
    print("  • First message must be 'user'")
    print("  • Token count grows with conversation length")
    print("  • Max context: 200K tokens (~150K words)")

    print("\n" + "─" * 40)
    print("🎯 Let's try interactive chat! (type 'quit' to exit)\n")
    demo_interactive_chat()


if __name__ == "__main__":
    main()
