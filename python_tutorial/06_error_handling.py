"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 6: Error Handling                               ║
║                                                          ║
║   Learn:                                                 ║
║   • Different error types the API can return             ║
║   • Which errors are retryable vs fix-your-code          ║
║   • Implementing retry with exponential backoff          ║
║   • SDK auto-retry configuration                         ║
╚══════════════════════════════════════════════════════════╝

Run: python 06_error_handling.py
"""

import os
import time
import random
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


def demo_error_types():
    """Show different types of errors and how to catch them."""
    print("\n📋 Demo 1: Error Types\n")

    # ── 1. AuthenticationError (401) ───────────────────────────────────────
    print("  1. AuthenticationError (invalid API key):")
    try:
        bad_client = anthropic.Anthropic(api_key="sk-ant-invalid-key-12345")
        bad_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
    except anthropic.AuthenticationError as e:
        print(f"     ✗ Caught! Status: 401")
        print(f"     ✗ Message: {e.message}")
        print(f"     → Fix: Check your ANTHROPIC_API_KEY")
        print(f"     → Retryable? NO\n")

    # ── 2. BadRequestError (400) ───────────────────────────────────────────
    print("  2. BadRequestError (invalid request structure):")
    try:
        client = anthropic.Anthropic()
        client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[
                # First message must be 'user', not 'assistant'
                {"role": "assistant", "content": "This is wrong"}
            ]
        )
    except anthropic.BadRequestError as e:
        print(f"     ✗ Caught! Status: 400")
        print(f"     ✗ Message: {e.message[:120]}")
        print(f"     → Fix: First message must be role='user'")
        print(f"     → Retryable? NO\n")

    # ── 3. NotFoundError (404) ─────────────────────────────────────────────
    print("  3. NotFoundError (wrong model name):")
    try:
        client = anthropic.Anthropic()
        client.messages.create(
            model="claude-does-not-exist-99",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
    except anthropic.NotFoundError as e:
        print(f"     ✗ Caught! Status: 404")
        print(f"     ✗ Message: {e.message[:120]}")
        print(f"     → Fix: Use valid model IDs like 'claude-haiku-4-5'")
        print(f"     → Retryable? NO\n")

    # ── Summary ────────────────────────────────────────────────────────────
    print("  ┌────────────┬───────────────────────────────┬───────────┐")
    print("  │ HTTP Code  │ Error Type                    │ Retryable │")
    print("  ├────────────┼───────────────────────────────┼───────────┤")
    print("  │ 400        │ BadRequestError               │    No     │")
    print("  │ 401        │ AuthenticationError            │    No     │")
    print("  │ 403        │ PermissionDeniedError          │    No     │")
    print("  │ 404        │ NotFoundError                  │    No     │")
    print("  │ 429        │ RateLimitError                 │   YES     │")
    print("  │ 500        │ APIStatusError (server)        │   YES     │")
    print("  │ 529        │ APIStatusError (overloaded)    │   YES     │")
    print("  │ —          │ APIConnectionError             │   YES     │")
    print("  └────────────┴───────────────────────────────┴───────────┘")


def demo_comprehensive_handler():
    """Show the recommended error handling pattern."""
    print("\n\n📋 Demo 2: Comprehensive Error Handler\n")

    client = anthropic.Anthropic()

    def call_claude_safely(message: str) -> str:
        """Call Claude with comprehensive error handling."""
        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text

        except anthropic.BadRequestError as e:
            # Your code is wrong — fix the request
            print(f"  ✗ Bad request: {e.message}")
            raise

        except anthropic.AuthenticationError:
            # Wrong API key
            print("  ✗ Invalid API key. Check ANTHROPIC_API_KEY.")
            raise

        except anthropic.PermissionDeniedError:
            # Key doesn't have access to this model/feature
            print("  ✗ Permission denied. Check your API key permissions.")
            raise

        except anthropic.NotFoundError:
            # Typo in model name or invalid endpoint
            print("  ✗ Model not found. Check the model ID.")
            raise

        except anthropic.RateLimitError as e:
            # Too many requests — wait and retry
            retry_after = getattr(e, "retry_after", 60)
            print(f"  ⚠ Rate limited. Should retry after {retry_after}s.")
            raise

        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                # Server error — safe to retry
                print(f"  ⚠ Server error ({e.status_code}). Safe to retry.")
            else:
                print(f"  ✗ API error {e.status_code}: {e.message}")
            raise

        except anthropic.APIConnectionError:
            # Network issue
            print("  ⚠ Network error. Check internet connection.")
            raise

    # Test with a valid request
    print("  Testing with valid request...")
    result = call_claude_safely("Say 'hello' in 3 words.")
    print(f"  ✓ Response: {result}")


def demo_retry_backoff():
    """Implement retry with exponential backoff."""
    print("\n\n📋 Demo 3: Retry with Exponential Backoff\n")

    client = anthropic.Anthropic()

    def call_with_retry(
        message: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ) -> str:
        """
        Call Claude with automatic retry on transient errors.

        Uses exponential backoff with jitter:
        - Attempt 1: wait ~1s
        - Attempt 2: wait ~2s
        - Attempt 3: wait ~4s
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": message}]
                )
                if attempt > 0:
                    print(f"    ✓ Succeeded on attempt {attempt + 1}")
                return response.content[0].text

            except anthropic.RateLimitError as e:
                last_error = e
                should_retry = True

            except anthropic.APIStatusError as e:
                last_error = e
                should_retry = e.status_code >= 500  # Only retry server errors

            except anthropic.APIConnectionError as e:
                last_error = e
                should_retry = True

            except anthropic.APIError as e:
                # All other API errors (400, 401, 403, etc.) — don't retry
                raise

            if should_retry and attempt < max_retries:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                print(f"    ⏳ Attempt {attempt + 1} failed. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            elif not should_retry:
                raise last_error

        raise last_error  # All retries exhausted

    # Test the retry logic with a valid request
    print("  Testing retry logic with valid request...")
    result = call_with_retry("What is 2 + 2?")
    print(f"  ✓ Result: {result}")


def demo_sdk_auto_retry():
    """Show the SDK's built-in retry configuration."""
    print("\n\n📋 Demo 4: SDK Built-in Auto-Retry\n")

    print("  The Anthropic SDK automatically retries 429 and 5xx errors!")
    print("  You can configure it:\n")

    print("  # Default: 2 retries")
    print("  client = anthropic.Anthropic()")
    print()
    print("  # Custom: 5 retries")
    print("  client = anthropic.Anthropic(max_retries=5)")
    print()
    print("  # Disable auto-retry (handle it yourself)")
    print("  client = anthropic.Anthropic(max_retries=0)")
    print()
    print("  # With custom timeout (default: 10 minutes)")
    print("  client = anthropic.Anthropic(timeout=30.0)  # 30 seconds")

    # Actually create a client with custom retries
    client = anthropic.Anthropic(max_retries=3)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say 'OK' in one word."}]
    )
    print(f"\n  ✓ Client with max_retries=3 worked: \"{response.content[0].text}\"")


