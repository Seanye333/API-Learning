"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 2: System Prompts                               ║
║                                                          ║
║   Learn:                                                 ║
║   • What system prompts are and where they go            ║
║   • How to change Claude's persona and behavior          ║
║   • Common patterns: persona, format, task, constraints  ║
╚══════════════════════════════════════════════════════════╝

Run: python 02_system_prompts.py
"""

import os
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


def main():
    print("\n🤖 LESSON 2: System Prompts\n" + "─" * 40)

    client = anthropic.Anthropic()
    question = "Tell me about gravity."

    # ── Example 1: No system prompt (default behavior) ─────────────────────────
    print("\n📋 Example 1: DEFAULT (no system prompt)")
    print(f'  Prompt: "{question}"')

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": question}]
    )
    print(f"\n  Response:\n  {response.content[0].text[:200]}...")

    # ── Example 2: Pirate persona ──────────────────────────────────────────────
    print("\n\n📋 Example 2: PIRATE PERSONA")
    pirate_system = (
        "You are a friendly pirate. Respond to everything in pirate speak. "
        "Say 'Arrr!' frequently and use nautical metaphors."
    )
    print(f'  System: "{pirate_system}"')
    print(f'  Prompt: "{question}"')

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=pirate_system,  # ← system prompt goes in the 'system' parameter
        messages=[{"role": "user", "content": question}]
    )
    print(f"\n  Response:\n  {response.content[0].text[:300]}")

    # ── Example 3: JSON-only output ────────────────────────────────────────────
    print("\n\n📋 Example 3: JSON OUTPUT MODE")
    json_system = (
        "You only respond with valid JSON. Never include prose or markdown. "
        "Always return a JSON object with relevant fields."
    )
    json_prompt = "Create a profile for a fictional character named Luna."
    print(f'  System: "{json_system}"')
    print(f'  Prompt: "{json_prompt}"')

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=json_system,
        messages=[{"role": "user", "content": json_prompt}]
    )
    print(f"\n  Response:\n  {response.content[0].text[:400]}")

    # ── Example 4: Teacher for kids ────────────────────────────────────────────
    print("\n\n📋 Example 4: SIMPLE TEACHER")
    teacher_system = (
        "You are a patient teacher explaining concepts to a 10-year-old. "
        "Use simple language, fun analogies, and short sentences."
    )
    print(f'  System: "{teacher_system}"')
    print(f'  Prompt: "{question}"')

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=teacher_system,
        messages=[{"role": "user", "content": question}]
    )
    print(f"\n  Response:\n  {response.content[0].text[:300]}")

    # ── Key Concepts ───────────────────────────────────────────────────────────
    print("\n\n💡 Key Concepts:")
    print("  • System prompt goes in the 'system' parameter, NOT in 'messages'")
    print("  • It persists for the entire conversation")
    print("  • Use it for: personas, output format, task focus, constraints")
    print("  • Be specific — vague prompts lead to inconsistent results")

    # ── Practice ───────────────────────────────────────────────────────────────
    print("\n" + "─" * 40)
    print("🎯 YOUR TURN — Try these exercises:")
    print('  1. Create a "haiku only" system prompt')
    print('  2. Make Claude respond as a Shakespearean actor')
    print('  3. Make a "code reviewer" that only critiques Python code')
    print("  4. Combine constraints: JSON output + a specific persona\n")


if __name__ == "__main__":
    main()
