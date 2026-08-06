"""
Article deduplication: exact title-hash (fast) + fuzzy similarity (near-duplicates).
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

FUZZY_THRESHOLD: float = 0.82

_SOURCE_SUFFIX_RE = re.compile(
    r"\s*[-|–]\s*(Reuters|Bloomberg|AP|AFP|CNBC|MarketWatch|WSJ|FT|"
    r"The Wall Street Journal|Financial Times|Business Wire|PR Newswire)\b.*$",
    re.IGNORECASE,
)

# Escaped literal dot before exchange codes
_TICKER_SUFFIX_RE = re.compile(r"(?<=[A-Z0-9])\.(NS|BSE|L|HK|T|TO|AX|DE|FR|BO|SI)\b")

def _canonical(title: str) -> str:
    title = _SOURCE_SUFFIX_RE.sub("", title)
    title = _TICKER_SUFFIX_RE.sub("", title)
    title = unicodedata.normalize("NFKD", title.lower())
    title = re.sub(r"[^\w\s]", "", title)
    return re.sub(r"\s+", " ", title).strip()

def _hash(title: str) -> str:
    return hashlib.md5(_canonical(title).encode()).hexdigest()

def _similar(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if min(len(a), len(b)) / max(len(a), len(b)) < 0.60:
        return False
    return SequenceMatcher(None, a, b).ratio() >= FUZZY_THRESHOLD