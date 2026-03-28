"""
╔══════════════════════════════════════════════════════════╗
║              SETUP CHECKER                               ║
║   Run this first to verify everything is configured.     ║
╚══════════════════════════════════════════════════════════╝

Usage:
  python setup_check.py
"""

import sys
import os


def check_python():
    """Check Python version."""
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 9
    status = "✓" if ok else "✗"
    print(f"  {status} Python version: {v.major}.{v.minor}.{v.micro}", end="")
    if not ok:
        print("  (Need 3.9+)")
    else:
        print()
    return ok


def check_anthropic():
    """Check if anthropic SDK is installed."""
    try:
        import anthropic
        print(f"  ✓ anthropic SDK: v{anthropic.__version__}")
        return True
    except ImportError:
        print("  ✗ anthropic SDK: NOT INSTALLED")
        print("    → Run: pip install anthropic")
        return False


def check_dotenv():
    """Check if python-dotenv is installed."""
    try:
        import dotenv
        print("  ✓ python-dotenv: installed")
        return True
    except ImportError:
        print("  ✗ python-dotenv: NOT INSTALLED")
        print("    → Run: pip install python-dotenv")
        return False


def check_api_key():
    """Check if API key is available."""
    # Try .env file first
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(env_path)
    except ImportError:
        pass

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key and key != "sk-ant-your-key-here":
        masked = key[:10] + "..." + key[-4:]
        print(f"  ✓ API key found: {masked}")
        return True
    else:
        print("  ✗ API key: NOT FOUND")
        print("    → Option 1: Set environment variable: export ANTHROPIC_API_KEY=sk-ant-...")
        print("    → Option 2: Create ../.env file with: ANTHROPIC_API_KEY=sk-ant-...")
        return False


def check_connection():
    """Quick API connectivity test."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(env_path)
    except ImportError:
        pass

    try:
        import anthropic
        client = anthropic.Anthropic()
        # Use token counting (cheap/free) to verify connectivity
        response = client.messages.count_tokens(
            model="claude-haiku-4-5",
            messages=[{"role": "user", "content": "test"}]
        )
        print(f"  ✓ API connection: OK (counted {response.input_tokens} tokens)")
        return True
    except Exception as e:
        print(f"  ✗ API connection: FAILED — {e}")
        return False


def main():
    print("\n╔══════════════════════════════════════════╗")
    print("║     Claude API Tutorial — Setup Check    ║")
    print("╚══════════════════════════════════════════╝\n")

    results = {}

    print("[ Python ]")
    results["python"] = check_python()

    print("\n[ Dependencies ]")
    results["sdk"] = check_anthropic()
    results["dotenv"] = check_dotenv()

    print("\n[ API Key ]")
    results["key"] = check_api_key()

    if all(results.values()):
        print("\n[ Connection Test ]")
        results["conn"] = check_connection()

    # Summary
    print("\n" + "─" * 44)
    passed = sum(results.values())
    total = len(results)

    if passed == total:
        print(f"\n  ✅ All {total} checks passed! You're ready to go.")
        print("     Run: python 01_basic_message.py\n")
    else:
        print(f"\n  ⚠️  {passed}/{total} checks passed. Fix the issues above.")
        if not results.get("sdk"):
            print("     Run: pip install -r requirements.txt\n")
        elif not results.get("key"):
            print("     Set your API key first, then re-run this script.\n")


if __name__ == "__main__":
    main()
