from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


@dataclass
class PluginConfig:
    enabled: bool = False
    delay_days: int = 1
    cron: str = "0 9 * * *"
    selected_categories: List[str] = field(default_factory=list)
    search_sites: List[str] = field(default_factory=list)
    max_scan_subscribes: int = 20
    notify_tg: bool = True
    allow_tg_rule_update: bool = False
    season_pack_cleanup: str = "off"
    season_pack_full_download: bool = False
    candidate_cache_days: int = 3
    notification_suppression_days: int = 3
    custom_release_groups: List[str] = field(default_factory=list)
    custom_platforms: List[str] = field(default_factory=list)
    notify_rules: Dict[str, str] = field(default_factory=dict)
    default_notify_target: str = ""

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, Any]]) -> "PluginConfig":
        raw = raw or {}
        config = cls()
        for key in asdict(config):
            if key in raw:
                setattr(config, key, raw[key])

        config.enabled = bool(config.enabled)
        config.delay_days = max(0, int(config.delay_days or 0))
        config.selected_categories = [str(item) for item in _as_list(config.selected_categories)]
        config.search_sites = [str(item) for item in _as_list(config.search_sites)]
        config.max_scan_subscribes = max(1, int(config.max_scan_subscribes or 1))
        config.notify_tg = bool(config.notify_tg)
        config.allow_tg_rule_update = bool(config.allow_tg_rule_update)
        config.season_pack_full_download = bool(config.season_pack_full_download)
        config.candidate_cache_days = max(0, int(config.candidate_cache_days or 0))
        config.notification_suppression_days = max(0, int(config.notification_suppression_days or 0))
        config.custom_release_groups = [
            str(item).strip()
            for item in _as_list(config.custom_release_groups)
            if str(item).strip()
        ]
        config.custom_platforms = [
            str(item).strip()
            for item in _as_list(config.custom_platforms)
            if str(item).strip()
        ]
        config.default_notify_target = str(config.default_notify_target or "").strip()
        config.notify_rules = {
            str(key): str(value)
            for key, value in (config.notify_rules or {}).items()
            if str(key).strip() and str(value).strip()
        }
        # 兼容旧配置：notify_rules 历史值可能是以分隔符拼出的多目标，统一拆分
        config.notify_rules = {
            str(key): ",".join(
                item for item in re.split(r"[,，]", str(value or ""))
                if item.strip()
            )
            for key, value in config.notify_rules.items()
        }
        from .season_cleanup import normalize_cleanup_mode

        config.season_pack_cleanup = normalize_cleanup_mode(config.season_pack_cleanup)
        config.cron = str(config.cron or "0 9 * * *")
        return config

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StaleEpisode:
    season: int
    episode: int
    air_date: str
    evidence: str = "未在媒体库缓存或整理历史中命中"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnosisInput:
    subscribe_id: int
    title: str
    tmdbid: int
    season: int
    category: str
    include: str = ""
    sites: List[str] = field(default_factory=list)
    episodes: List[StaleEpisode] = field(default_factory=list)
    username: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["episodes"] = [episode.to_dict() for episode in self.episodes]
        return data


@dataclass
class DiagnosisItem:
    subscribe_id: int
    title: str
    tmdbid: int
    season: int
    category: str
    reason: str
    message: str
    episodes: List[Dict[str, Any]] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    sites: List[str] = field(default_factory=list)
    site_names: List[str] = field(default_factory=list)
    source: str = ""
    original_reason: str = ""
    subscription_sites: List[str] = field(default_factory=list)
    subscription_site_names: List[str] = field(default_factory=list)
    subscription_site_progress: List[Dict[str, Any]] = field(default_factory=list)
    search_keyword_suggestion: str = ""
    username: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InteractionState:
    token: str
    diagnosis: Dict[str, Any]
    view: str = "main"
    stack: List[str] = field(default_factory=list)
    expires_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
