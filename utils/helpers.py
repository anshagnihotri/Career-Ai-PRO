"""
utils/helpers.py — Shared utility functions for CareerAI Pro.
"""

import html
import re
import textwrap
from datetime import datetime
from typing import Any


def sanitize_text(text: Any) -> str:
    """Escape HTML special characters to prevent XSS in st.markdown."""
    return html.escape(str(text or ""))


def chunk_list(lst: list, size: int) -> list[list]:
    """Split a list into chunks of at most `size` items."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def initials(name: str, max_chars: int = 2) -> str:
    """Return uppercase initials from a company/person name."""
    if not name:
        return "??"
    words = name.strip().split()
    if len(words) == 1:
        return words[0][:max_chars].upper()
    return "".join(w[0] for w in words[:max_chars]).upper()


def format_chat_export(messages: list[dict]) -> str:
    """Format chat messages as a plain-text transcript."""
    lines = ["CareerAI Pro — Chat Export", "=" * 40, ""]
    for msg in messages:
        role = "You" if msg["role"] == "user" else "CareerAI"
        ts = msg.get("created_at", "")
        lines.append(f"[{ts}] {role}:")
        lines.append(textwrap.fill(msg["content"], width=80))
        lines.append("")
    return "\n".join(lines)


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate a string and add ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def percentage(part: int, total: int) -> int:
    if total == 0:
        return 0
    return round((part / total) * 100)


def clean_text(text: str) -> str:
    """Remove excess whitespace and control characters."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def current_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
