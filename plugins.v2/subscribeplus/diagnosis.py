from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .models import DiagnosisInput, DiagnosisItem


PLATFORM_PATTERNS = [
    ("Baha", r"(?<![A-Za-z0-9])Baha(?![A-Za-z0-9])"),
    ("CR", r"(?<![A-Za-z0-9])(?:CR|Crunchyroll)(?![A-Za-z0-9])"),
    ("Netflix", r"(?<![A-Za-z0-9])Netflix(?![A-Za-z0-9])"),
    ("Disney", r"(?<![A-Za-z0-9])Disney(?:\+|Plus)?(?![A-Za-z0-9])"),
    ("Prime", r"(?<![A-Za-z0-9])Prime(?![A-Za-z0-9])"),
    ("B-Global", r"(?<![A-Za-z0-9])B-Global(?![A-Za-z0-9])"),
]
QUALITY_PATTERNS = [
    "WEB-DL",
    "WEBRip",
    "BluRay",
    "BDRip",
    "HDTV",
]
CODEC_PATTERNS = [
    ("H264", r"(?<![A-Za-z0-9])H\.?264(?![A-Za-z0-9])"),
    ("H265", r"(?<![A-Za-z0-9])H\.?265(?![A-Za-z0-9])"),
    ("HEVC", r"(?<![A-Za-z0-9])HEVC(?![A-Za-z0-9])"),
    ("x264", r"(?<![A-Za-z0-9])x264(?![A-Za-z0-9])"),
    ("x265", r"(?<![A-Za-z0-9])x265(?![A-Za-z0-9])"),
    ("AVC", r"(?<![A-Za-z0-9])AVC(?![A-Za-z0-9])"),
]


@dataclass
class DiagnosisResult:
    reason: str
    candidates: List[Dict[str, Any]]
    message: str


def extract_season_episode(title: str) -> Tuple[Optional[int], Optional[int]]:
    title = title or ""
    match = re.search(r"S(\d{1,2})E(\d{1,3})", title, re.I)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.search(r"(?:第\s*)?(\d{1,3})\s*[集话話]", title, re.I)
    if match:
        return None, int(match.group(1))
    return None, None


def _safe_positive_int(value: Any) -> Optional[int]:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _as_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


def _extract_platforms(title: str) -> List[str]:
    platforms: List[str] = []
    for label, pattern in PLATFORM_PATTERNS:
        if re.search(pattern, title or "", re.I) and label not in platforms:
            platforms.append(label)
    return platforms


def _extract_quality(title: str) -> str:
    for quality in QUALITY_PATTERNS:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(quality)}(?![A-Za-z0-9])", title or "", re.I):
            return quality
    return ""


def _extract_resolution(title: str) -> str:
    match = re.search(r"(?<![A-Za-z0-9])(2160p|1080p|720p|480p)(?![A-Za-z0-9])", title or "", re.I)
    return match.group(1) if match else ""


def _extract_video_codec(title: str) -> str:
    for label, pattern in CODEC_PATTERNS:
        if re.search(pattern, title or "", re.I):
            return label
    return ""


def _extract_release_groups(title: str) -> List[str]:
    text = title or ""
    groups = []
    match = re.search(r"-([A-Za-z][A-Za-z0-9_.-]{1,31})(?:\.[A-Za-z0-9]{2,5})?$", text)
    if match:
        groups.append(match.group(1))
    for match in re.finditer(r"(?<![A-Za-z0-9])(HHWeb|MWeb|ADWeb|FROGWeb|CMCTV|ANi|LoliHouse|cctc)(?![A-Za-z0-9])", text, re.I):
        groups.append(match.group(1))
    result = []
    seen = set()
    for group in groups:
        key = group.lower()
        if key not in seen:
            seen.add(key)
            result.append(group)
    return result


