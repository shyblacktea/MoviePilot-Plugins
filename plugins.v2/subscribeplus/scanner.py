from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional

from .models import DiagnosisInput, PluginConfig, StaleEpisode
from .sites import SiteResolver


UNCATEGORIZED = "未分类"
TV_TYPE_VALUES = {"电视剧", "tv", "episode"}


def normalize_category(category: Optional[str]) -> str:
    return str(category).strip() if category else UNCATEGORIZED


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
    histories: Iterable[Dict[str, Any]], tmdbid: int, season: int, episode: int
) -> bool:
    for item in histories:
        if int(item.get("tmdbid") or 0) != int(tmdbid):
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


def episodes_in_transfer_history(histories: Iterable[Dict[str, Any]], tmdbid: int, season: int) -> set[int]:
    episodes: set[int] = set()
    for item in histories:
        if int(item.get("tmdbid") or 0) != int(tmdbid):
            continue
        if _season_value(item) != int(season):
            continue
        episodes.update(_episode_numbers(item.get("episodes")))
    return episodes


class SubscriptionScanner:
    def __init__(
        self,
        load_subscribes: Callable[[], List[Any]],
        load_tmdb_episodes: Callable[[int, int, Optional[str]], List[Dict[str, Any]]],
        is_episode_downloaded: Callable[[int, int, int], tuple[bool, str]],
        load_categories: Optional[Callable[[], List[Any]]] = None,
        resolve_subscribe_category: Optional[Callable[[Any], Optional[str]]] = None,
        load_downloaded_episodes: Optional[Callable[[int, int], set[int]]] = None,
    ):
        self.load_subscribes = load_subscribes
        self.load_tmdb_episodes = load_tmdb_episodes
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
            if getattr(subscribe, "state", None) == "R" and self._is_tv(subscribe)
        ]
        return sorted(_ordered_unique(categories))

    def scan(self, config: PluginConfig, site_resolver: SiteResolver, today: Optional[date] = None) -> List[DiagnosisInput]:
        today = today or date.today()
        selected_categories = set(config.selected_categories or self.collect_categories())
        results: List[DiagnosisInput] = []

        for subscribe in self.load_subscribes():
            if getattr(subscribe, "state", None) != "R" or not self._is_tv(subscribe):
                continue
            tmdbid = int(getattr(subscribe, "tmdbid", 0) or 0)
            season = int(getattr(subscribe, "season", 0) or 0)
            if not tmdbid or not season:
                continue
            category = self._subscribe_category(subscribe)
            if category not in selected_categories:
                continue

            stale_episodes = []
            downloaded_episodes = self._downloaded_episodes(tmdbid, season)
            start_episode = int(getattr(subscribe, "start_episode", 0) or 0)
            latest_downloaded_episode = max(downloaded_episodes or {0})
            recent_threshold = max(start_episode - 1, latest_downloaded_episode)
            episode_group = getattr(subscribe, "episode_group", None)
            for episode in self.load_tmdb_episodes(tmdbid, season, episode_group):
                air_date = parse_air_date(episode.get("air_date"))
                episode_number = int(episode.get("episode_number") or episode.get("episode") or 0)
                if not air_date or not episode_number:
                    continue
                if episode_number <= recent_threshold:
                    continue
                if not should_check_episode(air_date, config.delay_days, today):
                    continue
                downloaded, evidence = self.is_episode_downloaded(tmdbid, season, episode_number)
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
                        tmdbid=tmdbid,
                        season=season,
                        category=category,
                        include=str(getattr(subscribe, "include", "") or ""),
                        sites=site_resolver.resolve_for_category(config, category),
                        episodes=stale_episodes,
                    )
                )
        return results

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

    def _downloaded_episodes(self, tmdbid: int, season: int) -> set[int]:
        if not self.load_downloaded_episodes:
            return set()
        try:
            return {int(item) for item in (self.load_downloaded_episodes(tmdbid, season) or set()) if int(item or 0) > 0}
        except Exception:
            return set()
