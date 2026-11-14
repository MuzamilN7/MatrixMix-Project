"""Tiny .env loader so the app and evaluate.py find GROQ_API_KEY the same way.

Order of precedence: a real environment variable wins; otherwise the key is read from a local .env file.
The key is only ever placed in os.environ, never printed or logged.
"""
import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def load_env_key(name: str = "GROQ_API_KEY", path: Path | None = None) -> bool:
    """Load `name` from the .env file into os.environ if it is not already set. Returns True if it is set."""
    if os.environ.get(name):
        return True
    env_file = Path(path) if path else ENV_FILE
    if not env_file.exists():
        return False
    try:
        text = env_file.read_text(encoding="utf-8-sig")  # utf-8-sig tolerates a BOM from Windows editors
    except (OSError, UnicodeDecodeError):
        return False
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() == name:
            value = value.strip().strip("\"'")
            if value:
                os.environ[name] = value
                return True
    return False
