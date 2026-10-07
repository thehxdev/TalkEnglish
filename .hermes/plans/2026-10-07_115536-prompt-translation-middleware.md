# Plan: Prompt Translation and Refinement Middleware

- **Plan File:** `.hermes/plans/2026-10-07_115536-prompt-translation-middleware.md`
- **Target Workspace:** `/home/hx/src/TalkEnglish`

---

## Goal
Implement a zero-dependency Python middleware that intercepts user prompts, fast-path bypasses English inputs, and translates non-English prompts into precise, entity-preserving technical English for coding agents.

---

## Current Context / Assumptions
- Workspace `/home/hx/src/TalkEnglish` is currently uninitialized.
- Python 3.14+ runtime available; standard library only (no pip dependencies required).
- Middleware targets OpenAI-compatible endpoints (`/v1/chat/completions`) configured via environment variables (`TRANSLATOR_API_KEY`, `TRANSLATOR_API_BASE`, `TRANSLATOR_MODEL`).
- Invariant: User memory mandates TDD verification and minimal heap allocations. Never auto-commit unless instructed.

---

## Architecture / Proposed Approach
- Pre-processing pipeline wrapper sits between raw user input ingestion and agent message context building.
- Heuristic gatekeeper strips code fences, paths, and URLs, then evaluates ASCII letter density to short-circuit English prompts without network I/O.
- Non-English inputs query a lightweight LLM (default `gpt-4o-mini`) with zero temperature and strict invariants preserving code symbols, paths, and syntax unchanged.

---

## Step-by-Step Tasks

### Task 1: Initialize Git Repository and Project Structure
Create root directory layout.

- **Action:** Initialize git repo and directories.
- **Commands:**
```bash
git init
mkdir -p src tests
```
- **Verification:**
```bash
git status
```
- **Expected Output:**
`On branch master` (or `main`) with untracked directory notice.

---

### Task 2: Write Failing Tests for English Heuristic Detector (RED)
Define test suite in `tests/test_detector.py` checking fast-path pass and non-English rejection.

- **File:** `tests/test_detector.py`
```python
import unittest
from src.detector import is_english_prompt

class TestDetector(unittest.TestCase):
    def test_pure_english(self):
        self.assertTrue(is_english_prompt("Fix race condition in thread pool worker"))

    def test_english_with_code_and_paths(self):
        self.assertTrue(is_english_prompt("Refactor `auth_handler` in /var/www/api.py to use `user_id`"))

    def test_persian_prompt(self):
        self.assertFalse(is_english_prompt("تابع `process_data` در مسیر /app/utils.py را بازنویسی کن"))

    def test_chinese_prompt(self):
        self.assertFalse(is_english_prompt("重构 user_service 中的 authenticate 方法"))

    def test_code_only_prompt(self):
        self.assertTrue(is_english_prompt("```python\ndef test(): pass\n```"))

if __name__ == "__main__":
    unittest.main()
```
- **Verification Command:**
```bash
python3 -m unittest tests/test_detector.py
```
- **Expected Output:** `ModuleNotFoundError: No module named 'src.detector'` (Failure).

---

### Task 3: Implement English Heuristic Detector (GREEN)
Implement regex-based stripping and character set density check in `src/detector.py`.

- **File:** `src/detector.py`
```python
import re

CODE_AND_PATH_PATTERN = re.compile(
    r"(`{1,3}[^`]+`{1,3}|https?://\S+|/[a-zA-Z0-9_.-]+|[a-zA-Z0-9_]+\.[a-zA-Z0-9]+)"
)

def is_english_prompt(text: str, ascii_threshold: float = 0.85) -> bool:
    """Detect whether prompt is predominantly English without network overhead."""
    cleaned = CODE_AND_PATH_PATTERN.sub("", text)
    letters = [c for c in cleaned if c.isalpha()]
    if not letters:
        return True
    ascii_letters = [c for c in letters if ord(c) < 128]
    return (len(ascii_letters) / len(letters)) >= ascii_threshold
```
- **Verification Command:**
```bash
python3 -m unittest tests/test_detector.py
```
- **Expected Output:** `OK` (All 5 tests pass).

---

### Task 4: Write Failing Tests for HTTP Translator Client (RED)
Write test suite mocking `urllib.request.urlopen` in `tests/test_translator.py`.

- **File:** `tests/test_translator.py`
```python
import io
import json
import unittest
from unittest.mock import patch
from src.translator import PromptTranslator

