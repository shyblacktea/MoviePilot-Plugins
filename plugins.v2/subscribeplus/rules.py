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


def _site_pattern(site_id: str, site_name: str = "") -> str:
    payload = {"site_id": str(site_id)}
    if site_name:
        payload["site_name"] = str(site_name)
    return json.dumps(payload, ensure_ascii=False)


def _normalize_site_id(value: Any) -> int | None:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d+", text):
        return None
    return int(text)


def _normalize_site_ids(value: Any) -> List[int]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    result: List[int] = []
    seen = set()
    for item in values:
        site_id = _normalize_site_id(item)
        if site_id is None or site_id in seen:
            continue
        seen.add(site_id)
        result.append(site_id)
    return result


def _site_names(site_ids: List[int], selected_id: int | None = None, selected_name: str = "") -> List[str]:
    names = []
    for site_id in site_ids:
        if selected_id is not None and site_id == selected_id and selected_name:
            names.append(selected_name)
        else:
            names.append(str(site_id))
    return names


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
        site_id = _normalize_site_id(site)
        if site_id is not None:
            site_name = str(item.get("site_name") or site_id).strip()
            suggestion = {
                "kind": "site",
                "value": str(site_id),
                "text": f"添加PT站点：{site_name}",
                "pattern": _site_pattern(str(site_id), site_name),
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
    if re.fullmatch(r"\d+", str(pattern or "").strip()):
        raise ValueError("规则建议无效：不能把站点 ID 直接写入包含规则")
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


def build_site_preview(subscribe: Any, site_id: str, site_name: str = "", source: str = "vue") -> Dict[str, Any]:
    normalized_site_id = _normalize_site_id(site_id)
    if normalized_site_id is None:
        raise ValueError("站点建议无效：缺少可写入订阅站点的 PT 站点 ID")
    old_sites = _normalize_site_ids(getattr(subscribe, "sites", None))
    new_sites = list(old_sites)
    if normalized_site_id not in new_sites:
        new_sites.append(normalized_site_id)
    clean_site_name = str(site_name or normalized_site_id).strip()
    return {
        "subscribe_id": int(getattr(subscribe, "id")),
        "field": "sites",
        "old_sites": old_sites,
        "new_sites": new_sites,
        "old_site_names": _site_names(old_sites, normalized_site_id, clean_site_name),
        "new_site_names": _site_names(new_sites, normalized_site_id, clean_site_name),
        "source": source,
    }


def build_rule_preview(subscribe: Any, pattern: str, source: str = "vue") -> Dict[str, Any]:
    payload = _parse_suggestion_pattern(pattern)
    clean_pattern = str(pattern or "").strip()
    site_id = payload.get("site_id") or (clean_pattern if re.fullmatch(r"\d+", clean_pattern) else "")
    if site_id:
        return build_site_preview(subscribe, site_id, payload.get("site_name", ""), source=source)
    return build_include_preview(subscribe, pattern, source=source)


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


def apply_site_preview(
    preview: Dict[str, Any], update_subscribe: Callable[[int, Dict[str, Any]], Dict[str, Any]]
) -> Dict[str, Any]:
    subscribe_id = int(preview["subscribe_id"])
    new_sites = _normalize_site_ids(preview.get("new_sites"))
    update_subscribe(subscribe_id, {"sites": new_sites})
    old_value = ", ".join(preview.get("old_site_names") or [str(item) for item in preview.get("old_sites") or []])
    new_value = ", ".join(preview.get("new_site_names") or [str(item) for item in new_sites])
    return {
        "subscribe_id": subscribe_id,
        "field": "sites",
        "old_value": old_value,
        "new_value": new_value,
        "source": preview.get("source") or "vue",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def apply_rule_preview(
    preview: Dict[str, Any], update_subscribe: Callable[[int, Dict[str, Any]], Dict[str, Any]]
) -> Dict[str, Any]:
    if preview.get("field") == "sites":
        return apply_site_preview(preview, update_subscribe)
    return apply_include_preview(preview, update_subscribe)
