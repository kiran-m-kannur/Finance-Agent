"""Entry point. Run the session indicated by CURRENT_SESSION in tools.py.

  python main.py

To switch sessions, flip CURRENT_SESSION = 1 -> 2 in tools.py.

Requires OPENAI_API_KEY to be set. Optionally override OPENAI_MODEL
(defaults to gpt-4o-mini).
"""

from agent.loop import run_session
from tools import CURRENT_SESSION

SESSION_TURNS: dict[int, list[str]] = {
    1: [
        "I just got my salary credited. Help me figure out how much I can realistically save this month.",
        "I feel like I'm spending too much on food delivery. How much did I actually spend on it last month?",
        "Okay that's worse than I thought. Let's say I want to cut that in half AND put aside ₹30,000 for my house fund this month — is that realistic given my upcoming bills?",
        "Got it. Remind me to actually transfer the ₹30,000 to my house fund on the 25th.",
    ],
    2: [
        "Hey, my colleague is selling his MacBook for ₹80,000, barely used. I've been wanting to upgrade. Should I buy it?",
    ],
}

# The scenario is fixed in time; pin "today" so tool data and prompt agree.
SESSION_DATES = {1: "2025-11-03", 2: "2025-11-06"}


def main() -> None:
    run_session(SESSION_TURNS[CURRENT_SESSION], today=SESSION_DATES[CURRENT_SESSION])


if __name__ == "__main__":
    main()