class TestTranslator(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_successful_translation(self, mock_urlopen):
        mock_response = io.BytesIO(json.dumps({
            "choices": [{"message": {"content": "Refactor auth_handler in /app/auth.py"}}]
        }).encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = mock_response

        translator = PromptTranslator(api_key="test-key", api_base="http://localhost:8000/v1")
        result = translator.translate("تابع auth_handler در /app/auth.py را بازنویسی کن")

        self.assertEqual(result, "Refactor auth_handler in /app/auth.py")
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_network_failure_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")

        translator = PromptTranslator(api_key="test-key", api_base="http://localhost:8000/v1")
        original = "تابع خراب"
        result = translator.translate(original)

        # Invariant: On network failure, return original prompt safely without crashing
        self.assertEqual(result, original)

if __name__ == "__main__":
    unittest.main()
```
- **Verification Command:**
```bash
python3 -m unittest tests/test_translator.py
```
- **Expected Output:** `ModuleNotFoundError: No module named 'src.translator'` (Failure).

---

### Task 5: Implement HTTP Translator Client (GREEN)
Implement `src/translator.py` using `urllib.request` with exact technical preservation meta-prompt.

- **File:** `src/translator.py`
```python
import json
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

META_PROMPT = """You are an execution-grade prompt translator for a software engineering AI agent.
Your task: Translate incoming developer instructions into concise, technically rigorous English optimized for automated code generation.

INVARIANTS:
1. PRESERVE UNCHANGED:
   - Code blocks (```...```) and inline code (`...`)
   - Identifiers, variables, types, class names, functions (e.g., `user_id`, `AuthToken`)
   - File paths, directory trees, file names (e.g., `/var/log`, `main.py`)
   - CLI commands, flags, shell scripts, regex patterns
   - Git refs, hashes, URLs, domain names, API routes
   - Acronyms (UDP, JWT, TDD, AST, CRUD)

2. TRANSLATION RULES:
   - Map domain idioms to standard SWE terms.
   - Strip polite user conversational padding.
   - Keep imperative mood.
   - Never answer the prompt or add speculative tasks.

OUTPUT FORMAT:
Output strictly the translated prompt text. No markdown wraps, no explanations, no prefixes."""

class PromptTranslator:
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 10
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

    def translate(self, text: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": META_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.0
        }

        req = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        try:
            # ponytail: add exponential backoff retry when intermittent network jitter occurs
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Translation failed: {e}. Falling back to original prompt.")
            return text
```
- **Verification Command:**
```bash
python3 -m unittest tests/test_translator.py
```
- **Expected Output:** `OK` (All tests pass).

---

### Task 6: Write Failing Middleware Pipeline Tests (RED)
Write integration unit tests connecting detector and translator in `tests/test_middleware.py`.

- **File:** `tests/test_middleware.py`
```python
import unittest
from unittest.mock import MagicMock
from src.middleware import PromptMiddleware

class TestPromptMiddleware(unittest.TestCase):
    def test_english_bypasses_translator(self):
        mock_translator = MagicMock()
        middleware = PromptMiddleware(translator=mock_translator)
        
        result = middleware.process("Fix typo in README.md")
        self.assertEqual(result, "Fix typo in README.md")
        mock_translator.translate.assert_not_called()

    def test_non_english_calls_translator(self):
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "Run tests in /tests/test_api.py"
        middleware = PromptMiddleware(translator=mock_translator)
        
        result = middleware.process("تست‌های /tests/test_api.py را اجرا کن")
        self.assertEqual(result, "Run tests in /tests/test_api.py")
        mock_translator.translate.assert_called_once_with("تست‌های /tests/test_api.py را اجرا کن")

if __name__ == "__main__":
    unittest.main()
```
- **Verification Command:**
```bash
python3 -m unittest tests/test_middleware.py
```
- **Expected Output:** `ModuleNotFoundError: No module named 'src.middleware'` (Failure).

---

### Task 7: Implement Prompt Middleware and Runner Entrypoint (GREEN)
Create `src/middleware.py` and top-level runner `src/main.py`.

- **File:** `src/middleware.py`
```python
import os
from typing import Optional
from src.detector import is_english_prompt
from src.translator import PromptTranslator

class PromptMiddleware:
    def __init__(self, translator: Optional[PromptTranslator] = None):
        if translator is None:
            api_key = os.getenv("TRANSLATOR_API_KEY", "")
            api_base = os.getenv("TRANSLATOR_API_BASE", "https://api.openai.com/v1")
            model = os.getenv("TRANSLATOR_MODEL", "gpt-4o-mini")
            self.translator = PromptTranslator(api_key=api_key, api_base=api_base, model=model)
        else:
            self.translator = translator

    def process(self, prompt: str) -> str:
        if is_english_prompt(prompt):
            return prompt
        return self.translator.translate(prompt)
```

- **File:** `src/main.py`
```python
import sys
from src.middleware import PromptMiddleware

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m src.main '<prompt>'", file=sys.stderr)
        sys.exit(1)
    raw_prompt = sys.argv[1]
    middleware = PromptMiddleware()
    print(middleware.process(raw_prompt))

if __name__ == "__main__":
    main()
```

- **Verification Command:**
```bash
python3 -m unittest discover tests
```
- **Expected Output:** `Ran 9 tests in ...s -> OK`.

---

## Tests / Validation Summary
Full regression suite execution:
```bash
python3 -m unittest discover tests -v
```
Expected output:
- `test_code_only_prompt (tests.test_detector.TestDetector) ... ok`
- `test_english_with_code_and_paths (tests.test_detector.TestDetector) ... ok`
- `test_persian_prompt (tests.test_detector.TestDetector) ... ok`
- `test_chinese_prompt (tests.test_detector.TestDetector) ... ok`
- `test_pure_english (tests.test_detector.TestDetector) ... ok`
- `test_network_failure_fallback (tests.test_translator.TestTranslator) ... ok`
- `test_successful_translation (tests.test_translator.TestTranslator) ... ok`
- `test_english_bypasses_translator (tests.test_middleware.TestPromptMiddleware) ... ok`
- `test_non_english_calls_translator (tests.test_middleware.TestPromptMiddleware) ... ok`

---

## Risks, Tradeoffs, and Open Questions
1. **Risk:** Mixed-language prompts (e.g. 90% non-English text with long code snippet).
   - *Mitigation:* Regex strips code blocks prior to ASCII density calculation.
2. **Tradeoff:** Using ASCII density ratio (`>= 0.85`) instead of `langdetect` library keeps project zero-dependency and fast (<0.1ms), but non-English Latin-script languages (German, Spanish, French) may pass through untranslated.
   - *Ceiling:* If multilingual Latin prompts become frequent, add dedicated Unicode character range checks or lightweight n-gram trigram model.
3. **Open Question:** Does agent runtime expose an async event loop for concurrent hook processing, or is synchronous blocking I/O required? Middleware design defaults to synchronous `urllib.request` for universal compatibility.
