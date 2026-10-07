import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

META_PROMPT = """You are an expert prompt engineer and technical translator specializing in autonomous coding agents.
Your objective: Transform the user's raw input into a clear, precise, and actionable engineering prompt in English, optimized for an autonomous coding agent to execute.

TRANSFORMATION RULES:
1. TARGET AUDIENCE: Autonomous coding agent. Output concise, unambiguous, task-focused software engineering instructions.
2. RESTRUCTURE INTENT (NOT 1:1 TRANSLATION):
   - Convert informal, conversational, or vague descriptions into standard engineering imperatives (e.g., "Implement...", "Refactor...", "Fix bug where...", "Optimize...", "Write unit tests for...").
   - Translate colloquial bug or architecture descriptions into precise technical terms (e.g., "قفل میکنه" -> "deadlock / hang", "اطلاعات خراب ذخیره میشه" -> "data race / race condition").
   - Strip all conversational filler, politeness, and greetings ("لطفاً", "می‌خواستم", "بی‌زحمت", "hello").
   - If input is purely a greeting with no task, output: "Hello. Ready for engineering tasks."
3. PRESERVE TECHNICAL ARTIFACTS VERBATIM:
   - Identifiers, variable names, functions, classes, types (e.g., `user_id`, `AuthHandler`).
   - File paths, directory structures, extensions (e.g., `src/auth.py`, `/etc/config.json`).
   - CLI commands, flags, arguments, code snippets, git references, regex.
   - Enclose technical identifiers, functions, and file paths in backticks (`...`) if not already formatted.
4. STRICT INVARIANTS:
   - Output language: STRICTLY ENGLISH. Never output in the source language.
   - DO NOT EXECUTE OR SOLVE THE TASK. DO NOT WRITE IMPLEMENTATION CODE.
   - DO NOT ADD UNREQUESTED FEATURES OR SPECULATIVE REQUIREMENTS.
   - Output ONLY the refined English prompt. No preamble, no quotes, no explanations."""

class PromptTranslator:
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 15
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _parse_sse(self, raw_text: str) -> str:
        chunks = []
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("data:") and not line.endswith("[DONE]"):
                payload_str = line[5:].strip()
                if payload_str:
                    try:
                        chunk_data = json.loads(payload_str)
                        choices = chunk_data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                chunks.append(content)
                    except json.JSONDecodeError:
                        continue
        return "".join(chunks).strip()

    def translate(self, text: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": META_PROMPT},
                {"role": "user", "content": f"Text to translate to English:\n{text}"}
            ],
            "temperature": 0.0
        }

        req = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        try:
            # ponytail: add exponential backoff retry when intermittent network jitter occurs
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_bytes = resp.read()
                raw_text = raw_bytes.decode("utf-8").strip()

                if raw_text.startswith("data:"):
                    parsed_sse = self._parse_sse(raw_text)
                    if parsed_sse:
                        return parsed_sse

                data = json.loads(raw_text)
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Translation failed: {e}. Falling back to original prompt.")
            return text
