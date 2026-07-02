from __future__ import annotations

import re
import json
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List


PLATFORM_KEYWORDS = ["baha", "cr", "crunchyroll", "netflix", "disney", "prime", "b-global"]
PLATFORM_DISPLAY = {
    "baha": "Baha",
    "cr": "CR",
    "crunchyroll": "CR",
    "netflix": "Netflix",
    "disney": "Disney",
    "prime": "Prime",
    "b-global": "B-Global",
}
SITE_RELEASE_GROUPS = {
    "cctc": "cctc",
}
KNOWN_RELEASE_GROUPS = [
    "HHWeb",
    "MWeb",
    "ADWeb",
    "ANi",
    "LoliHouse",
    "LoliHouse-合集",
    "cctc",
]


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


def _matched_platforms(title: str) -> List[str]:
    platforms: List[str] = []
    for keyword in PLATFORM_KEYWORDS:
        if not re.search(rf"(?<![A-Za-z0-9]){re.escape(keyword)}(?![A-Za-z0-9])", title, re.I):
            continue
        value = PLATFORM_DISPLAY.get(keyword, keyword)
        if value not in platforms:
            platforms.append(value)
    return platforms


def _normalize_release_group(value: str) -> str:
    return str(value or "").strip().strip("[]【】()（）")


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        normalized = _normalize_release_group(value)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def extract_release_groups_from_words(words: Iterable[Any]) -> List[str]:
    groups: List[str] = []
    for raw in words or []:
        text = str(raw or "")
        stripped = _normalize_release_group(text)
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,31}", stripped):
            groups.append(stripped)
        groups.extend(re.findall(r"[【\[]([A-Za-z][A-Za-z0-9_.-]{1,31})[】\]]", text))
        groups.extend(re.findall(r"\(\?=\.\*([A-Za-z][A-Za-z0-9_.-]{1,31})\)", text))
    return _dedupe(groups)


def _matched_release_groups(title: str, site: str, extra_groups: Iterable[str]) -> List[str]:
    groups: List[str] = []
    site_group = SITE_RELEASE_GROUPS.get(str(site or "").strip().lower())
    if site_group:
        groups.append(site_group)
    for group in list(extra_groups or []) + KNOWN_RELEASE_GROUPS:
        normalized = _normalize_release_group(group)
        if normalized and re.search(rf"(?<![A-Za-z0-9]){re.escape(normalized)}(?![A-Za-z0-9])", title, re.I):
            groups.append(normalized)
    return _dedupe(groups)


def _suggestion_pattern(release_group: str = "", platform: str = "") -> str:
    payload = {
        key: value
        for key, value in {"release_group": release_group, "platform": platform}.items()
        if value
    }
    return json.dumps(payload, ensure_ascii=False)


def build_rule_suggestions(
    candidates: List[Dict[str, Any]], release_groups: Iterable[str] | None = None
) -> List[Dict[str, str]]:
    found: List[Dict[str, str]] = []
    extra_groups = _dedupe(release_groups or [])
    for item in candidates:
        site = str(item.get("site") or "").strip()
        title = str(item.get("title") or "")
        platforms = _matched_platforms(title)
        groups = _matched_release_groups(title, site, extra_groups)
        for platform in platforms:
            suggestion = {
                "kind": "platform",
                "value": platform,
                "text": f"添加平台：{platform}",
                "pattern": _suggestion_pattern(platform=platform),
            }
            if suggestion not in found:
                found.append(suggestion)
        for group in groups:
            suggestion = {
                "kind": "release_group",
                "value": group,
                "text": f"添加官组：{group}",
                "pattern": _suggestion_pattern(release_group=group),
            }
            if suggestion not in found:
                found.append(suggestion)
    return found


def _parse_suggestion_pattern(pattern: str) -> Dict[str, str]:
    try:
        payload = json.loads(pattern or "")
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {key: str(value).strip() for key, value in payload.items() if str(value).strip()}


def _add_term_to_lookahead(include: str, term: str, group_index: int) -> str:
    term = str(term or "").strip()
    if not term:
        return include
    matches = list(re.finditer(r"\(\?=\.\*([^)]*)\)", include))
    if not matches:
        return merge_include(include, term)
    if group_index >= len(matches):
        return f"{include}(?=.*{term})"

    match = matches[group_index]
    values = [value for value in match.group(1).split("|") if value]
    if not any(value.lower() == term.lower() for value in values):
        values.append(term)
    replacement = f"(?=.*{'|'.join(values)})"
    return f"{include[:match.start()]}{replacement}{include[match.end():]}"


def merge_include_suggestion(old_include: str, pattern: str) -> str:
    payload = _parse_suggestion_pattern(pattern)
    if not payload:
        return merge_include(old_include, pattern)
    new_include = old_include or ""
    new_include = _add_term_to_lookahead(
        new_include,
        payload.get("release_group", "") or payload.get("site", ""),
        0,
    )
    new_include = _add_term_to_lookahead(new_include, payload.get("platform", ""), 1)
    return new_include


def build_include_preview(subscribe: Any, pattern: str, source: str = "vue") -> Dict[str, Any]:
    old_include = str(getattr(subscribe, "include", "") or "")
    new_include = merge_include_suggestion(old_include, pattern)
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
