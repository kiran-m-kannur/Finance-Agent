# Finance Agent

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

Set your OpenAI key 

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o   # optional, defaults to gpt-4o-mini
```

## Run

```bash
uv run main.py
```

This runs whichever session `CURRENT_SESSION` points to in `tools.py`.

## Switching sessions

1. Run Session 1 with `CURRENT_SESSION = 1` in `tools.py`.
2. Flip to `CURRENT_SESSION = 2` and run again. Memory from Session 1 (`data/memory.json`) carries over.

## Reset

To start over, delete the memory file:

```bash
rm data/memory.json
```
