# TalkEnglish

Execution-grade prompt translation and engineering refinement middleware for autonomous coding agents (Hermes, Claude Code, Codex).

TalkEnglish intercepts raw, informal, or non-English developer prompts (Persian, Chinese, Arabic, etc.) and transforms them into concise, technically unambiguous English instructions optimized for automated code generation. Already-English prompts automatically bypass the LLM with 0ms latency and $0 token cost.

---

## Features

- **Interactive Textual TUI (Default):** Two-pane terminal interface with live status notifications and zero button clutter.
- **Pure Keyboard-Driven Workflow:**
  - `Ctrl+J` / `Ctrl+Enter` / `F5`: Refine prompt.
  - `Ctrl+K`: Clear input area.
  - `Ctrl+Y`: Copy refined prompt to system clipboard.
  - `Ctrl+C`: Quit application.
- **Cross-Platform Clipboard Integration:**
  - Linux Wayland: native `wl-copy` support.
  - Linux X11: `xclip` / `xsel` support.
  - macOS: `pbcopy`.
  - Windows: `clip.exe`.
  - Terminal fallback: ANSI OSC 52 escape sequences.
- **Preserves Technical Entities Verbatim:** Identifiers, file paths, function names, types, flags, and code snippets are preserved exactly as written and enclosed in backticks.
- **Fast-Path Heuristic:** Strips code and path tokens before checking ASCII ratio; English prompts bypass upstream API calls instantly.
- **Streaming & SSE Resilient:** Handles upstream OpenAI-compatible endpoints regardless of whether they return standard JSON or Server-Sent Events (`text/event-stream`).
- **Headless CLI & Pipeline Ready:** Run in scripts, CI, or shell pipelines with the `--headless` flag or stdin piping.

---

## Installation & Setup

Managed via `uv`:

```bash
git clone https://github.com/thehxdev/TalkEnglish.git
cd TalkEnglish
uv sync
```

### Environment Configuration

Copy the example configuration file and fill in your credentials:

```bash
cp .env.example .env
```

Default variables in `.env`:

```bash
# OpenAI or OpenAI-compatible provider API key
TRANSLATOR_API_KEY="sk-..."

# API Base URL (defaults to https://api.openai.com/v1 if unset)
# Examples:
#   OpenAI:       https://api.openai.com/v1
#   OpenRouter:   https://openrouter.ai/api/v1
#   Local proxy:  http://localhost:20128/v1
#   Ollama:       http://localhost:11434/v1
TRANSLATOR_API_BASE="https://api.openai.com/v1"

# Model identifier (e.g., gpt-4o-mini, ag/gemini-3.8-flash-low)
TRANSLATOR_MODEL="gpt-4o-mini"
```

*Note: TalkEnglish automatically detects and loads `.env` or `api` files in the working directory on startup.*

---

## Usage

### 1. Interactive TUI (Default)

Launch the interface directly in your terminal:

```bash
uv run talkenglish
```

1. Type or paste your prompt into the top pane.
2. Press `Ctrl+J` or `F5` to refine.
3. Press `Ctrl+Y` to copy the refined English prompt to your clipboard.
4. Press `Ctrl+K` to clear and enter a new prompt.

### 2. Headless CLI Mode

Pass prompts as command-line arguments:

```bash
# Explicit headless flag:
uv run talkenglish --headless "سلام، یک تابع برای فاکتوریل بنویس"

# Direct argument (runs headless automatically):
uv run talkenglish "تابع auth_handler در مسیر /app/auth.py را اصلاح کن"
```

### 3. Shell Pipeline / Agent Wrapper

Pipe non-English prompts directly into your coding agent CLI:

```bash
RAW_PROMPT="توی فایل src/server.py وقتی پورت پره ارور هندل کن ولی برنامه کرش نکنه"
REFINED=$(uv run talkenglish --headless "$RAW_PROMPT")

# Pass refined prompt directly to coding agent:
hermes chat -q "$REFINED"
```

Or via stdin pipe:

```bash
echo "یک اسکریپت پایتون برای بررسی وضعیت پورت بنویس" | uv run talkenglish --headless
```

### 4. Python Library Integration

```python
from talkenglish import PromptMiddleware

middleware = PromptMiddleware()

raw_user_input = "یک تابع تست برای لاگین بنویس"
refined_prompt = middleware.process(raw_user_input)

print(refined_prompt)
# Output: Write unit test for `login` function.
```

---

## Architecture

```
TalkEnglish/
├── src/talkenglish/
│   ├── __init__.py       # Package exports
│   ├── detector.py       # Heuristic ASCII/English bypass detector
│   ├── translator.py     # OpenAI-compatible SWE prompt transformer & SSE parser
│   ├── middleware.py     # Pipeline coordinator & environment loader
│   ├── clipboard.py      # Cross-platform clipboard backend (Wayland, X11, macOS, Win)
│   ├── tui.py            # Textual TUI interface & keyboard event handlers
│   └── main.py           # CLI / TUI entrypoint dispatcher
└── tests/                # Test suite (unittest)
```

---

## Running Tests

All functionality is backed by unit tests:

```bash
uv run python -m unittest discover tests -v
```
