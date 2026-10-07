# AGENTS.md — Development Guidelines for TalkEnglish

## Overview
TalkEnglish is a prompt translation and engineering refinement tool for autonomous coding agents. It intercepts non-English prompts, preserves technical entities (code, identifiers, paths), and produces unambiguous technical English instructions. It provides both an interactive Textual TUI and a headless CLI.

---

## Environment & Toolchain
- **Package & Dependency Manager:** `uv`
- **Runtime:** Python >= 3.14
- **Version Control:** Git (never auto-commit changes unless explicitly instructed by the user).
- **Core Dependencies:** Standard library first (`urllib.request`, `json`, `subprocess`, `re`, `shutil`). `textual` for the TUI.

### Essential Commands
```bash
# Sync environment and dependencies
uv sync

# Run complete test suite (must always pass with 0 errors)
uv run python -m unittest discover tests -v

# Run single test module
uv run python -m unittest tests/test_textual_tui.py

# Launch interactive TUI
uv run talkenglish

# Run headless CLI
uv run talkenglish --headless "سلام"
```

---

## Architecture & Code Map
```
src/talkenglish/
├── detector.py      # is_english_prompt(): Heuristic ASCII letter ratio check (threshold: 0.85)
│                    # Strips markdown fences, inline code, URLs, and file paths before calculation.
├── translator.py    # PromptTranslator: Calls OpenAI-compatible /v1/chat/completions endpoint.
│                    # Uses META_PROMPT for agent-oriented prompt refinement.
│                    # Handles both standard application/json and text/event-stream (SSE) chunks.
├── middleware.py    # PromptMiddleware: Auto-loads .env / api files in cwd.
│                    # Bypasses translator if is_english_prompt() is True; otherwise calls PromptTranslator.
├── clipboard.py     # copy_to_system_clipboard(): Cross-platform system clipboard integration.
│                    # Priority: Wayland (wl-copy) -> X11 (xclip/xsel) -> macOS (pbcopy) -> Windows (clip) -> OSC 52.
├── tui.py           # TalkEnglishApp: Textual-based interactive UI.
│                    # Pure keyboard shortcuts: Ctrl+J/F5 (refine), Ctrl+K (clear), Ctrl+Y (copy), Ctrl+C (quit).
│                    # Non-blocking async worker thread (@work(thread=True)) with is_busy state guard.
└── main.py          # Entrypoint: Dispatches to headless CLI if --headless, piped, or prompt arg given;
                     # otherwise launches interactive TUI if stdout/stdin is a TTY.
```

---

## Architectural & Engineering Invariants

1. **Security & Secret Protection:**
   - Never commit or log API keys or secrets.
   - `.env` and `api` files must remain in `.gitignore`.
   - `PromptTranslator` logs network errors gracefully and never exposes credential strings in logs or exceptions.

2. **English Fast-Path ($0 cost, 0ms latency):**
   - Pure English or code-only prompts must never make network calls.
   - Any modification to `is_english_prompt()` must maintain the `CODE_AND_PATH_PATTERN` exclusion to avoid false negatives on English prompts containing foreign paths or symbols.

3. **Strict Preservations in Translation:**
   - Any changes to `META_PROMPT` in `translator.py` must retain the strict invariants:
     - Preserve verbatim: code blocks, inline code, paths, variables, functions, CLI flags, URLs, git refs, and acronyms.
     - Never solve the task, generate implementation code, or converse with the user.
     - Pure greetings must resolve to `Hello. Ready for engineering tasks.`

4. **Resilient Network Parsing:**
   - Proxies and local gateways (e.g., Next.js proxies, LiteLLM, Ollama) may return SSE streams (`data: {"choices": ...}`) even when `"stream": false` is requested.
   - `PromptTranslator._parse_sse` must remain in place to parse raw SSE chunks if standard JSON decoding fails.

5. **Clipboard Fallback Safety:**
   - Subprocess clipboard calls must always specify `timeout=2` to prevent deadlocks on headless or frozen display servers.
   - If native binaries are absent, fallback to terminal ANSI OSC 52 escape sequences (`\033]52;c;...`).

---

## Testing & Quality Discipline
- Strict TDD: Write the failing test first, verify failure, implement minimally, verify pass.
- All new TUI interactions must be covered by async tests in `tests/test_textual_tui.py` using `app.run_test()` and `pilot.press(...)`.
- Clipboard behaviors must be mocked and tested across platforms in `tests/test_clipboard.py`.
