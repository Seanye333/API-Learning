"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 4: Streaming                                    ║
║                                                          ║
║   Learn:                                                 ║
║   • Why use streaming (UX + timeout prevention)          ║
║   • Using client.messages.stream() context manager       ║
║   • text_stream for simple use vs raw events for control ║
║   • Getting final message metadata after streaming       ║
╚══════════════════════════════════════════════════════════╝

Run: python 04_streaming.py
"""

import os
import time
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


def demo_non_streaming():
    """Standard non-streaming call for comparison."""
    print("\n📋 Demo 1: Non-Streaming (for comparison)\n")

    client = anthropic.Anthropic()
    prompt = "Write a 4-line poem about coding."

    print(f"  Prompt: \"{prompt}\"")
    print("  Waiting for complete response...")

    start = time.time()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start

    print(f"  (waited {elapsed:.2f}s for the full response)\n")
    print(f"  {response.content[0].text}")
    print(f"\n  → You saw NOTHING until all {response.usage.output_tokens} tokens were ready.")


def demo_text_stream():
    """The simplest streaming approach — text_stream iterator."""
    print("\n\n📋 Demo 2: text_stream (Simple Streaming)\n")

    client = anthropic.Anthropic()
    prompt = "Write a short paragraph about the future of AI."

    print(f"  Prompt: \"{prompt}\"")
    print("  Streaming response:\n")
    print("  ┌─", end="", flush=True)

    token_count = 0
    start = time.time()

    # client.messages.stream() returns a context manager
    with client.messages.stream(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        # text_stream yields each text token as it arrives
        for text in stream.text_stream:
            print(text, end="", flush=True)
            token_count += 1

        # After the loop, get the full final message with metadata
        final = stream.get_final_message()

    elapsed = time.time() - start
    print("\n  └─")
    print(f"\n  ⏱  First token appeared almost instantly!")
    print(f"  📊 Total: {final.usage.output_tokens} tokens in {elapsed:.2f}s")
    print(f"  📊 Stop reason: {final.stop_reason}")


def demo_raw_events():
    """Raw event stream for fine-grained control."""
    print("\n\n📋 Demo 3: Raw Events (Full Control)\n")

    client = anthropic.Anthropic()
    prompt = "What is the speed of light?"

    print(f"  Prompt: \"{prompt}\"")
    print("  Event log:\n")

    with client.messages.stream(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        full_text = ""
        for event in stream:
            # Each event has a .type that tells you what happened

            if event.type == "message_start":
                print(f"  📡 [message_start]  id={event.message.id}")

            elif event.type == "content_block_start":
                block_type = event.content_block.type
                print(f"  📦 [content_block_start]  type={block_type}")

            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    full_text += event.delta.text
                    # Show a dot for each delta (so we don't flood the screen)
                    print(".", end="", flush=True)

            elif event.type == "content_block_stop":
                print(f"\n  📦 [content_block_stop]")

            elif event.type == "message_delta":
                print(f"  🏁 [message_delta]  stop_reason={event.delta.stop_reason}")
                if event.usage:
                    print(f"      output_tokens={event.usage.output_tokens}")

            elif event.type == "message_stop":
                print(f"  🛑 [message_stop]")

    print(f"\n  Full text received: \"{full_text[:100]}...\"")


def demo_streaming_chat():
    """Interactive chat with streaming responses."""
    print("\n\n📋 Demo 4: Streaming Chat\n")
    print("  Type messages. Claude's response streams in real-time.")
    print("  Type 'quit' to exit.\n")

    client = anthropic.Anthropic()
    messages: list[dict] = []

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input or user_input.lower() == "quit":
            if user_input.lower() == "quit":
                print("  Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        print("  Claude: ", end="", flush=True)

        try:
            with client.messages.stream(
                model="claude-haiku-4-5",
                max_tokens=512,
                messages=messages
            ) as stream:
                full_reply = ""
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    full_reply += text

                final = stream.get_final_message()

            messages.append({"role": "assistant", "content": full_reply})
            print(f"\n  ({final.usage.input_tokens} in / {final.usage.output_tokens} out)\n")

        except anthropic.APIError as e:
            print(f"\n  ⚠️ Error: {e}\n")
            messages.pop()


def main():
    print("\n⚡ LESSON 4: Streaming\n" + "─" * 40)

    print("\n  Why streaming?")
    print("  • Users see text immediately (better UX)")
    print("  • Prevents HTTP timeouts on long responses")
    print("  • Same total time, but feels much faster")

    # Demo 1: Non-streaming for comparison
    demo_non_streaming()

    # Demo 2: Simple text_stream
    demo_text_stream()

    # Demo 3: Raw events
    demo_raw_events()

    # Key concepts
    print("\n\n💡 Key Concepts:")
    print("  • Use client.messages.stream() instead of .create()")
    print("  • stream.text_stream → simple iterator for text tokens")
    print("  • Iterate over stream directly → raw events for full control")
    print("  • stream.get_final_message() → complete message with usage stats")
    print("  • Always flush output: print(text, end='', flush=True)")

    print("\n" + "─" * 40)
    print("🎯 YOUR TURN — Exercises:")
    print("  1. Modify demo_text_stream to count tokens per second")
    print("  2. Add extended thinking (thinking={'type': 'adaptive'})")
    print("  3. Time the first-token latency vs total response time")

    # Demo 4: Interactive streaming chat
    print("\n" + "─" * 40)
    print("🎯 Try the streaming chat! (type 'quit' to exit)\n")
    demo_streaming_chat()


if __name__ == "__main__":
    main()
