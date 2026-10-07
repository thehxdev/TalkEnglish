import os
from typing import Optional
from talkenglish.detector import is_english_prompt
from talkenglish.translator import PromptTranslator

def _load_env_defaults():
    for candidate in (".env", "api"):
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("export "):
                            line = line[7:].strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("\"'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except OSError:
                pass

class PromptMiddleware:
    def __init__(self, translator: Optional[PromptTranslator] = None):
        if translator is None:
            _load_env_defaults()
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
