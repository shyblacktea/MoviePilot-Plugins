from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .models import DiagnosisInput, DiagnosisItem


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


def normalize_search_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("title") or raw.get("name") or raw.get("torrent_name") or ""
    season, episode = extract_season_episode(title)
    raw_episode = raw.get("episode")
    if raw_episode is None and raw.get("episodes"):
        episodes = raw.get("episodes")
        if isinstance(episodes, list) and episodes:
            raw_episode = episodes[0]
    return {
        "site": str(raw.get("site") or raw.get("site_id") or ""),
        "site_name": str(raw.get("site_name") or raw.get("site") or ""),
        "title": title,
        "season": int(raw.get("season") or season or 0),
        "episode": int(raw_episode or episode or 0),
        "recognized": bool(raw.get("recognized", raw.get("media_info") is not None or raw.get("meta") is not None)),
        "seeders": int(raw.get("seeders") or raw.get("seed_count") or 0),
        "size": raw.get("size") or raw.get("volume") or "",
        "free": bool(raw.get("free") or raw.get("is_free")),
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
