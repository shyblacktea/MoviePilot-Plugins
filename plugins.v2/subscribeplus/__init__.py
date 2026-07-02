from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from fastapi import Body
except Exception:  # pragma: no cover - local unit tests may not install FastAPI
    def Body(default=None, **kwargs):
        return default

try:
    from apscheduler.triggers.cron import CronTrigger
except Exception:  # pragma: no cover - MoviePilot runtime dependency
    CronTrigger = None

try:
    from app.core.event import eventmanager
    from app.log import logger
    from app.plugins import _PluginBase
    from app.schemas.types import EventType, MediaType, NotificationType, SystemConfigKey
except Exception:  # pragma: no cover - lets local unit tests import this package
    eventmanager = None
    NotificationType = None

    class _FallbackLogger:
        @staticmethod
        def info(*args, **kwargs):
            pass

        @staticmethod
        def warning(*args, **kwargs):
            pass

        @staticmethod
        def error(*args, **kwargs):
            pass

    logger = _FallbackLogger()

    class _PluginBase:
        def get_data_path(self, plugin_id: Optional[str] = None) -> Path:
            path = Path(__file__).resolve().parent / ".data"
            path.mkdir(parents=True, exist_ok=True)
            return path

        def post_message(self, **kwargs):
            return None

        def update_config(self, config: dict, plugin_id: Optional[str] = None) -> bool:
            return True

    class EventType:
        MessageAction = "message.action"

    class MediaType:
        TV = type("TV", (), {"value": "电视剧"})()

    class SystemConfigKey:
        IndexerSites = "IndexerSites"
        CustomIdentifiers = "CustomIdentifiers"

from .diagnosis import TorrentDiagnoser
from .models import DiagnosisInput, PluginConfig
from .rules import (
    apply_include_preview,
    build_include_preview,
    build_rule_suggestions,
    extract_release_groups_from_words,
)
from .scanner import SubscriptionScanner, episode_in_seasoninfo, episode_in_transfer_history
from .sites import SiteResolver
from .storage import JsonStore
from .telegram import (
    build_main_menu,
    build_resource_menu,
    build_rule_confirm_menu,
    build_rule_done_menu,
    build_rule_menu,
    make_token,
    render_notification_text,
    render_rule_preview_text,
)


PLUGIN_ID = "SubscribePlus"