def normalize_search_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("title") or raw.get("name") or raw.get("torrent_name") or ""
    season, episode = extract_season_episode(title)
    raw_episode = raw.get("episode")
    raw_episodes = raw.get("episodes")
    episodes = []
    if isinstance(raw_episodes, list):
        episodes = [number for item in raw_episodes if (number := _safe_positive_int(item))]
        if raw_episode is None and episodes:
            raw_episode = episodes[0]
    upload_factor = raw.get("uploadvolumefactor")
    download_factor = raw.get("downloadvolumefactor")
    volume_factor = _first_non_empty(raw.get("volume_factor"), raw.get("free_text"), raw.get("promotion"))
    if not volume_factor and download_factor is not None:
        try:
            if float(download_factor) == 0:
                volume_factor = "Free"
            elif float(download_factor) < 1:
                volume_factor = f"{int(float(download_factor) * 100)}%"
        except (TypeError, ValueError):
            volume_factor = ""

    return {
        "site": str(raw.get("site") or raw.get("site_id") or ""),
        "site_name": str(raw.get("site_name") or raw.get("site") or ""),
        "title": title,
        "season": int(raw.get("season") or season or 0),
        "episode": int(raw_episode or episode or 0),
        "episodes": episodes,
        "recognized": bool(raw.get("recognized", raw.get("media_info") is not None or raw.get("meta") is not None)),
        "seeders": int(raw.get("seeders") or raw.get("seed_count") or 0),
        "size": raw.get("size") or raw.get("volume") or "",
        "free": bool(raw.get("free") or raw.get("is_free") or download_factor == 0),
        "description": raw.get("description") or "",
        "pubdate": raw.get("pubdate") or "",
        "date_elapsed": raw.get("date_elapsed") or "",
        "freedate": raw.get("freedate") or "",
        "freedate_diff": raw.get("freedate_diff") or "",
        "volume_factor": volume_factor,
        "uploadvolumefactor": upload_factor,
        "downloadvolumefactor": download_factor,
        "labels": _as_string_list(raw.get("labels")),
        "quality": _first_non_empty(raw.get("quality"), _extract_quality(title)),
        "resolution": _first_non_empty(raw.get("resolution"), _extract_resolution(title)),
        "video_codec": _first_non_empty(raw.get("video_codec"), raw.get("codec"), _extract_video_codec(title)),
        "platforms": _as_string_list(raw.get("platforms")) or _extract_platforms(title),
        "release_groups": _as_string_list(raw.get("release_groups")) or _extract_release_groups(title),
        "page_url": raw.get("page_url") or "",
        "enclosure": raw.get("enclosure") or "",
        "peers": int(raw.get("peers") or 0),
        "grabs": int(raw.get("grabs") or 0),
        "download_payload": raw.get("download_payload") or raw,
    }


def _target_episode_set(episode: int | Iterable[int]) -> set[int]:
    if isinstance(episode, int):
        return {int(episode)}
    return {int(item) for item in episode if int(item or 0) > 0}


def _matches_target_episode(item: Dict[str, Any], season: int, target_episodes: set[int]) -> bool:
    item_season = int(item.get("season") or season)
    if item_season not in (0, int(season)):
        return False
    episodes = item.get("episodes")
    if isinstance(episodes, list) and episodes:
        return bool({int(ep) for ep in episodes if int(ep or 0) > 0} & target_episodes)
    return int(item.get("episode") or 0) in target_episodes


def classify_results(
    results: List[Dict[str, Any]], season: int, episode: int | Iterable[int], include_pattern: str
) -> DiagnosisResult:
    normalized = [normalize_search_result(item) for item in results]
    target_episodes = _target_episode_set(episode)
    episode_hits = [
        item
        for item in normalized
        if _matches_target_episode(item, season, target_episodes)
    ]
    if not episode_hits:
        return DiagnosisResult("no_pt_resource", [], "未搜索到覆盖目标集的 PT 资源")

    recognized = [item for item in episode_hits if item.get("recognized")]
    if not recognized:
        return DiagnosisResult("recognition_issue", episode_hits, "资源存在，但无法稳定识别到目标 TMDB 或季集")

    if include_pattern:
        try:
            regex = re.compile(include_pattern, re.I)
        except re.error:
            return DiagnosisResult("rule_blocked", recognized, "订阅包含规则正则无效，资源无法正常匹配")
        passed = [item for item in recognized if regex.search(item.get("title") or "")]
        if not passed:
            return DiagnosisResult("rule_blocked", recognized, "资源存在且识别正确，但被订阅包含规则拦截")

    return DiagnosisResult("downloadable", recognized, "存在可下载候选资源")


class TorrentDiagnoser:
    def __init__(self, search_torrents: Callable[[DiagnosisInput], List[Dict[str, Any]]]):
        self.search_torrents = search_torrents

    def diagnose(self, item: DiagnosisInput) -> DiagnosisItem:
        try:
            raw_results = self.search_torrents(item)
        except Exception as exc:
            return DiagnosisItem(
                subscribe_id=item.subscribe_id,
                title=item.title,
                tmdbid=item.tmdbid,
                season=item.season,
                category=item.category,
                reason="search_failed",
                message=f"PT 搜索失败：{exc}",
                episodes=[episode.to_dict() for episode in item.episodes],
                sites=item.sites,
            )

        target_episodes = [episode.episode for episode in item.episodes]
        diagnosis = classify_results(raw_results, item.season, target_episodes, item.include)
        return DiagnosisItem(
            subscribe_id=item.subscribe_id,
            title=item.title,
            tmdbid=item.tmdbid,
            season=item.season,
            category=item.category,
            reason=diagnosis.reason,
            message=diagnosis.message,
            episodes=[episode.to_dict() for episode in item.episodes],
            candidates=diagnosis.candidates,
            sites=item.sites,
        )
