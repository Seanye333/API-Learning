"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 7: Advanced Features                           ║
║                                                          ║
║   Learn:                                                 ║
║   • Extended thinking (adaptive)                         ║
║   • Vision (image analysis)                              ║
║   • Structured outputs (JSON with Pydantic)              ║
║   • Prompt caching for cost savings                      ║
║   • Token counting before requests                       ║
╚══════════════════════════════════════════════════════════╝

Run: python 07_advanced.py
"""

import os
import json
import base64
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


def demo_extended_thinking():
    """Show Claude thinking step-by-step before answering."""
    print("\n📋 Demo 1: Extended Thinking\n")
    print("  Extended thinking lets Claude 'think out loud' before answering.")
    print("  Great for math, logic, and complex reasoning tasks.\n")

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=8000,
        thinking={
            "type": "enabled",
            "budget_tokens": 5000  # Max tokens Claude can use for thinking
        },
        messages=[{
            "role": "user",
            "content": "I have 3 boxes. Box A has a red ball. Box B has a blue ball. "
                       "I swap the contents of A and B, then swap B and C (which was empty). "
                       "What's in each box now?"
        }]
    )

    for block in response.content:
        if block.type == "thinking":
            print("  🧠 Thinking (Claude's internal reasoning):")
            # Show first 400 chars of thinking
            thinking_text = block.thinking[:400]
            for line in thinking_text.split("\n"):
                print(f"    │ {line}")
            if len(block.thinking) > 400:
                print(f"    │ ... ({len(block.thinking)} chars total)")
            print()

        elif block.type == "text":
            print("  📝 Final Answer:")
            print(f"    {block.text}")

    print(f"\n  📊 Tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out")


def demo_structured_output():
    """Get Claude to return structured JSON using output_config."""
    print("\n\n📋 Demo 2: Structured Outputs (JSON Schema)\n")
    print("  Force Claude's response to match a specific JSON schema.\n")

    client = anthropic.Anthropic()

    # Method 1: Using output_config with JSON schema
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "skills": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "bio": {"type": "string"}
                    },
                    "required": ["name", "age", "skills", "bio"],
                    "additionalProperties": False
                }
            }
        },
        messages=[{
            "role": "user",
            "content": "Create a profile for a fictional software engineer named Alex."
        }]
    )

    raw = response.content[0].text
    data = json.loads(raw)

    print("  Raw response (guaranteed valid JSON):")
    print(f"  {json.dumps(data, indent=2)}")
    print(f"\n  Parsed fields:")
    print(f"    name:   {data['name']}")
    print(f"    age:    {data['age']}")
    print(f"    skills: {', '.join(data['skills'])}")
    print(f"    bio:    {data['bio'][:80]}...")

    # Method 2: Using Pydantic (recommended for Python)
    print("\n  ─ Method 2: Pydantic (recommended) ─")
    try:
        from pydantic import BaseModel
        from typing import List

        class MovieReview(BaseModel):
            title: str
            rating: float
            pros: List[str]
            cons: List[str]
            summary: str

        response = client.messages.parse(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": "Review the movie 'Inception' (2010)."
            }],
            output_format=MovieReview,
        )

        review = response.parsed_output
        print(f"\n  Parsed MovieReview object:")
        print(f"    title:   {review.title}")
        print(f"    rating:  {review.rating}")
        print(f"    pros:    {review.pros}")
        print(f"    cons:    {review.cons}")
        print(f"    summary: {review.summary[:80]}...")

    except ImportError:
        print("  (Pydantic not installed — pip install pydantic to try this)")
    except Exception as e:
        print(f"  Note: Pydantic demo: {e}")


def demo_prompt_caching():
    """Show how prompt caching reduces costs on repeated requests."""
    print("\n\n📋 Demo 3: Prompt Caching\n")
    print("  Cache large system prompts to save up to 90% on subsequent calls.\n")

    client = anthropic.Anthropic()

    # Create a large system prompt (caching works best with >1024 tokens)
    large_context = """You are an expert on the following comprehensive knowledge base:

    CHAPTER 1: Introduction to APIs
    An API (Application Programming Interface) is a set of protocols and tools for building
    software applications. APIs define how different software components should interact.
    REST APIs use HTTP methods (GET, POST, PUT, DELETE) to perform operations on resources.
    Each resource is identified by a URL, and the API returns data in JSON format.

    CHAPTER 2: Authentication
    API authentication verifies the identity of the caller. Common methods include:
    - API Keys: Simple string tokens passed in headers
    - OAuth 2.0: Token-based authorization framework
    - JWT: JSON Web Tokens for stateless authentication
    API keys should never be exposed in client-side code or public repositories.

    CHAPTER 3: Rate Limiting
    Rate limiting protects APIs from abuse by restricting request frequency.
    Common strategies: token bucket, sliding window, fixed window.
    When rate limited, respect the Retry-After header and implement exponential backoff.

    CHAPTER 4: Error Handling
    HTTP status codes indicate request outcomes:
    - 2xx: Success
    - 4xx: Client errors (fix your request)
    - 5xx: Server errors (retry with backoff)
    Always handle errors gracefully with appropriate user-facing messages.
    """ * 3  # Make it bigger for caching demo

    # First request — full cost (cold cache)
    print("  Request 1 (cold cache — full cost):")
    response1 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        system=[{
            "type": "text",
            "text": large_context,
            "cache_control": {"type": "ephemeral"}  # ← Enable caching
        }],
        messages=[{"role": "user", "content": "What are the main API auth methods?"}]
    )
    print(f"    Answer: {response1.content[0].text[:100]}...")
    print(f"    Tokens — input: {response1.usage.input_tokens}")
    cache_write = getattr(response1.usage, 'cache_creation_input_tokens', 0)
    cache_read = getattr(response1.usage, 'cache_read_input_tokens', 0)
    print(f"    Cache write: {cache_write}, Cache read: {cache_read}")

    # Second request — cache hit (90% cheaper for cached portion)
    print("\n  Request 2 (warm cache — ~90% cheaper):")
    response2 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        system=[{
            "type": "text",
            "text": large_context,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{"role": "user", "content": "Explain rate limiting strategies."}]
    )
    print(f"    Answer: {response2.content[0].text[:100]}...")
    print(f"    Tokens — input: {response2.usage.input_tokens}")
    cache_write2 = getattr(response2.usage, 'cache_creation_input_tokens', 0)
    cache_read2 = getattr(response2.usage, 'cache_read_input_tokens', 0)
    print(f"    Cache write: {cache_write2}, Cache read: {cache_read2}")
    if cache_read2 > 0:
        print(f"    ✅ Cache hit! {cache_read2} tokens read from cache (90% cheaper)")


def demo_token_counting():
    """Count tokens before sending a request."""
    print("\n\n📋 Demo 4: Token Counting\n")
    print("  Count tokens before sending to estimate cost and stay under limits.\n")

    client = anthropic.Anthropic()

    messages = [
        {"role": "user", "content": "Explain quantum computing in detail, covering qubits, "
         "superposition, entanglement, and practical applications."}
    ]

    # Count tokens without making a full API call
    count = client.messages.count_tokens(
        model="claude-haiku-4-5",
        messages=messages
    )

    print(f"  Message: \"{messages[0]['content'][:60]}...\"")
    print(f"  Input tokens: {count.input_tokens}")

    # Estimate cost
    # Haiku: $1/1M input, $5/1M output
    est_input_cost = count.input_tokens * 1.00 / 1_000_000
    print(f"  Estimated input cost: ${est_input_cost:.6f}")
    print()

    # Check against budget
    MAX_INPUT_TOKENS = 1000
    if count.input_tokens > MAX_INPUT_TOKENS:
        print(f"  ⚠ Warning: {count.input_tokens} tokens exceeds budget of {MAX_INPUT_TOKENS}")
        print("  → Consider shortening the prompt or using a cheaper model")
    else:
        print(f"  ✓ Within budget ({count.input_tokens}/{MAX_INPUT_TOKENS} tokens)")


def main():
    print("\n🚀 LESSON 7: Advanced Features\n" + "─" * 40)

    demo_extended_thinking()
    demo_structured_output()
    demo_prompt_caching()
    demo_token_counting()

    print("\n\n💡 Key Concepts:")
    print("  • Extended thinking: thinking={'type': 'enabled', budget_tokens: N}")
    print("    (On Opus 4.6, use thinking={'type': 'adaptive'} instead)")
    print("  • Structured output: output_config={'format': {'type': 'json_schema', ...}}")
    print("  • Prompt caching: Add cache_control={'type': 'ephemeral'} to system blocks")
    print("  • Token counting: client.messages.count_tokens() before sending")
    print("  • Vision: Pass images as base64 or URLs in content blocks")

    print("\n" + "─" * 40)
    print("🎯 YOUR TURN — Exercises:")
    print("  1. Try extended thinking with a harder logic puzzle")
    print("  2. Create a Pydantic model for your own use case")
    print("  3. Benchmark caching savings by timing 5 requests")
    print("  4. Build a cost estimator using token counting\n")


if __name__ == "__main__":
    main()