def demo_validation():
    """Validate inputs before sending to prevent 400 errors."""
    print("\n\n📋 Demo 5: Input Validation\n")

    def validate_request(model: str, max_tokens: int, messages: list) -> list[str]:
        """Validate API request parameters before sending."""
        errors = []

        # Validate model
        valid_models = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"]
        if model not in valid_models:
            errors.append(f"Invalid model '{model}'. Use one of: {valid_models}")

        # Validate max_tokens
        if not isinstance(max_tokens, int) or max_tokens < 1:
            errors.append(f"max_tokens must be a positive integer, got {max_tokens}")
        if max_tokens > 128_000:
            errors.append(f"max_tokens {max_tokens} exceeds maximum (128,000)")

        # Validate messages
        if not messages:
            errors.append("messages array cannot be empty")
        elif messages[0].get("role") != "user":
            errors.append(f"First message must be role='user', got '{messages[0].get('role')}'")

        # Check alternation
        for i in range(1, len(messages)):
            if messages[i]["role"] == messages[i-1]["role"]:
                errors.append(f"Messages must alternate roles. Messages {i-1} and {i} are both '{messages[i]['role']}'")

        return errors

    # Test with invalid input
    test_cases = [
        ("claude-gpt-4", 100, [{"role": "user", "content": "hi"}]),
        ("claude-haiku-4-5", -5, [{"role": "user", "content": "hi"}]),
        ("claude-haiku-4-5", 100, [{"role": "assistant", "content": "hi"}]),
        ("claude-haiku-4-5", 100, [
            {"role": "user", "content": "hi"},
            {"role": "user", "content": "duplicate user"}
        ]),
    ]

    for model, tokens, msgs in test_cases:
        errors = validate_request(model, tokens, msgs)
        if errors:
            print(f"  ✗ validate({model}, {tokens}, ...) → {errors[0]}")
        else:
            print(f"  ✓ validate({model}, {tokens}, ...) → OK")

    # Valid request
    errors = validate_request("claude-haiku-4-5", 1024, [{"role": "user", "content": "Hello"}])
    print(f"  ✓ validate('claude-haiku-4-5', 1024, ...) → {'OK' if not errors else errors}")


def main():
    print("\n⚠️  LESSON 6: Error Handling\n" + "─" * 40)

    demo_error_types()
    demo_comprehensive_handler()
    demo_retry_backoff()
    demo_sdk_auto_retry()
    demo_validation()

    print("\n\n💡 Key Concepts:")
    print("  • 4xx errors = YOUR fault → fix your code, don't retry")
    print("  • 5xx errors = SERVER fault → safe to retry with backoff")
    print("  • 429 = rate limit → retry after delay")
    print("  • SDK auto-retries 429 + 5xx (configure with max_retries)")
    print("  • Always validate input before sending → prevents 400 errors")
    print("  • Use exponential backoff with jitter for custom retries")

    print("\n" + "─" * 40)
    print("🎯 YOUR TURN — Exercises:")
    print("  1. Create a wrapper that logs all errors to a file")
    print("  2. Add a circuit breaker (stop retrying after N failures)")
    print("  3. Build validation for your specific use case")
    print("  4. Try setting max_retries=0 and handling retries yourself\n")


if __name__ == "__main__":
    main()
