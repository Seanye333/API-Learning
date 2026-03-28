"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║       Claude API Tutorial — Python Edition               ║
║       Interactive Lesson Runner                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Run: python run_tutorial.py

This script lets you pick which lesson to run from a menu.
You can also run each lesson directly: python 01_basic_message.py
"""

import os
import sys
import subprocess


LESSONS = [
    ("setup_check.py",             "Setup Check",             "Verify your environment is ready"),
    ("00_rest_fundamentals.py",    "REST Fundamentals",       "GET, POST, PUT, PATCH, DELETE basics"),
    ("01_basic_message.py",        "Your First API Call",     "Send a message, read the response"),
    ("02_system_prompts.py",       "System Prompts",          "Control Claude's persona and behavior"),
    ("03_conversations.py",        "Multi-Turn Conversations","Build chatbots with history management"),
    ("04_streaming.py",            "Streaming",               "Display responses in real-time"),
    ("05_tool_use.py",             "Tool Use",                "Give Claude functions to call"),
    ("06_error_handling.py",       "Error Handling",           "Handle errors gracefully"),
    ("07_advanced.py",             "Advanced Features",        "Thinking, structured output, caching"),
    ("08_autodesk_acc.py",         "Autodesk ACC Build",       "Two-legged OAuth + projects, issues, RFIs"),
]


def print_banner():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║     Claude API Tutorial — Python Edition     ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()


def print_menu():
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  Choose a lesson:                                   │")
    print("  ├─────────────────────────────────────────────────────┤")
    for i, (_, title, desc) in enumerate(LESSONS):
        num = "0" if i == 0 else str(i)
        prefix = "  " if i == 0 else f"L{i}"
        line = f"  │  {num}. [{prefix}] {title:<28s} {desc[:22]:>22s} │"
        print(line)
    print("  ├─────────────────────────────────────────────────────┤")
    print("  │  q. Quit                                            │")
    print("  └─────────────────────────────────────────────────────┘")
    print()


def run_lesson(idx: int):
    script = LESSONS[idx][0]
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)

    if not os.path.exists(script_path):
        print(f"  ✗ Script not found: {script_path}")
        return

    print(f"\n  ▶ Running: {script}")
    print("  " + "═" * 50)

    try:
        subprocess.run([sys.executable, script_path], check=False)
    except KeyboardInterrupt:
        print("\n\n  (Interrupted)")

    print("  " + "═" * 50)


def main():
    print_banner()

    while True:
        print_menu()
        try:
            choice = input("  Enter choice (0-9 or q): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye!")
            break

        if choice in ("q", "quit", "exit"):
            print("\n  Goodbye! Happy coding!\n")
            break

        try:
            idx = int(choice)
            if 0 <= idx < len(LESSONS):
                run_lesson(idx)
                print()
                input("  Press Enter to return to menu...")
            else:
                print(f"  ✗ Invalid choice. Enter 0-{len(LESSONS)-1} or q.\n")
        except ValueError:
            print("  ✗ Invalid input. Enter a number or 'q'.\n")


if __name__ == "__main__":
    main()
