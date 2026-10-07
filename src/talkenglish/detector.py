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