class SubscribePlus(_PluginBase):
    plugin_name = "订阅下载增强"
    plugin_desc = "检测已播出但未入库的电视剧订阅，并分析 PT 资源、识别和订阅规则原因。"
    plugin_icon = "tv.png"
    plugin_version = "0.2"
    plugin_author = "shyblacktea,Codex"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "subscribeplus_"
    plugin_order = 998
    auth_level = 1

    _config: Dict[str, Any] = {}
    _plugin_config: PluginConfig = PluginConfig()
    _store: Optional[JsonStore] = None
    _site_resolver: Optional[SiteResolver] = None
    _scanner: Optional[SubscriptionScanner] = None
    _diagnoser: Optional[TorrentDiagnoser] = None
    _download_contexts: Dict[str, Any] = {}
    _category_cache: Dict[str, str] = {}
    _custom_release_groups_cache: List[str] = []

    def init_plugin(self, config: dict = None):
        self._config = config or {}
        self._plugin_config = PluginConfig.from_dict(self._config)
        self._store = JsonStore(self.get_data_path(PLUGIN_ID))
        self._site_resolver = SiteResolver(self._load_moviepilot_search_sites)
        self._scanner = SubscriptionScanner(
            load_subscribes=self._load_subscribes,
            load_tmdb_episodes=self._load_tmdb_episodes,
            is_episode_downloaded=self._is_episode_downloaded,
            load_categories=self._load_tv_categories,
            resolve_subscribe_category=self._resolve_subscribe_category,
        )
        self._diagnoser = TorrentDiagnoser(self._search_torrents)
        self._download_contexts = {}
        self._category_cache = {}
        self._custom_release_groups_cache = []

    def get_state(self) -> bool:
        return bool(self._plugin_config.enabled)

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        return "vue", "dist/assets"

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        if not self._plugin_config.enabled:
            return []
        trigger = self._plugin_config.cron
        if CronTrigger:
            try:
                trigger = CronTrigger.from_crontab(self._plugin_config.cron)
            except Exception as exc:
                logger.warning(f"订阅下载增强 Cron 配置无效，使用每日 9 点：{exc}")
                trigger = CronTrigger.from_crontab("0 9 * * *")
        return [
            {
                "id": "subscribeplus_scan",
                "name": "订阅下载增强扫描",
                "trigger": trigger,
                "func": self.run_scan,
                "kwargs": {"source": "schedule"},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {"path": "/status", "endpoint": self.get_status_api, "methods": ["GET"], "auth": "bear", "summary": "订阅下载增强状态"},
            {"path": "/categories", "endpoint": self.get_categories_api, "methods": ["GET"], "auth": "bear", "summary": "获取订阅二级分类"},
            {"path": "/sites", "endpoint": self.get_site_options_api, "methods": ["GET"], "auth": "bear", "summary": "获取可搜索 PT 站点"},
            {"path": "/scan", "endpoint": self.run_scan_api, "methods": ["POST"], "auth": "bear", "summary": "手动扫描订阅"},
            {"path": "/results", "endpoint": self.get_results_api, "methods": ["GET"], "auth": "bear", "summary": "获取最近诊断结果"},
            {"path": "/results/clear", "endpoint": self.clear_results_api, "methods": ["POST"], "auth": "bear", "summary": "清除最近诊断结果"},
            {"path": "/rule_preview", "endpoint": self.rule_preview_api, "methods": ["POST"], "auth": "bear", "summary": "生成规则修改预览"},
            {"path": "/rule_confirm", "endpoint": self.rule_confirm_api, "methods": ["POST"], "auth": "bear", "summary": "确认规则修改"},
        ]

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        return None, self._plugin_config.to_dict()

    def get_page(self) -> Optional[List[dict]]:
        return None

    def stop_service(self):
        pass

    def get_status_api(self) -> Dict[str, Any]:
        store = self._ensure_store()
        results = store.load_scan_results()
        counts: Dict[str, int] = {}
        for item in results:
            reason = item.get("reason") or "unknown"
            counts[reason] = counts.get(reason, 0) + 1
        return {
            "success": True,
            "data": {
                "enabled": self.get_state(),
                "config": self._plugin_config.to_dict(),
                "last_scan": store.load_scan_meta().get("last_scan_at"),
                "count": len(results),
                "counts": counts,
                "rule_records": store.load_rule_records()[:20],
            },
        }

    def get_categories_api(self) -> Dict[str, Any]:
        categories = self._ensure_scanner().collect_categories()
        return {
            "success": True,
            "data": {"items": [{"title": item, "value": item} for item in categories]},
        }

    def get_site_options_api(self) -> Dict[str, Any]:
        return {"success": True, "data": {"items": self._ensure_site_resolver().available_sites()}}

    def get_results_api(self) -> Dict[str, Any]:
        store = self._ensure_store()
        return {
            "success": True,
            "data": {
                "items": store.load_scan_results(),
                "last_scan": store.load_scan_meta().get("last_scan_at"),
                "rule_records": store.load_rule_records()[:50],
            },
        }

    def clear_results_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        self._ensure_store().clear_scan_results()
        return {"success": True}

    def run_scan_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        return self.run_scan(source="manual")

    def rule_preview_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        return self._rule_preview(payload, source="vue")

    def rule_confirm_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        token = payload.get("token") or payload.get("confirm_token")
        if not token:
            return {"success": False, "message": "缺少确认 token"}
        return self._rule_confirm(str(token))

    def run_scan(self, source: str = "manual") -> Dict[str, Any]:
        config = self._plugin_config
        store = self._ensure_store()
        scanner = self._ensure_scanner()
        diagnoser = self._ensure_diagnoser()
        resolver = self._ensure_site_resolver()

        results = []
        inputs = scanner.scan(config, resolver)
        for item in inputs[: config.max_scan_subscribes]:
            diagnosis = diagnoser.diagnose(item)
            results.append(diagnosis.to_dict())

        store.save_scan_results(results)
        if config.notify_tg:
            self._notify_each_show(results)
        return {"success": True, "count": len(results), "source": source}

    def _notify_each_show(self, results: List[Dict[str, Any]]):
        for item in results:
            ignore_key = self._ignore_key(item)
            if self._ensure_store().is_ignored(ignore_key):
                continue
            token = self._save_interaction(item)
            try:
                self.post_message(
                    mtype=NotificationType.Plugin if NotificationType else None,
                    title=f"订阅下载增强：{item.get('title')}",
                    text=render_notification_text(item),
                    buttons=build_main_menu(token, self._plugin_config.allow_tg_rule_update),
                    save_history=False,
                )
            except Exception as exc:
                logger.warning(f"订阅下载增强发送通知失败: {exc}")

    if eventmanager:
        @eventmanager.register(EventType.MessageAction)
        def handle_message_action(self, event):
            event_data = getattr(event, "event_data", None) or {}
            plugin_id = event_data.get("plugin_id")
            if plugin_id and plugin_id != PLUGIN_ID:
                return
            action = event_data.get("text") or event_data.get("action") or event_data.get("callback_data") or ""
            if not str(action).startswith(f"[PLUGIN]{PLUGIN_ID}|") and plugin_id != PLUGIN_ID:
                return
            self._handle_callback(str(action), event_data)

    def _handle_callback(self, action: str, event_data: Dict[str, Any]):
        command = action
        if action.startswith(f"[PLUGIN]{PLUGIN_ID}|"):
            command = action.split("|", 1)[1]
        op, _, token = command.partition(":")
        state = self._ensure_store().load_interaction(token)
        if not state:
            self.post_message(title="订阅下载增强", text="交互已过期，请重新扫描。", save_history=False)
            return

        diagnosis = state.get("diagnosis") or {}
        if op == "download":
            self.post_message(
                title=f"选择下载资源：{diagnosis.get('title')}",
                text="请选择一个候选资源下载。",
                buttons=build_resource_menu(token, diagnosis.get("candidates") or []),
                save_history=False,
            )
            return
        if op.startswith("pick"):
            index = int(op.replace("pick", "") or 0) - 1
            self._download_candidate(diagnosis, index)
            return
        if op == "rule":
            suggestions = build_rule_suggestions(
                diagnosis.get("candidates") or [],
                release_groups=self._release_groups_for_diagnosis(diagnosis),
            )
            self.post_message(
                title=f"调整订阅规则：{diagnosis.get('title')}",
                text="请选择要加入订阅包含规则的官组或平台关键词。",
                buttons=build_rule_menu(token, suggestions),
                save_history=False,
            )
            return
        if op == "rule-confirm":
            back_token = ((state.get("preview") or {}).get("back_token") or "").strip()
            result = self._rule_confirm(token)
            if result.get("success"):
                record = result.get("data") or {}
                text = "\n".join(
                    [
                        f"已添加：{record.get('selected_text') or '订阅包含规则'}",
                        "当前包含规则：",
                        record.get("new_value") or "-",
                    ]
                )
                self.post_message(
                    title="订阅下载增强",
                    text=text,
                    buttons=build_rule_done_menu(back_token) if back_token else None,
                    save_history=False,
                )
            else:
                self.post_message(title="订阅下载增强", text=result.get("message", "订阅规则修改失败。"), save_history=False)
            return
        if op.startswith("rule"):
            index = int(op.replace("rule", "") or 0) - 1
            suggestions = build_rule_suggestions(
                diagnosis.get("candidates") or [],
                release_groups=self._release_groups_for_diagnosis(diagnosis),
            )
            if 0 <= index < len(suggestions):
                selected_text = suggestions[index].get("text") or suggestions[index].get("value") or "规则"
                result = self._rule_preview(
                    {
                        "subscribe_id": diagnosis.get("subscribe_id"),
                        "pattern": suggestions[index].get("pattern"),
                        "back_token": token,
                        "selected_text": selected_text,
                    },
                    source="telegram",
                )
                if result.get("success"):
                    preview = result.get("data") or {}
                    self.post_message(
                        title=f"规则修改预览：{diagnosis.get('title')}",
                        text=render_rule_preview_text(preview, selected_text),
                        buttons=build_rule_confirm_menu(preview.get("token"), token),
                        save_history=False,
                    )
                else:
                    self.post_message(title="订阅下载增强", text=result.get("message", "生成预览失败。"), save_history=False)
            return
        if op == "ignore":
            self._ensure_store().save_ignore(self._ignore_key(diagnosis))
            self.post_message(title="订阅下载增强", text="已忽略本次提醒。", save_history=False)
            return
        if op == "close":
            self._ensure_store().delete_interaction(token)
            if not self._delete_callback_message(event_data):
                self.post_message(title="订阅下载增强", text="已关闭本次交互。", save_history=False)
            return
        if op == "back":
            self.post_message(
                title=f"订阅下载增强：{diagnosis.get('title')}",
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(token, self._plugin_config.allow_tg_rule_update),
                save_history=False,
            )

    def _rule_preview(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        subscribe_id = int(payload.get("subscribe_id") or 0)
        pattern = payload.get("pattern") or payload.get("include") or ""
        subscribe = self._get_subscribe(subscribe_id)
        if not subscribe:
            return {"success": False, "message": "订阅不存在"}
        try:
            preview = build_include_preview(subscribe, pattern, source=source)
        except ValueError as exc:
            return {"success": False, "message": str(exc)}
        token = make_token(preview)
        preview.update(
            {
                "token": token,
                "back_token": payload.get("back_token") or "",
                "selected_text": payload.get("selected_text") or "",
            }
        )
        self._ensure_store().save_interaction(
            token,
            {
                "view": "rule_preview",
                "preview": preview,
                "expires_at": (datetime.now() + timedelta(hours=2)).isoformat(timespec="seconds"),
            },
        )
        return {"success": True, "data": preview}

    def _rule_confirm(self, token: str) -> Dict[str, Any]:
        state = self._ensure_store().load_interaction(token)
        if not state or not state.get("preview"):
            return {"success": False, "message": "确认 token 无效或已过期"}
        try:
            record = apply_include_preview(state["preview"], self._update_subscribe)
        except ValueError as exc:
            return {"success": False, "message": str(exc)}
        record["selected_text"] = (state.get("preview") or {}).get("selected_text") or ""
        self._ensure_store().append_rule_record(record)
        self._ensure_store().delete_interaction(token)
        return {"success": True, "data": record}

    def _download_candidate(self, diagnosis: Dict[str, Any], index: int):
        candidates = diagnosis.get("candidates") or []
        if not (0 <= index < len(candidates)):
            self.post_message(title="订阅下载增强", text="候选资源不存在。", save_history=False)
            return
        candidate = candidates[index]
        candidate_id = candidate.get("download_payload") or candidate.get("candidate_id")
        context = self._download_contexts.get(str(candidate_id))
        if not context:
            self.post_message(title="订阅下载增强", text="下载上下文已过期，请重新扫描后再下载。", save_history=False)
            return
        try:
            from app.chain.download import DownloadChain

            DownloadChain().download_single(context=context, username=PLUGIN_ID)
            self.post_message(title="订阅下载增强", text="已提交下载任务。", save_history=False)
        except Exception as exc:
            self.post_message(title="订阅下载增强", text=f"提交下载失败：{exc}", save_history=False)

    def _delete_callback_message(self, event_data: Dict[str, Any]) -> bool:
        try:
            channel = event_data.get("channel")
            source = event_data.get("source")
            message_id = event_data.get("original_message_id") or event_data.get("message_id")
            chat_id = event_data.get("original_chat_id") or event_data.get("chat_id")
            if not message_id or not chat_id:
                return False
            chain = getattr(self, "chain", None)
            if not chain or not hasattr(chain, "delete_message"):
                return False
            chain.delete_message(channel, source, message_id, chat_id)
            return True
        except Exception as exc:
            logger.warning(f"订阅下载增强删除 Telegram 消息失败: {exc}")
            return False

    def _save_interaction(self, diagnosis: Dict[str, Any]) -> str:
        token = make_token(
            {
                "subscribe_id": diagnosis.get("subscribe_id"),
                "tmdbid": diagnosis.get("tmdbid"),
                "season": diagnosis.get("season"),
                "created_at": diagnosis.get("created_at"),
            }
        )
        self._ensure_store().save_interaction(
            token,
            {
                "view": "main",
                "diagnosis": diagnosis,
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds"),
            },
        )
        return token

    @staticmethod
    def _ignore_key(item: Dict[str, Any]) -> str:
        episodes = ",".join(str(episode.get("episode")) for episode in item.get("episodes") or [])
        return f"{item.get('subscribe_id')}:{item.get('season')}:{episodes}"

    def _load_subscribes(self) -> List[Any]:
        try:
            from app.db.subscribe_oper import SubscribeOper

            return SubscribeOper().list("R") or []
        except Exception as exc:
            logger.warning(f"订阅下载增强读取订阅失败: {exc}")
            return []

    def _get_subscribe(self, subscribe_id: int) -> Any:
        try:
            from app.db.subscribe_oper import SubscribeOper

            return SubscribeOper().get(subscribe_id)
        except Exception as exc:
            logger.warning(f"订阅下载增强读取订阅 {subscribe_id} 失败: {exc}")
            return None

    def _update_subscribe(self, subscribe_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        from app.db.subscribe_oper import SubscribeOper

        subscribe = SubscribeOper().update(subscribe_id, payload)
        return {"id": subscribe_id, "updated": bool(subscribe)}

    @staticmethod
    def _flatten_words(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]
        if isinstance(value, dict):
            words: List[str] = []
            for item in value.values():
                words.extend(SubscribePlus._flatten_words(item))
            return words
        if isinstance(value, (list, tuple, set)):
            words = []
            for item in value:
                words.extend(SubscribePlus._flatten_words(item))
            return words
        return [str(value)]

    def _load_custom_release_groups(self) -> List[str]:
        words: List[str] = []
        try:
            from app.db.systemconfig_oper import SystemConfigOper

            oper = SystemConfigOper()
            for key in (
                getattr(SystemConfigKey, "CustomIdentifiers", "CustomIdentifiers"),
                getattr(SystemConfigKey, "CustomReleaseGroups", "CustomReleaseGroups"),
                getattr(SystemConfigKey, "CustomWords", "CustomWords"),
                getattr(SystemConfigKey, "ReleaseGroups", "ReleaseGroups"),
            ):
                try:
                    words.extend(self._flatten_words(oper.get(key)))
                except Exception:
                    continue
        except Exception as exc:
            logger.warning(f"订阅下载增强读取自定义制作组词表失败: {exc}")
        return extract_release_groups_from_words(words)

    def _release_groups_for_diagnosis(self, diagnosis: Dict[str, Any]) -> List[str]:
        groups = list(self._load_custom_release_groups())
        subscribe_id = int(diagnosis.get("subscribe_id") or 0)
        if subscribe_id:
            subscribe = self._get_subscribe(subscribe_id)
            if subscribe:
                words: List[str] = []
                for attr in ("custom_words", "custom_identifiers", "release_groups"):
                    words.extend(self._flatten_words(getattr(subscribe, attr, None)))
                groups.extend(extract_release_groups_from_words(words))

        result: List[str] = []
        seen = set()
        for group in groups:
            key = str(group or "").lower()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(str(group))
        return result

    def _load_moviepilot_search_sites(self) -> List[Dict[str, Any]]:
        try:
            indexers = []
            try:
                from app.helper.sites import SitesHelper

                indexers = SitesHelper().get_indexers() or []
            except Exception:
                from app.db.site_oper import SiteOper

                indexers = [
                    {
                        "id": getattr(site, "id", None),
                        "name": getattr(site, "name", None),
                        "is_active": getattr(site, "is_active", True),
                    }
                    for site in (SiteOper().list_active() or [])
                ]
            return self._normalize_indexer_sites(indexers)
        except Exception as exc:
            logger.warning(f"订阅下载增强读取搜索站点失败: {exc}")
            return []

    @staticmethod
    def _normalize_indexer_sites(indexers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        sites = []
        for indexer in indexers or []:
            if indexer.get("is_active") is False:
                continue
            site_id = indexer.get("id", indexer.get("value"))
            if site_id in (None, ""):
                continue
            site_id = str(site_id)
            sites.append({"id": site_id, "name": str(indexer.get("name") or indexer.get("title") or site_id)})
        return sites

    def _load_tv_categories(self) -> List[str]:
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain

            raw_categories = (MediaChain().media_category() or {}).get(MediaType.TV.value) or []
            categories = []
            for item in raw_categories:
                if isinstance(item, dict):
                    value = item.get("title") or item.get("name") or item.get("value")
                else:
                    value = item
                if value:
                    categories.append(str(value).strip())
            return categories
        except Exception as exc:
            logger.warning(f"订阅下载增强读取二级分类策略失败: {exc}")
            return []

    def _resolve_subscribe_category(self, subscribe: Any) -> Optional[str]:
        tmdbid = int(getattr(subscribe, "tmdbid", 0) or 0)
        if not tmdbid:
            return None
        episode_group = getattr(subscribe, "episode_group", None) or ""
        cache_key = f"{tmdbid}:{episode_group}"
        if cache_key in self._category_cache:
            return self._category_cache[cache_key]
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain

            mediainfo = MediaChain().recognize_media(
                mtype=MediaType.TV,
                tmdbid=tmdbid,
                episode_group=episode_group or None,
            )
            category = str(getattr(mediainfo, "category", "") or "").strip()
            if category:
                self._category_cache[cache_key] = category
                return category
        except Exception as exc:
            logger.warning(f"订阅下载增强识别订阅分类失败 TMDB={tmdbid}: {exc}")
        return None

    def _load_tmdb_episodes(self, tmdbid: int, season: int, episode_group: Optional[str]) -> List[Dict[str, Any]]:
        cache_key = f"{tmdbid}:{season}:{episode_group or ''}"
        cached = self._ensure_store().load_tmdb_cache(cache_key)
        if cached and cached.get("episodes"):
            return cached["episodes"]
        try:
            from app.chain.tmdb import TmdbChain

            episodes = TmdbChain().tmdb_episodes(tmdbid=tmdbid, season=season, episode_group=episode_group) or []
            normalized = [
                {
                    "episode_number": getattr(episode, "episode_number", None) or getattr(episode, "episode", None),
                    "air_date": str(getattr(episode, "air_date", "") or ""),
                }
                for episode in episodes
            ]
            self._ensure_store().save_tmdb_cache(
                cache_key,
                {"episodes": normalized, "updated_at": datetime.now().isoformat(timespec="seconds")},
            )
            return normalized
        except Exception as exc:
            logger.warning(f"订阅下载增强读取 TMDB 剧集失败 TMDB={tmdbid} S{season}: {exc}")
            return []

    def _is_episode_downloaded(self, tmdbid: int, season: int, episode: int) -> tuple[bool, str]:
        try:
            from app.db.mediaserver_oper import MediaServerOper

            item = MediaServerOper().exists(tmdbid=tmdbid, mtype=MediaType.TV.value)
            seasoninfo = getattr(item, "seasoninfo", None) if item else None
            if episode_in_seasoninfo(seasoninfo, season, episode):
                return True, "媒体库缓存已命中"
        except Exception as exc:
            logger.warning(f"订阅下载增强查询媒体库缓存失败: {exc}")

        try:
            from app.db.transferhistory_oper import TransferHistoryOper

            histories = TransferHistoryOper().get_by(tmdbid=tmdbid, mtype=MediaType.TV.value, season=f"S{season}") or []
            history_dicts = [
                {
                    "tmdbid": getattr(history, "tmdbid", None),
                    "season": getattr(history, "seasons", None),
                    "episodes": getattr(history, "episodes", None),
                }
                for history in histories
            ]
            if episode_in_transfer_history(history_dicts, tmdbid, season, episode):
                return True, "整理历史已命中"
        except Exception as exc:
            logger.warning(f"订阅下载增强查询整理历史失败: {exc}")

        return False, "媒体库缓存和整理历史均未命中"

    def _search_torrents(self, item: DiagnosisInput) -> List[Dict[str, Any]]:
        try:
            from app.chain.search import SearchChain

            site_ids = [int(site_id) for site_id in item.sites if str(site_id).isdigit()]
            coro = SearchChain().async_search_by_id(
                tmdbid=item.tmdbid,
                mtype=MediaType.TV,
                area="title",
                season=item.season,
                sites=site_ids or None,
                cache_local=False,
            )
            try:
                contexts = asyncio.run(coro)
            except RuntimeError:
                loop = asyncio.get_event_loop()
                contexts = loop.run_until_complete(coro)

            results = []
            for context in contexts or []:
                torrent = getattr(context, "torrent_info", context)
                media_info = getattr(context, "media_info", None)
                meta_info = getattr(context, "meta_info", None)
                title = getattr(torrent, "title", None) or getattr(torrent, "name", None) or ""
                episodes = list(getattr(meta_info, "episode_list", None) or [])
                season_list = list(getattr(meta_info, "season_list", None) or [])
                candidate_id = self._remember_download_context(context, item, title)
                recognized = bool(
                    getattr(context, "candidate_recognized", False)
                    or (
                        media_info
                        and int(getattr(media_info, "tmdb_id", 0) or 0) == int(item.tmdbid)
                    )
                )
                results.append(
                    {
                        "candidate_id": candidate_id,
                        "site": str(getattr(torrent, "site", "") or ""),
                        "site_name": getattr(torrent, "site_name", None),
                        "title": title,
                        "recognized": recognized,
                        "season": season_list[0] if season_list else item.season,
                        "episode": episodes[0] if episodes else 0,
                        "episodes": episodes,
                        "seeders": getattr(torrent, "seeders", 0),
                        "size": getattr(torrent, "size", ""),
                        "free": bool(getattr(torrent, "downloadvolumefactor", None) == 0),
                        "download_payload": candidate_id,
                    }
                )
            return results
        except Exception as exc:
            logger.warning(f"订阅下载增强搜索 PT 资源失败: {exc}")
            return []

    def _remember_download_context(self, context: Any, item: DiagnosisInput, title: str) -> str:
        raw = f"{item.subscribe_id}:{item.tmdbid}:{item.season}:{title}:{len(self._download_contexts)}"
        candidate_id = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        self._download_contexts[candidate_id] = context
        if len(self._download_contexts) > 300:
            for old_key in list(self._download_contexts.keys())[:100]:
                self._download_contexts.pop(old_key, None)
        return candidate_id

    @staticmethod
    def _extract_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not payload:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}

    def _ensure_store(self) -> JsonStore:
        if not self._store:
            self._store = JsonStore(self.get_data_path(PLUGIN_ID))
        return self._store

    def _ensure_site_resolver(self) -> SiteResolver:
        if not self._site_resolver:
            self._site_resolver = SiteResolver(self._load_moviepilot_search_sites)
        return self._site_resolver

    def _ensure_scanner(self) -> SubscriptionScanner:
        if not self._scanner:
            self._scanner = SubscriptionScanner(
                self._load_subscribes,
                self._load_tmdb_episodes,
                self._is_episode_downloaded,
                load_categories=self._load_tv_categories,
                resolve_subscribe_category=self._resolve_subscribe_category,
            )
        return self._scanner

    def _ensure_diagnoser(self) -> TorrentDiagnoser:
        if not self._diagnoser:
            self._diagnoser = TorrentDiagnoser(self._search_torrents)
        return self._diagnoser
