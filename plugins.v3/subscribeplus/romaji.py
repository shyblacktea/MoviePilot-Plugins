from __future__ import annotations

import re
from typing import Any, Iterable, List


ROMAJI_PARTICLES = {"no", "ni", "to", "wa", "wo", "ga", "de", "na", "e"}
RESOURCE_WORDS = {
    "web",
    "webdl",
    "bluray",
    "remux",
    "x264",
    "x265",
    "h264",
    "h265",
    "aac",
    "flac",
    "1080p",
    "2160p",
}


def _normalized_words(value: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9]+", value or "")


def _is_latin_title(value: str) -> bool:
    if not value or re.search(r"[^\x00-\x7f]", value):
        return False
    words = _normalized_words(value)
    if len(words) < 3 or any(word.lower() in RESOURCE_WORDS for word in words):
        return False
    if any(re.fullmatch(r"(?:19|20)\d{2}", word) for word in words):
        return False
    if re.search(r"\bS\d{1,2}(?:E\d{1,4})?\b", value, re.I):
        return False
    return True


def _romaji_score(value: str) -> tuple[int, int, int, str]:
    words = _normalized_words(value)
    particles = sum(1 for word in words if word.lower() in ROMAJI_PARTICLES)
    # 有罗马音连接词的标题优先；随后选择较短、较稳定的剧名词干。
    return (-int(particles > 0), len(words), len(value), value.lower())


def select_romaji_aliases(aliases: Iterable[Any], limit: int = 3) -> List[str]:
    unique: List[str] = []
    seen = set()
    for alias in aliases or []:
        value = str(alias or "").strip()
        key = re.sub(r"\s+", " ", value).lower()
        if key in seen or not _is_latin_title(value):
            continue
        seen.add(key)
        unique.append(value)
    unique.sort(key=_romaji_score)
    return unique[: max(0, int(limit or 0))]


def should_try_romaji_fallback(subscribe_keyword: Any, matched_contexts: Iterable[Any]) -> bool:
    return not str(subscribe_keyword or "").strip() and not list(matched_contexts or [])
