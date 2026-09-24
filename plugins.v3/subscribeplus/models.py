from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_MEDIA_SOURCE = "themoviedb"


def normalize_identity(media_source: Any, media_id: Any) -> Tuple[str, str]:
    """把媒体来源与原生 ID 归一为字符串身份，任一侧无效时返回空身份。"""
    source = str(media_source or "").strip().lower()
    identity = str(media_id or "").strip()
    if not source or not identity or identity == "0":
        return "", ""
    return source, identity


def subscribe_identity(subscribe: Any) -> Tuple[str, str]:
    """读取订阅的规范媒体身份，兼容旧宿主仅保存 tmdbid 的记录。"""
    source, identity = normalize_identity(
        getattr(subscribe, "media_source", None),
        getattr(subscribe, "media_id", None),
    )
    if source and identity:
        return source, identity
    legacy = str(getattr(subscribe, "tmdbid", 0) or 0).strip()
    if legacy and legacy != "0":
        return DEFAULT_MEDIA_SOURCE, legacy
    return "", ""


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
    notify_tg: bool = True
    allow_tg_rule_update: bool = False
    season_pack_enabled: bool = False
    season_pack_qb_cleanup: str = "off"
    mv3_url: str = ""
    mv3_api_token: str = ""
    candidate_cache_days: int = 3
    notification_suppression_days: int = 3
    custom_release_groups: List[str] = field(default_factory=list)
    custom_platforms: List[str] = field(default_factory=list)


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
        config.notify_tg = bool(config.notify_tg)
        config.allow_tg_rule_update = bool(config.allow_tg_rule_update)
        if "season_pack_enabled" in raw:
            config.season_pack_enabled = bool(raw.get("season_pack_enabled"))
        else:
            legacy_cleanup = str(raw.get("season_pack_cleanup") or "off").strip().lower()
            config.season_pack_enabled = bool(
                raw.get("season_pack_full_download")
                or raw.get("season_pack_replace_enabled")
                or legacy_cleanup != "off"
                or str(raw.get("season_pack_qb_cleanup") or "off").strip().lower() != "off"
            )
        # 兼容旧版“完播整季包替换”开关：统一迁移到最终集整季包策略。
        if "season_pack_qb_cleanup" not in raw and raw.get("season_pack_replace_delete_qb"):
            config.season_pack_qb_cleanup = "task"
        config.mv3_url = str(config.mv3_url or "").strip().rstrip("/")
        config.mv3_api_token = str(config.mv3_api_token or "").strip()
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

        from .season_cleanup import normalize_qb_cleanup_mode

        config.season_pack_qb_cleanup = normalize_qb_cleanup_mode(config.season_pack_qb_cleanup)
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
    # V3 规范媒体身份；tmdbid 仅保留为 TMDB 来源下的兼容字段。
    media_source: str = ""
    media_id: str = ""
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
    media_source: str = ""
    media_id: str = ""
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
    search_stats: Dict[str, int] = field(default_factory=dict)
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
