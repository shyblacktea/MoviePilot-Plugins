from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Dict, List


PLATFORM_KEYWORDS = ["baha", "cr", "crunchyroll", "netflix", "disney", "prime", "b-global"]


def compile_include(pattern: str):
    try:
        return re.compile(pattern or "")
    except re.error as exc:
        raise ValueError(f"include 正则无效：{exc}") from exc


def merge_include(old_include: str, new_pattern: str) -> str:
    parts = [part for part in str(old_include or "").split("|") if part]
    if new_pattern and new_pattern not in parts:
        parts.append(new_pattern)
    return "|".join(parts)


def build_rule_suggestions(candidates: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    found: List[Dict[str, str]] = []
    titles = " ".join(item.get("title") or "" for item in candidates).lower()
    for keyword in PLATFORM_KEYWORDS:
        if keyword in titles:
            value = "cr" if keyword == "crunchyroll" else keyword
            suggestion = {"kind": "platform", "value": value, "pattern": f"(?i){re.escape(value)}"}
            if suggestion not in found:
                found.append(suggestion)
    for site_id in sorted({str(item.get("site") or "") for item in candidates if item.get("site")}):
        suggestion = {"kind": "site", "value": site_id, "pattern": site_id}
        if suggestion not in found:
            found.append(suggestion)
    return found


def build_include_preview(subscribe: Any, pattern: str, source: str = "vue") -> Dict[str, Any]:
    old_include = str(getattr(subscribe, "include", "") or "")
    new_include = merge_include(old_include, pattern)
    compile_include(new_include)
    return {
        "subscribe_id": int(getattr(subscribe, "id")),
        "field": "include",
        "old_include": old_include,
        "new_include": new_include,
        "source": source,
    }


def apply_include_preview(
    preview: Dict[str, Any], update_subscribe: Callable[[int, Dict[str, Any]], Dict[str, Any]]
) -> Dict[str, Any]:
    subscribe_id = int(preview["subscribe_id"])
    compile_include(preview.get("new_include") or "")
    update_subscribe(subscribe_id, {"include": preview.get("new_include") or ""})
    return {
        "subscribe_id": subscribe_id,
        "field": "include",
        "old_value": preview.get("old_include") or "",
        "new_value": preview.get("new_include") or "",
        "source": preview.get("source") or "vue",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
