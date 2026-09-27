from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, List, Optional

from .models import DiagnosisInput, PluginConfig, StaleEpisode
from .sites import SiteResolver
from .models import normalize_identity, subscribe_identity


RECENT_GAP_LOOKBACK = 2


UNCATEGORIZED = "未分类"
TV_TYPE_VALUES = {"电视剧", "tv", "episode"}
TMDB_SOURCE_VALUES = {"themoviedb", "tmdb"}


def normalize_category(category: Optional[str]) -> str:
    return str(category).strip() if category else UNCATEGORIZED


def _tmdbid_of(media_source: str, media_id: str) -> int:
    """仅在 TMDB 来源下把原生 ID 暴露为 tmdbid，其他来源返回 0。"""
    if str(media_source or "").strip().lower() not in TMDB_SOURCE_VALUES:
        return 0
    raw = str(media_id or "").strip()
    return int(raw) if raw.isdigit() else 0


def _ordered_unique(values: Iterable[Any]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        category = normalize_category(str(value).strip() if value is not None else None)
        if category in seen:
            continue
        result.append(category)
        seen.add(category)
    return result



def _episode_numbers(raw: Any) -> set[int]:
    if isinstance(raw, int):
        return {raw}
    if isinstance(raw, list):
        return {int(item) for item in raw if str(item).isdigit()}
    result = set()
    for start, end in re.findall(r"(\d+)\s*-\s*(\d+)", str(raw or "")):
        result.update(range(int(start), int(end) + 1))
    for number in re.findall(r"\d+", str(raw or "")):
        result.add(int(number))
    return result


def _season_value(item: Dict[str, Any]) -> Optional[int]:
    raw = item.get("season", item.get("seasons"))
    if isinstance(raw, int):
        return raw
    numbers = re.findall(r"\d+", str(raw or ""))
    return int(numbers[0]) if numbers else None


def episode_in_transfer_history(
    histories: Iterable[Dict[str, Any]], media_source: str, media_id: str, season: int, episode: int
) -> bool:
    for item in histories:
        if not _history_identity_matches(item, media_source, media_id):
            continue
        if _season_value(item) != int(season):
            continue
        if episode in _episode_numbers(item.get("episodes")):
            return True
    return False


def episode_in_seasoninfo(seasoninfo: Any, season: int, episode: int) -> bool:
    return episode in episodes_in_seasoninfo(seasoninfo, season)


def episodes_in_seasoninfo(seasoninfo: Any, season: int) -> set[int]:
    episodes: set[int] = set()
    if isinstance(seasoninfo, dict):
        if str(season) in seasoninfo:
            return _episode_numbers(seasoninfo.get(str(season)))
        if season in seasoninfo:
            return _episode_numbers(seasoninfo.get(season))
        seasoninfo = seasoninfo.get("seasons") or seasoninfo.get("seasoninfo") or seasoninfo.values()
    for item in seasoninfo or []:
        if not isinstance(item, dict):
            continue
        if _season_value(item) != int(season):
            continue
        episodes.update(_episode_numbers(item.get("episodes") or item.get("episode")))
    return episodes


def episodes_in_transfer_history(
    histories: Iterable[Dict[str, Any]], media_source: str, media_id: str, season: int
) -> set[int]:
    episodes: set[int] = set()
    for item in histories:
        if not _history_identity_matches(item, media_source, media_id):
            continue
        if _season_value(item) != int(season):
            continue
        episodes.update(_episode_numbers(item.get("episodes")))
    return episodes


def _history_identity_matches(item: Dict[str, Any], media_source: str, media_id: str) -> bool:
    """按规范媒体身份匹配整理历史，兼容旧记录仅保存 TMDB ID 的形态。"""
    source, identity = normalize_identity(
        item.get("media_source") or item.get("source"),
        item.get("media_id"),
    )
    if source and identity:
        return source == str(media_source or "").strip().lower() and identity == str(media_id or "").strip()
    legacy = str(item.get("tmdbid") or "").strip()
    if legacy and legacy != "0":
        return legacy == str(media_id or "").strip()
    return False


class SubscriptionScanner:
    def __init__(
        self,
        load_subscribes: Callable[[], List[Any]],
        is_episode_downloaded: Callable[[str, str, int, int], tuple[bool, str]] = lambda *_args: (False, ""),
        load_categories: Optional[Callable[[], List[Any]]] = None,
        resolve_subscribe_category: Optional[Callable[[Any], Optional[str]]] = None,
        load_downloaded_episodes: Optional[Callable[[str, str, int], set[int]]] = None,

    ):
        self.load_subscribes = load_subscribes


        self.is_episode_downloaded = is_episode_downloaded
        self.load_categories = load_categories
        self.resolve_subscribe_category = resolve_subscribe_category
        self.load_downloaded_episodes = load_downloaded_episodes

    def collect_categories(self) -> List[str]:
        strategy_categories = self.load_categories() if self.load_categories else []
        if strategy_categories:
            return _ordered_unique([*strategy_categories, UNCATEGORIZED])

        categories = [
            self._subscribe_category(subscribe)
            for subscribe in self.load_subscribes()
            if self._is_tv(subscribe)
        ]
        return sorted(_ordered_unique(categories))

    def scan(
        self,
        config: PluginConfig,
        site_resolver: SiteResolver,
        **_: Any,
    ) -> List[DiagnosisInput]:
        subscribes = list(self.load_subscribes() or [])
        if not subscribes:
            self.last_scan_stats = {
                "total": 0, "non_tv": 0, "paused": 0, "pending": 0,
                "not_active": 0, "unknown_state": 0, "missing_identity": 0,
                "category_skipped": 0, "no_stale": 0, "candidates": 0,
                "state_counts": {}, "skipped": [],
            }
            return []
        selected_categories = set(config.selected_categories or self._collect_categories_from(subscribes))
        results: List[DiagnosisInput] = []
        stats = {
            "total": len(subscribes), "non_tv": 0, "paused": 0,
            "pending": 0, "not_active": 0, "unknown_state": 0,
            "missing_identity": 0, "category_skipped": 0, "no_stale": 0,
            "state_counts": {}, "skipped": [],
        }

        def record_skip(subscribe: Any, reason: str, state: str = "") -> None:
            """记录单条订阅的可诊断跳过原因。"""
            source, identity = subscribe_identity(subscribe)
            raw_season = _field(subscribe, "season", _field(subscribe, "seasons", ""))
            stats["skipped"].append({
                "subscribe_id": _field(subscribe, "id", None),
                "title": str(_field(subscribe, "name", "") or _field(subscribe, "title", "") or ""),
                "media_source": source,
                "media_id": identity,
                "season": raw_season,
                "category": self._subscribe_category(subscribe) if self._is_tv(subscribe) else "",
                "state": state,
                "reason": reason,
            })

        for subscribe in subscribes:
            state = str(_field(subscribe, "state", "") or "").strip().upper()
            if state:
                state_counts = stats["state_counts"]
                state_counts[state] = state_counts.get(state, 0) + 1
            if not self._is_tv(subscribe):
                stats["non_tv"] += 1
                record_skip(subscribe, "non_tv", state)
                continue
            # R 可搜索，P 可搜索但待定；S、N 不进入诊断/原生搜索。
            if state == "S":
                stats["paused"] += 1
                record_skip(subscribe, "paused", state)
                continue
            if state == "P":
                stats["pending"] += 1
            elif state == "N":
                stats["not_active"] += 1
                record_skip(subscribe, "not_active", state)
                continue
            elif state and state != "R":
                stats["unknown_state"] += 1
                record_skip(subscribe, "unknown_state", state)
                continue
            # V3 起订阅主身份为 media_source + media_id；tmdbid 仅作旧宿主回落。
            media_source, media_id = subscribe_identity(subscribe)
            season_raw = getattr(subscribe, "season", 0) or getattr(subscribe, "seasons", 0) or 0
            season_match = re.search(r"\d+", str(season_raw))
            season = int(season_match.group(0)) if season_match else 0
            if not media_id or not season:
                stats["missing_identity"] += 1
                record_skip(subscribe, "missing_identity", state)
                continue
            category = self._subscribe_category(subscribe)
            if category not in selected_categories:
                stats["category_skipped"] += 1
                record_skip(subscribe, "category_skipped", state)
                continue

            stale_episodes = []
            total_episode = int(_field(subscribe, "total_episode", 0) or 0)
            start_episode = int(_field(subscribe, "start_episode", 0) or 1)
            downloaded_episodes = self._downloaded_episodes(media_source, media_id, season)
            if total_episode <= 0:
                stats["missing_episode_metadata"] = stats.get("missing_episode_metadata", 0) + 1
                record_skip(subscribe, "missing_episode_metadata", state)
                continue
            target_episodes = range(max(1, start_episode), total_episode + 1)
            for episode_number in target_episodes:
                if episode_number in downloaded_episodes:
                    continue
                downloaded, evidence = self.is_episode_downloaded(
                    media_source, media_id, season, episode_number
                )
                if downloaded:
                    downloaded_episodes.add(episode_number)
                    continue
                stale_episodes.append(
                    StaleEpisode(
                        season=season,
                        episode=episode_number,
                        evidence=evidence,
                    )
                )

            if stale_episodes:
                results.append(
                    DiagnosisInput(
                        subscribe_id=int(getattr(subscribe, "id", 0) or 0),
                        title=str(getattr(subscribe, "name", "") or getattr(subscribe, "title", "")),
                        tmdbid=_tmdbid_of(media_source, media_id),
                        season=season,
                        category=category,
                        media_source=media_source,
                        media_id=media_id,
                        include=str(getattr(subscribe, "include", "") or ""),
                        sites=site_resolver.resolve_for_category(config, category),
                        episodes=stale_episodes,
                        username=str(getattr(subscribe, "username", "") or ""),
                    )
                )
            else:
                stats["no_stale"] += 1
                record_skip(subscribe, "no_stale", state)
        self.last_scan_stats = stats | {"candidates": len(results)}
        return results

    def _collect_categories_from(self, subscribes: List[Any]) -> List[str]:
        """从已加载的订阅列表收集分类，避免同一轮扫描重复查询订阅。"""
        return sorted(_ordered_unique([
            self._subscribe_category(subscribe)
            for subscribe in subscribes
            if self._is_tv(subscribe)
        ]))

    @staticmethod
    def _is_tv(subscribe: Any) -> bool:
        raw_type = _field(subscribe, "type", "") or ""
        return str(raw_type).strip().lower() in TV_TYPE_VALUES

    def _subscribe_category(self, subscribe: Any) -> str:
        explicit_category = (
            str(_field(subscribe, "media_category", "") or _field(subscribe, "category", "") or "").strip()
        )
        if explicit_category:
            return normalize_category(explicit_category)
        if self.resolve_subscribe_category:
            return normalize_category(self.resolve_subscribe_category(subscribe))
        return UNCATEGORIZED

    def _downloaded_episodes(self, media_source: str, media_id: str, season: int) -> set[int]:
        """读取已下载集号；媒体来源和原生 ID 始终成对传递。"""
        if not self.load_downloaded_episodes:
            return set()
        try:
            return {
                int(item)
                for item in (self.load_downloaded_episodes(media_source, media_id, season) or set())
                if int(item or 0) > 0
            }
        except Exception:
            return set()


def _field(value: Any, name: str, default: Any = None) -> Any:
    """同时支持订阅 ORM 对象与字典快照读取字段。"""
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)
