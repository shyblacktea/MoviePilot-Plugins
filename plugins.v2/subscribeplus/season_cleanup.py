from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Set


CLEANUP_OFF = "off"
CLEANUP_RECORD = "record"
CLEANUP_SOURCE = "source"
CLEANUP_MODES = {CLEANUP_OFF, CLEANUP_RECORD, CLEANUP_SOURCE}

_EPISODE_RE = re.compile(r"E(\d{1,4})(?:\s*[-~]\s*E?(\d{1,4}))?", re.IGNORECASE)
_SEASON_RE = re.compile(r"S(\d{1,2})(?!\s*E\d)", re.IGNORECASE)
_SINGLE_EPISODE_RE = re.compile(r"S\d{1,2}\s*E\d{1,4}", re.IGNORECASE)


@dataclass
class CleanupPlan:
    mode: str = CLEANUP_OFF
    histories: List[Any] = field(default_factory=list)
    reason: str = ""
    episode_numbers: List[int] = field(default_factory=list)

    @property
    def delete_source(self) -> bool:
        return self.mode == CLEANUP_SOURCE

    @property
    def should_cleanup(self) -> bool:
        return self.mode != CLEANUP_OFF and bool(self.histories)


@dataclass
class SeasonPackMatch:
    matched: bool = False
    reason: str = ""
    season: int = 0


def normalize_cleanup_mode(value: Any) -> str:
    if isinstance(value, bool):
        return CLEANUP_SOURCE if value else CLEANUP_OFF
    normalized = str(value or "").strip().lower()
    aliases = {
        "records": CLEANUP_RECORD,
        "record_only": CLEANUP_RECORD,
        "source_file": CLEANUP_SOURCE,
        "delete_source": CLEANUP_SOURCE,
        "delete_src": CLEANUP_SOURCE,
        "true": CLEANUP_SOURCE,
        "false": CLEANUP_OFF,
        "none": CLEANUP_OFF,
        "": CLEANUP_OFF,
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in CLEANUP_MODES else CLEANUP_OFF


def parse_episode_numbers(value: Any) -> Set[int]:
    if value is None:
        return set()
    if isinstance(value, int):
        return {value} if value > 0 else set()
    if isinstance(value, (list, tuple, set)):
        episodes: Set[int] = set()
        for item in value:
            episodes.update(parse_episode_numbers(item))
        return episodes

    text = str(value)
    episodes: Set[int] = set()
    for match in _EPISODE_RE.finditer(text):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if end < start:
            start, end = end, start
        episodes.update(range(start, end + 1))
    return {episode for episode in episodes if episode > 0}


def parse_season_number(value: Any) -> int:
    if isinstance(value, int):
        return value
    match = re.search(r"S?(\d{1,2})", str(value or ""), re.IGNORECASE)
    return int(match.group(1)) if match else 0


def is_season_pack_title(title: str, season: int) -> bool:
    text = str(title or "")
    if not text:
        return False
    if re.search(r"\bComplete\b|全集|全季|整季", text, re.IGNORECASE):
        return True
    if _SINGLE_EPISODE_RE.search(text):
        return False
    for match in _SEASON_RE.finditer(text):
        if int(match.group(1)) == int(season):
            return True
    return False


def _history_title(history: Any) -> str:
    attached_torrent_name = str(getattr(history, "_subscribeplus_torrent_name", "") or "")
    if attached_torrent_name:
        return attached_torrent_name
    torrent_name = str(getattr(history, "torrent_name", "") or "")
    if torrent_name:
        return torrent_name
    parts = [
        getattr(history, "title", ""),
        getattr(history, "src", ""),
    ]
    src_fileitem = getattr(history, "src_fileitem", None)
    if isinstance(src_fileitem, dict):
        parts.append(str(src_fileitem.get("path") or src_fileitem.get("name") or ""))
    return " ".join(str(part) for part in parts if part)


def _same_show_and_season(current: Any, history: Any, season: int) -> bool:
    if getattr(current, "tmdbid", None) and getattr(history, "tmdbid", None) != getattr(current, "tmdbid", None):
        return False
    return parse_season_number(getattr(history, "seasons", None)) == season


def build_season_pack_match(current: Any, total_episode: int) -> SeasonPackMatch:
    season = parse_season_number(getattr(current, "seasons", None))
    if not season:
        return SeasonPackMatch(reason="missing season")
    if not total_episode:
        return SeasonPackMatch(reason="missing total episode", season=season)

    current_episodes = parse_episode_numbers(getattr(current, "episodes", None))
    if int(total_episode) not in current_episodes:
        return SeasonPackMatch(reason="not finale", season=season)

    if not is_season_pack_title(_history_title(current), season):
        return SeasonPackMatch(reason="not season pack", season=season)

    return SeasonPackMatch(matched=True, reason="finale season pack", season=season)


def build_cleanup_plan(current: Any, histories: Iterable[Any], total_episode: int, mode: Any) -> CleanupPlan:
    normalized_mode = normalize_cleanup_mode(mode)
    if normalized_mode == CLEANUP_OFF:
        return CleanupPlan(mode=normalized_mode, reason="disabled")

    match = build_season_pack_match(current, total_episode)
    if not match.matched:
        return CleanupPlan(mode=normalized_mode, reason=match.reason)
    season = match.season

    current_id = getattr(current, "id", None)
    current_hash = str(getattr(current, "download_hash", "") or "")
    selected = []
    selected_episodes: Set[int] = set()
    seen_ids = set()
    valid_range = set(range(1, int(total_episode) + 1))

    for history in histories:
        history_id = getattr(history, "id", None)
        if history_id == current_id or history_id in seen_ids:
            continue
        if current_hash and str(getattr(history, "download_hash", "") or "") == current_hash:
            continue
        if not _same_show_and_season(current, history, season):
            continue
        episodes = parse_episode_numbers(getattr(history, "episodes", None))
        if not episodes or not (episodes & valid_range):
            continue
        selected.append(history)
        selected_episodes.update(episodes & valid_range)
        seen_ids.add(history_id)

    if not selected:
        return CleanupPlan(mode=normalized_mode, reason="no old histories")
    return CleanupPlan(
        mode=normalized_mode,
        histories=selected,
        reason="finale season pack",
        episode_numbers=sorted(selected_episodes),
    )
