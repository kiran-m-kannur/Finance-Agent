import json
from datetime import date

from tools import get_account_balance, get_recent_transactions, get_upcoming_bills, set_reminder


def summarize_spending(category: str, start_date: str, end_date: str) -> dict:
    """Sum debits for a category between two YYYY-MM-DD dates (inclusive)."""
    txns = get_recent_transactions(days=365)
    matching = [
        t for t in txns
        if t["category"] == category
        and t["amount"] < 0
        and start_date <= t["date"] <= end_date
    ]
    return {
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
        "total_spent": sum(-t["amount"] for t in matching),
        "transaction_count": len(matching),
    }


def _make_save_to_memory(memory: dict):
    def save_to_memory(kind: str, text: str) -> dict:
        if kind not in ("fact", "commitment"):
            return {"status": "error", "reason": f"unknown kind: {kind!r}"}
        bucket = memory["facts"] if kind == "fact" else memory["commitments"]
        if any(entry["text"] == text for entry in bucket):
            return {"status": "duplicate", "kind": kind}
        bucket.append({"text": text, "saved_on": date.today().isoformat()})
        return {"status": "saved", "kind": kind}
    return save_to_memory


TOOL_SCHEMAS: list[dict] = [
    {"type": "function", "function": {
        "name": "get_recent_transactions",
        "description": "Return raw transactions from the last N days. Use for inspection; for sums, use summarize_spending.",
        "parameters": {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "Look back N days"}},
            "required": ["days"],
        },
    }},
    {"type": "function", "function": {
        "name": "get_account_balance",
        "description": "Return current balances across the user's accounts. Call this when current balance matters — never quote balances from memory.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_upcoming_bills",
        "description": "Return scheduled bills/payments due in the next N days. Call this when upcoming obligations matter.",
        "parameters": {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "Look ahead N days (default 30)"}},
        },
    }},
    {"type": "function", "function": {
        "name": "summarize_spending",
        "description": "Sum spending in a single category between two dates. Use this instead of computing sums yourself.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["rent", "food_delivery", "shopping", "investment", "groceries",
                             "entertainment", "fuel", "salary"],
                    "description": "Transaction category. Must be one of the listed snake_case values exactly.",
                },
                "start_date": {"type": "string", "description": "YYYY-MM-DD, inclusive"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD, inclusive"},
            },
            "required": ["category", "start_date", "end_date"],
        },
    }},
    {"type": "function", "function": {
        "name": "set_reminder",
        "description": "Schedule a reminder for a specific date. Use when the user explicitly asks to be reminded of something on a date.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "YYYY-MM-DD date the reminder should fire."},
                "content": {"type": "string", "description": "What to remind the user about."},
            },
            "required": ["date", "content"],
        },
    }},
    {"type": "function", "function": {
        "name": "save_to_memory",
        "description": "Persist a fact or a commitment about the user across sessions. Use sparingly — only durable facts or things the user actually committed to.",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["fact", "commitment"]},
                "text": {"type": "string", "description": "Short, third-person statement."},
            },
            "required": ["kind", "text"],
        },
    }},
]


def build_dispatch(memory: dict) -> dict:
    return {
        "get_recent_transactions": get_recent_transactions,
        "get_account_balance":     get_account_balance,
        "get_upcoming_bills":      get_upcoming_bills,
        "summarize_spending":      summarize_spending,
        "set_reminder":            set_reminder,
        "save_to_memory":          _make_save_to_memory(memory),
    }


def execute(dispatch: dict, name: str, arguments_json: str) -> str:
    """Run a tool call by name; return JSON string for the tool message content."""
    try:
        args = json.loads(arguments_json) if arguments_json else {}
        result = dispatch[name](**args)
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {e}"}
    return json.dumps(result, default=str)
