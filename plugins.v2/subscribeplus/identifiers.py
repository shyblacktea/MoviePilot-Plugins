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


def identifier_title_stem(title: str, media_type: str) -> str:
    raw_title = str(title or "").strip().replace("\\", "/").rsplit("/", 1)[-1]
    raw_title = re.sub(r"\.(?:mkv|mp4|avi|mov|ts|m2ts|strm)$", "", raw_title, flags=re.IGNORECASE)
    if normalize_media_type(media_type) == "tv":
        match = re.search(r"(?i)(?:[.\s_-]+)S\d{1,3}(?:E\d{1,4}(?:-E?\d{1,4})?)?", raw_title)
        if match:
            raw_title = raw_title[: match.start()]
    return raw_title.strip(" ._- ")


def build_force_identifier_rule(title: str, target: Dict[str, Any]) -> str:
    media_type = normalize_media_type(target.get("media_type") or target.get("type"))
    tmdbid = target_tmdbid(target)
    name = str(target.get("name") or target.get("title") or "").strip()
    match_title = identifier_title_stem(title, media_type)
    if not match_title or not name or not tmdbid or media_type == "unknown":
        raise ValueError("缺少标题、TMDB 中文名、媒体类型或 TMDB ID")
    return normalize_identifier_line(f"{match_title} => {name}{{[tmdbid={tmdbid};type={media_type}]}}")


def build_year_identifier_rule(title: str, target: Dict[str, Any]) -> str:
    raw_title = str(title or "").strip().replace("\\", "/").rsplit("/", 1)[-1]
    raw_title = re.sub(r"\.(?:mkv|mp4|avi|mov|ts|m2ts|strm)$", "", raw_title, flags=re.IGNORECASE)
    target_year = str(target.get("year") or "").strip()
    if not (len(target_year) == 4 and target_year.isdigit()):
        raise ValueError("TMDB 没有可用的首播年份")

    season_match = re.search(r"(?i)(.*?[.\s_-]+S\d{1,3})(?:E\d{1,4}(?:-E?\d{1,4})?)?", raw_title)
    if season_match:
        prefix = season_match.group(1).strip(" ._- ")
        search_start = season_match.end()
    else:
        prefix = identifier_title_stem(raw_title, target.get("media_type") or target.get("type"))
        search_start = len(prefix)

    source_year = ""
    for match in re.finditer(r"(?<!\d)((?:19|20)\d{2})(?!\d)", raw_title[search_start:]):
        candidate = match.group(1)
        if candidate != target_year:
            source_year = candidate
            break
    if not source_year:
        raise ValueError(f"文件名中没有找到与 TMDB 年份 {target_year} 不同的年份")
    if not prefix:
        raise ValueError("无法从媒体文件名提取作品名或季号")
    return normalize_identifier_line(f"(?<={prefix}.*?){source_year} => {target_year}")


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
