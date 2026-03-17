import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DOTENV_PATH = PROJECT_ROOT / ".env"


def _load_dotenv(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(DOTENV_PATH)


def _normalize_telegram_token(value):
    token = (value or "").strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]{20,})", token)
    if match:
        return match.group(1)
    return token


TELEGRAM_TOKEN = _normalize_telegram_token(os.getenv("TELEGRAM_TOKEN", ""))
CHAT_ID = os.getenv("CHAT_ID", "").strip()
DATABASE = os.getenv("DATABASE", "cupones.db").strip() or "cupones.db"
