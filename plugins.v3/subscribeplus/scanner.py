from __future__ import annotations

import re
from datetime import date, datetime, timedelta
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


def should_check_episode(air_date: date, delay_days: int, today: date) -> bool:
    return air_date + timedelta(days=delay_days) <= today


def parse_air_date(value: Any) -> Optional[date]:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


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
        load_episodes: Callable[..., List[Dict[str, Any]]],
        is_episode_downloaded: Callable[[str, str, int, int], tuple[bool, str]],
        load_categories: Optional[Callable[[], List[Any]]] = None,
        resolve_subscribe_category: Optional[Callable[[Any], Optional[str]]] = None,
        load_downloaded_episodes: Optional[Callable[[str, str, int], set[int]]] = None,
        load_tmdb_episodes: Optional[Callable[..., List[Dict[str, Any]]]] = None,
    ):
        self.load_subscribes = load_subscribes
        # load_tmdb_episodes 为旧参数名，保留以便外部按旧签名构造扫描器。
        self.load_episodes = load_episodes or load_tmdb_episodes
        self.load_tmdb_episodes = self.load_episodes
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
        today: Optional[date] = None,
        force_refresh: bool = False,
    ) -> List[DiagnosisInput]:
        today = today or date.today()
        subscribes = list(self.load_subscribes() or [])
        if not subscribes:
            return []
        selected_categories = set(config.selected_categories or self._collect_categories_from(subscribes))
        results: List[DiagnosisInput] = []
        stats = {"total": len(subscribes), "non_tv": 0, "missing_identity": 0,
                 "category_skipped": 0, "no_stale": 0}

        for subscribe in subscribes:
            if not self._is_tv(subscribe):
                stats["non_tv"] += 1
                continue
            # V3 起订阅主身份为 media_source + media_id；tmdbid 仅作旧宿主回落。
            media_source, media_id = subscribe_identity(subscribe)
            season_raw = getattr(subscribe, "season", 0) or getattr(subscribe, "seasons", 0) or 0
            season_match = re.search(r"\d+", str(season_raw))
            season = int(season_match.group(0)) if season_match else 0
            if not media_id or not season:
                stats["missing_identity"] += 1
                continue
            category = self._subscribe_category(subscribe)
            if category not in selected_categories:
                stats["category_skipped"] += 1
                continue

            stale_episodes = []
            downloaded_episodes = self._downloaded_episodes(media_source, media_id, season)
            start_episode = int(getattr(subscribe, "start_episode", 0) or 0)
            latest_downloaded_episode = max(downloaded_episodes or {0})
            recent_threshold = max(start_episode - 1, latest_downloaded_episode - RECENT_GAP_LOOKBACK)
            episode_group = getattr(subscribe, "episode_group", None)
            for episode in self.load_episodes(
                media_source,
                media_id,
                season,
                episode_group,
                force_refresh=force_refresh,
            ):
                air_date = parse_air_date(episode.get("air_date"))
                episode_number = int(episode.get("episode_number") or episode.get("episode") or 0)
                if not air_date or not episode_number:
                    continue
                if episode_number <= recent_threshold:
                    continue
                if not should_check_episode(air_date, config.delay_days, today):
                    continue
                downloaded, evidence = self.is_episode_downloaded(
                    media_source, media_id, season, episode_number
                )
                if downloaded:
                    downloaded_episodes.add(episode_number)
                    recent_threshold = max(recent_threshold, episode_number)
                    continue
                stale_episodes.append(
                    StaleEpisode(
                        season=season,
                        episode=episode_number,
                        air_date=air_date.isoformat(),
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
        raw_type = getattr(subscribe, "type", "") or ""
        return str(raw_type).strip().lower() in TV_TYPE_VALUES

    def _subscribe_category(self, subscribe: Any) -> str:
        explicit_category = (
            str(getattr(subscribe, "media_category", "") or getattr(subscribe, "category", "") or "").strip()
        )
        if explicit_category:
            return normalize_category(explicit_category)
        if self.resolve_subscribe_category:
            return normalize_category(self.resolve_subscribe_category(subscribe))
        return UNCATEGORIZED

    def _downloaded_episodes(self, media_source: str, media_id: str, season: int) -> set[int]:
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
