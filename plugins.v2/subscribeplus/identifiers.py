from __future__ import annotations

import re
from importlib import import_module as _import_module
from datetime import datetime
from typing import Any, Dict, Iterable, List


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_media_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"tv", "电视剧", "剧集", "series"}:
        return "tv"
    if text in {"movie", "movies", "电影"}:
        return "movie"
    return "unknown"


def normalize_identifier_line(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def validate_identifier_rule(rule: str) -> bool:
    rule = normalize_identifier_line(rule)
    if not rule or rule.startswith("#"):
        return False
    if " => " in rule and " && " in rule and " >> " in rule and " <> " in rule:
        return True
    if " => " in rule:
        return True
    if " >> " in rule and " <> " in rule:
        return True
    return len(rule) >= 4


def clean_comment_line(comment: str) -> str:
    text = str(comment or "").strip().lstrip("#").strip()
    return f"#{text}" if text else ""


def target_tmdbid(target: Dict[str, Any]) -> int:
    return safe_int(target.get("tmdbid") or target.get("tmdb_id"), 0)


def build_exact_identifier_rule(title: str, target: Dict[str, Any]) -> str:
    raw_title = str(title or "").strip()
    name = str(target.get("name") or target.get("title") or "").strip()
    media_type = normalize_media_type(target.get("media_type") or target.get("type"))
    tmdbid = target_tmdbid(target)
    if not raw_title or not name or not tmdbid or media_type == "unknown":
        raise ValueError("缺少标题、目标名称、媒体类型或 TMDB ID")

    replacement = name
    year = str(target.get("year") or "").strip()
    if len(year) == 4 and year.isdigit():
        replacement += f".{year}"
    replacement += f"{{[tmdbid={tmdbid};type={media_type}"
    if media_type == "tv":
        season = safe_int(target.get("season"), 0)
        episode = safe_int(target.get("episode"), 0)
        if season:
            replacement += f";s={season}"
        if episode:
            replacement += f";e={episode}"
    replacement += "]}"
    return normalize_identifier_line(f"{re.escape(raw_title)} => {replacement}")


def build_identifier_lines(
    title: str,
    target: Dict[str, Any],
    comment: str = "订阅下载增强自动修正识别",
) -> List[str]:
    rule = build_exact_identifier_rule(title, target)
    return [rule]


def dedupe_identifier_lines(existing: Iterable[str], lines: Iterable[str]) -> List[str]:
    existing_set = {str(item or "").rstrip() for item in existing or []}
    added: List[str] = []
    for line in lines or []:
        normalized = str(line or "").rstrip()
        if not normalized or normalized in existing_set or normalized in added:
            continue
        added.append(normalized)
    return added


def refresh_identifier_runtime_cache(import_module=_import_module) -> None:
    metainfo = import_module("app.core.metainfo")
    clear_cache = getattr(metainfo, "clear_rust_parse_options_cache", None)
    if callable(clear_cache):
        clear_cache()


def build_identifier_record(
    *,
    subscribe_id: int,
    title: str,
    candidate_title: str,
    target: Dict[str, Any],
    added: List[str],
    source: str,
    status: str = "success",
    message: str = "",
) -> Dict[str, Any]:
    return {
        "subscribe_id": int(subscribe_id or 0),
        "title": str(title or ""),
        "candidate_title": str(candidate_title or ""),
        "tmdbid": target_tmdbid(target),
        "media_type": normalize_media_type(target.get("media_type") or target.get("type")),
        "season": safe_int(target.get("season"), 0),
        "episode": safe_int(target.get("episode"), 0),
        "added": added,
        "source": source,
        "status": status,
        "message": message,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
