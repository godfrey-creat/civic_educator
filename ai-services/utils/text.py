import re
from datetime import datetime, timezone


def slugify(text: str, max_length: int = 80) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\-\s]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:max_length] or "entry"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
