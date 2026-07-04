from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import re
from dataclasses import replace
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
        PluginAction = "plugin.action"

    class MediaType:
        TV = type("TV", (), {"value": "电视剧"})()

    class SystemConfigKey:
        IndexerSites = "IndexerSites"
        CustomIdentifiers = "CustomIdentifiers"

from .diagnosis import TorrentDiagnoser
from .identifiers import (
    build_identifier_lines,
    build_identifier_record,
    dedupe_identifier_lines,
    normalize_identifier_line,
    normalize_media_type,
    refresh_identifier_runtime_cache,
    safe_int,
    validate_identifier_rule,
)
from .models import DiagnosisInput, PluginConfig, StaleEpisode
from .rules import (
    apply_rule_preview,
    build_rule_preview,
    build_rule_suggestions,
    extract_release_groups_from_words,
)
from .scanner import (
    SubscriptionScanner,
    episode_in_seasoninfo,
    episode_in_transfer_history,
    episodes_in_seasoninfo,
    episodes_in_transfer_history,
)
from .sites import SiteResolver
from .storage import JsonStore
from .telegram import (
    build_ci_done_menu,
    build_ci_manual_type_menu,
    build_ci_mode_menu,
    build_ci_wait_tmdb_menu,
    build_main_menu,
    build_resource_menu,
    build_rule_confirm_menu,
    build_rule_done_menu,
    build_rule_menu,
    make_token,
    render_identifier_fix_result_text,
    render_notification_text,
    render_rule_preview_text,
)


PLUGIN_ID = "SubscribePlus"


class SubscribePlus(_PluginBase):
    plugin_name = "订阅下载增强"
    plugin_desc = "检测已播出但未入库的电视剧订阅，并分析 PT 资源、识别和订阅规则原因。"
    plugin_icon = "tv.png"
    plugin_version = "0.5"
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
            load_downloaded_episodes=self._load_downloaded_episodes,
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
        return [
            {
                "cmd": "/ci",
                "event": EventType.PluginAction,
                "desc": "自定义识别词修正",
                "category": "订阅下载增强",
                "data": {"action": "subscribeplus_ci"},
            }
        ]

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
            {"path": "/identifier_auto", "endpoint": self.identifier_auto_api, "methods": ["POST"], "auth": "bear", "summary": "自动识别并写入自定义识别词"},
            {"path": "/identifier_manual", "endpoint": self.identifier_manual_api, "methods": ["POST"], "auth": "bear", "summary": "按 TMDB 手动写入自定义识别词"},
            {"path": "/identifier_fix", "endpoint": self.identifier_fix_api, "methods": ["POST"], "auth": "bear", "summary": "兼容旧版识别修正入口"},
            {"path": "/rule_suggestions", "endpoint": self.rule_suggestions_api, "methods": ["POST"], "auth": "bear", "summary": "生成订阅规则建议"},
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
                "identifier_records": store.load_identifier_records()[:20],
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
                "identifier_records": store.load_identifier_records()[:50],
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

    def identifier_fix_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        return self._identifier_fix(payload, source="vue")

    def identifier_auto_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        return self._identifier_auto(payload, source="vue")

    def identifier_manual_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        return self._identifier_manual(payload, source="vue")

    def rule_suggestions_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        diagnosis = payload.get("diagnosis") or {}
        candidate = payload.get("candidate")
        candidates = payload.get("candidates")
        if candidate and not candidates:
            candidates = [candidate]
        if not candidates:
            candidates = diagnosis.get("candidates") or []
        suggestions = build_rule_suggestions(
            candidates or [],
            release_groups=self._release_groups_for_diagnosis(diagnosis),
        )
        return {"success": True, "data": {"items": suggestions}}

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
        resolver = self._ensure_site_resolver()

        results = []
        inputs = scanner.scan(config, resolver)
        for item in inputs[: config.max_scan_subscribes]:
            diagnosis = self._diagnose_item(item)
            if not diagnosis:
                continue
            results.append(diagnosis.to_dict())

        store.save_scan_results(results)
        if config.notify_tg:
            self._notify_each_show(results)
        return {"success": True, "count": len(results), "source": source}

    def _diagnose_item(self, item: DiagnosisInput) -> Optional[DiagnosisItem]:
        mp_search = self._run_moviepilot_subscribe_search_for_item(item)
        mp_diagnosis = self._diagnose_with_moviepilot_subscription_scope(item, mp_search)
        if mp_diagnosis.candidates:
            if mp_diagnosis.reason == "downloadable":
                logger.info(
                    f"订阅下载增强：{item.title} 在 MP 订阅搜索范围内已有可匹配资源，交给 MP 订阅搜索处理"
                )
                return None
            return mp_diagnosis
        logger.info(f"订阅下载增强：{item.title} 在 MP 订阅搜索范围内没有候选资源，不再执行插件 PT 范围兜底搜索")
        return None

    def _run_moviepilot_subscribe_search_for_item(self, item: DiagnosisInput) -> Dict[str, Any]:
        captured: Dict[str, Any] = {"matched_contexts": [], "diagnostic_contexts": [], "errors": []}
        subscribe_id = safe_int(item.subscribe_id, 0)
        if not subscribe_id:
            return captured
        try:
            from app.chain.subscribe import SubscribeChain
            from app.chain.search import SearchChain

            original_parse_result = getattr(SearchChain, "_SearchChain__parse_result")

            def wrapped_parse_result(
                search_self,
                torrents,
                mediainfo,
                keyword=None,
                rule_groups=None,
                season_episodes=None,
                custom_words=None,
                filter_params=None,
            ):
                raw_torrents = list(torrents or [])
                try:
                    diagnostic_contexts = original_parse_result(
                        search_self,
                        list(raw_torrents),
                        copy.deepcopy(mediainfo),
                        keyword=keyword,
                        rule_groups=[],
                        season_episodes=season_episodes,
                        custom_words=custom_words,
                        filter_params=None,
                    )
                    captured["diagnostic_contexts"].extend(diagnostic_contexts or [])
                except Exception as exc:
                    captured["errors"].append(str(exc))
                    logger.warning(f"订阅下载增强分析 MP 订阅搜索原始结果失败：{item.title}，{exc}")

                matched_contexts = original_parse_result(
                    search_self,
                    torrents,
                    mediainfo,
                    keyword=keyword,
                    rule_groups=rule_groups,
                    season_episodes=season_episodes,
                    custom_words=custom_words,
                    filter_params=filter_params,
                )
                captured["matched_contexts"].extend(matched_contexts or [])
                return matched_contexts

            setattr(SearchChain, "_SearchChain__parse_result", wrapped_parse_result)
            try:
                SubscribeChain().search(sid=subscribe_id, state=None, manual=False)
            finally:
                setattr(SearchChain, "_SearchChain__parse_result", original_parse_result)
        except Exception as exc:
            captured["errors"].append(str(exc))
            logger.warning(f"订阅下载增强触发 MP 订阅搜索失败：{item.title} ID={subscribe_id}，{exc}")
        return captured

    def _diagnose_with_moviepilot_subscription_scope(self, item: DiagnosisInput, mp_search: Optional[Dict[str, Any]] = None) -> DiagnosisItem:
        mp_sites = self._load_moviepilot_subscribe_sites(item)
        scoped_item = replace(item, sites=mp_sites)
        mp_search = mp_search or {}

        matched_candidates = [
            self._context_to_candidate(context, scoped_item)
            for context in (mp_search.get("matched_contexts") or [])
        ]
        matched_diagnosis = TorrentDiagnoser(lambda _item: matched_candidates).diagnose(scoped_item)
        if matched_diagnosis.candidates:
            matched_diagnosis.reason = "downloadable"
            matched_diagnosis.message = "MP 订阅搜索结果中存在可匹配资源，已交给 MP 订阅搜索处理"
            return matched_diagnosis

        diagnostic_candidates = [
            self._context_to_candidate(context, scoped_item)
            for context in (mp_search.get("diagnostic_contexts") or [])
        ]
        diagnostic_item = replace(scoped_item, include="")
        diagnostic_result = TorrentDiagnoser(lambda _item: diagnostic_candidates).diagnose(diagnostic_item)
        if diagnostic_result.candidates:
            diagnostic_result.reason = "rule_blocked"
            diagnostic_result.message = "MP 订阅搜索结果中存在季集正确资源，但被订阅规则或过滤条件拦截"
            return diagnostic_result

        return DiagnosisItem(
            subscribe_id=scoped_item.subscribe_id,
            title=scoped_item.title,
            tmdbid=scoped_item.tmdbid,
            season=scoped_item.season,
            category=scoped_item.category,
            reason="no_pt_resource",
            message="MP 订阅搜索结果中没有覆盖目标集的候选资源",
            episodes=[episode.to_dict() for episode in scoped_item.episodes],
            sites=scoped_item.sites,
        )

    def _manual_pt_scope_diagnosis(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        subscribe_id = safe_int(diagnosis.get("subscribe_id"), 0)
        season = safe_int(diagnosis.get("season"), 0)
        tmdbid = safe_int(diagnosis.get("tmdbid"), 0)
        title = str(diagnosis.get("title") or "").strip()
        episodes = []
        for raw in diagnosis.get("episodes") or []:
            episode = safe_int(raw.get("episode"), 0) if isinstance(raw, dict) else 0
            if not episode:
                continue
            episodes.append(
                StaleEpisode(
                    season=safe_int(raw.get("season"), season) if isinstance(raw, dict) else season,
                    episode=episode,
                    air_date=str(raw.get("air_date") or "") if isinstance(raw, dict) else "",
                    evidence=str(raw.get("evidence") or "来自当前 Telegram 诊断记录") if isinstance(raw, dict) else "来自当前 Telegram 诊断记录",
                )
            )
        if not (subscribe_id and season and tmdbid and title and episodes):
            failed = dict(diagnosis)
            failed.update(
                {
                    "reason": "search_failed",
                    "message": "插件 PT 范围搜索失败：当前通知缺少订阅、TMDB、季或缺失集信息",
                    "candidates": [],
                }
            )
            return failed

        subscribe = self._get_subscribe(subscribe_id)
        include = str(getattr(subscribe, "include", "") or diagnosis.get("include") or "")
        category = str(diagnosis.get("category") or getattr(subscribe, "media_category", "") or "")
        sites = self._ensure_site_resolver().resolve_for_category(self._plugin_config, category)
        item = DiagnosisInput(
            subscribe_id=subscribe_id,
            title=title,
            tmdbid=tmdbid,
            season=season,
            category=category,
            include=include,
            sites=sites,
            episodes=episodes,
        )
        result = TorrentDiagnoser(self._search_torrents).diagnose(item).to_dict()
        result["source"] = "plugin_pt_scope"
        result["message"] = f"插件 PT 范围搜索结果：{result.get('message') or result.get('reason')}"
        return result

    def _notify_each_show(self, results: List[Dict[str, Any]]):
        store = self._ensure_store()
        pending = []
        for item in results:
            ignore_key = self._ignore_key(item)
            if store.is_ignored(ignore_key) or store.is_snoozed(ignore_key):
                continue
            pending.append(item)
        store.save_notification_queue(pending)
        self._notify_next_queued_show()

    def _notify_next_queued_show(self):
        store = self._ensure_store()
        while True:
            item = store.pop_notification_queue()
            if not item:
                return
            ignore_key = self._ignore_key(item)
            if store.is_ignored(ignore_key) or store.is_snoozed(ignore_key):
                continue
            token = self._save_interaction(item)
            try:
                self.post_message(
                    mtype=NotificationType.Plugin if NotificationType else None,
                    title=f"SubscribePlus: {item.get('title')}",
                    text=render_notification_text(item),
                    buttons=build_main_menu(
                        token,
                        self._plugin_config.allow_tg_rule_update,
                        can_identifier_fix=item.get("reason") == "recognition_issue",
                    ),
                    save_history=False,
                )
            except Exception as exc:
                logger.warning(f"璁㈤槄涓嬭浇澧炲己鍙戦€侀€氱煡澶辫触: {exc}")
            return

    if eventmanager:
        @eventmanager.register(EventType.MessageAction)
        def handle_message_action(self, event):
            event_data = getattr(event, "event_data", None) or {}
            plugin_id = event_data.get("plugin_id")
            if plugin_id and plugin_id != PLUGIN_ID:
                return
            action = event_data.get("text") or event_data.get("action") or event_data.get("callback_data") or ""
            if str(action).strip().startswith("/ci"):
                self._handle_ci_command_text(str(action), event_data)
                return
            if not str(action).startswith(f"[PLUGIN]{PLUGIN_ID}|") and plugin_id != PLUGIN_ID:
                return
            self._handle_callback(str(action), event_data)

        @eventmanager.register(EventType.PluginAction)
        def handle_plugin_action(self, event):
            event_data = getattr(event, "event_data", None) or {}
            action = event_data.get("action") or (event_data.get("data") or {}).get("action")
            if action != "subscribeplus_ci":
                return
            args = event_data.get("arg_str") or event_data.get("args") or event_data.get("text") or ""
            if isinstance(args, (list, tuple)):
                args = " ".join(str(item) for item in args)
            text = str(args or "").strip()
            self._handle_ci_command_text(f"/ci {text}".strip(), event_data)

    @staticmethod
    def _callback_post_kwargs(event_data: Dict[str, Any]) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        for source_key, target_key in (
            ("channel", "channel"),
            ("source", "source"),
            ("userid", "userid"),
            ("user", "userid"),
            ("original_message_id", "original_message_id"),
            ("original_chat_id", "original_chat_id"),
        ):
            value = event_data.get(source_key)
            if value is not None and target_key not in kwargs:
                kwargs[target_key] = value
        return kwargs

    def _post_callback_message(self, event_data: Dict[str, Any], **kwargs):
        kwargs.update(self._callback_post_kwargs(event_data))
        self.post_message(**kwargs)

    def _handle_callback(self, action: str, event_data: Dict[str, Any]):
        command = action
        if action.startswith(f"[PLUGIN]{PLUGIN_ID}|"):
            command = action.split("|", 1)[1]
        op, _, token = command.partition(":")
        logger.info(f"订阅下载增强处理 Telegram 回调：{op}:{token}")
        if op == "close":
            self._ensure_store().delete_interaction(token)
            self._notify_next_queued_show()
            if not self._delete_callback_message(event_data):
                self._post_callback_message(event_data, title="订阅下载增强", text="已关闭本次交互。", save_history=False)
            return
        state = self._ensure_store().load_interaction(token)
        if not state:
            self._post_callback_message(event_data, title="订阅下载增强", text="交互已过期，请重新扫描。", save_history=False)
            return

        diagnosis = state.get("diagnosis") or {}
        if op == "snooze3d":
            until = (datetime.now() + timedelta(days=3)).isoformat(timespec="seconds")
            self._ensure_store().save_snooze(self._ignore_key(diagnosis), until)
            self._ensure_store().delete_interaction(token)
            self._post_callback_message(
                event_data,
                title=f"SubscribePlus: {diagnosis.get('title')}",
                text=f"Snoozed for 3 days until {until}",
                save_history=False,
            )
            self._notify_next_queued_show()
            return
        if op == "download":
            if diagnosis.get("source") == "plugin_pt_scope":
                candidates = diagnosis.get("candidates") or []
                if candidates:
                    self._post_callback_message(
                        event_data,
                        title=f"选择下载：{diagnosis.get('title')}",
                        text="请选择要下载的候选资源。",
                        buttons=build_resource_menu(token, candidates),
                        save_history=False,
                    )
                else:
                    self._post_callback_message(
                        event_data,
                        title=f"SubscribePlus: {diagnosis.get('title')}",
                        text="插件 PT 范围搜索没有可下载候选资源。",
                        buttons=build_main_menu(
                            token,
                            self._plugin_config.allow_tg_rule_update,
                            can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                        ),
                        save_history=False,
                    )
                return
            result = self._start_moviepilot_subscribe_search(diagnosis)
            self._ensure_store().delete_interaction(token)
            self._post_callback_message(
                event_data,
                title=f"SubscribePlus: {diagnosis.get('title')}",
                text=result.get("message") or ("Started MP subscribe search" if result.get("success") else "Failed to start MP subscribe search"),
                save_history=False,
            )
            self._notify_next_queued_show()
            return
        if op == "ptscope":
            diagnosis = self._manual_pt_scope_diagnosis(diagnosis)
            state["diagnosis"] = diagnosis
            state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
            self._ensure_store().save_interaction(token, state)
            self._post_callback_message(
                event_data,
                title=f"订阅下载增强：{diagnosis.get('title')}",
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(
                    token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                ),
                save_history=False,
            )
            return
        if op.startswith("pick"):
            index = int(op.replace("pick", "") or 0) - 1
            self._download_candidate(diagnosis, index, event_data)
            return
        if op == "ci-auto":
            result = self._identifier_auto({"title": state.get("title")}, source="telegram")
            self._update_ci_state_after_result(token, state, result)
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=render_identifier_fix_result_text(result),
                buttons=build_ci_done_menu(token),
                save_history=False,
            )
            return
        if op == "ci-manual":
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=f"媒体文件名：{state.get('title') or '-'}",
                buttons=build_ci_manual_type_menu(token),
                save_history=False,
            )
            return
        if op in {"ci-tv", "ci-movie"}:
            state["manual_media_type"] = "tv" if op == "ci-tv" else "movie"
            self._ensure_store().save_interaction(token, state)
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=f"已选择 {state['manual_media_type']}，请回复：/ci {token} TMDBID",
                buttons=build_ci_wait_tmdb_menu(token),
                save_history=False,
            )
            return
        if op == "ci-retry":
            result = self._retry_ci_recognition(state)
            self._post_callback_message(
                event_data,
                title="再次识别",
                text=render_identifier_fix_result_text(result),
                buttons=build_ci_done_menu(token),
                save_history=False,
            )
            return
        if op == "ci-back":
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=f"媒体文件名：{state.get('title') or '-'}",
                buttons=build_ci_mode_menu(token),
                save_history=False,
            )
            return
        if op == "rule":
            suggestions = build_rule_suggestions(
                diagnosis.get("candidates") or [],
                release_groups=self._release_groups_for_diagnosis(diagnosis),
            )
            self._post_callback_message(
                event_data,
                title=f"调整订阅规则：{diagnosis.get('title')}",
                text="请选择要添加的官组、平台关键词或 PT 站点。",
                buttons=build_rule_menu(token, suggestions),
                save_history=False,
            )
            return
        if op == "rule-confirm":
            back_token = ((state.get("preview") or {}).get("back_token") or "").strip()
            result = self._rule_confirm(token)
            if result.get("success"):
                record = result.get("data") or {}
                current_label = "当前订阅站点：" if record.get("field") == "sites" else "当前包含规则："
                default_target = "订阅站点" if record.get("field") == "sites" else "订阅包含规则"
                text = "\n".join(
                    [
                        f"已添加：{record.get('selected_text') or default_target}",
                        current_label,
                        record.get("new_value") or "-",
                    ]
                )
                self._post_callback_message(
                    event_data,
                    title="订阅下载增强",
                    text=text,
                    buttons=build_rule_done_menu(back_token) if back_token else None,
                    save_history=False,
                )
            else:
                self._post_callback_message(
                    event_data,
                    title="订阅下载增强",
                    text=result.get("message", "订阅规则修改失败。"),
                    save_history=False,
                )
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
                    self._post_callback_message(
                        event_data,
                        title=f"规则修改预览：{diagnosis.get('title')}",
                        text=render_rule_preview_text(preview, selected_text),
                        buttons=build_rule_confirm_menu(preview.get("token"), token),
                        save_history=False,
                    )
                else:
                    self._post_callback_message(
                        event_data,
                        title="订阅下载增强",
                        text=result.get("message", "生成预览失败。"),
                        save_history=False,
                    )
            return
        if op == "ignore":
            self._ensure_store().save_ignore(self._ignore_key(diagnosis))
            self._ensure_store().delete_interaction(token)
            self._post_callback_message(event_data, title="订阅下载增强", text="已忽略本次提醒。", save_history=False)
            self._notify_next_queued_show()
            return
        if op == "back":
            self._post_callback_message(
                event_data,
                title=f"订阅下载增强：{diagnosis.get('title')}",
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(
                    token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                ),
                save_history=False,
            )

    def _rule_preview(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        subscribe_id = int(payload.get("subscribe_id") or 0)
        pattern = payload.get("pattern") or payload.get("include") or ""
        subscribe = self._get_subscribe(subscribe_id)
        if not subscribe:
            return {"success": False, "message": "订阅不存在"}
        try:
            preview = build_rule_preview(subscribe, pattern, source=source)
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
            record = apply_rule_preview(state["preview"], self._update_subscribe)
        except ValueError as exc:
            return {"success": False, "message": str(exc)}
        record["selected_text"] = (state.get("preview") or {}).get("selected_text") or ""
        self._ensure_store().append_rule_record(record)
        self._ensure_store().delete_interaction(token)
        return {"success": True, "data": record}

    def _identifier_fix(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        if payload.get("mode") == "manual" or payload.get("tmdbid") or payload.get("tmdb_id"):
            return self._identifier_manual(payload, source)
        diagnosis = self._resolve_diagnosis_payload(payload)
        candidate = self._resolve_candidate_payload(payload, diagnosis) if diagnosis else {}
        title = str(payload.get("title") or payload.get("candidate_title") or candidate.get("title") or "").strip()
        return self._identifier_auto({"title": title}, source)

    def _identifier_auto(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        title = self._identifier_title_from_payload(payload)
        if not title:
            return self._record_identifier_tool_failure("", {}, "媒体文件名不能为空", "missing_title", source, "auto")
        try:
            target = self._identify_target_by_ai(title)
        except Exception as exc:
            return self._record_identifier_tool_failure(
                title,
                {},
                f"AI 未配置或调用失败：{exc}",
                "ai_unavailable",
                source,
                "auto",
            )
        if not isinstance(target, dict):
            return self._record_identifier_tool_failure(title, {}, "AI 返回格式无效", "invalid_ai_response", source, "auto")
        return self._apply_identifier_rule(title, target, source, mode="auto")

    def _identifier_manual(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        title = self._identifier_title_from_payload(payload)
        if not title:
            return self._record_identifier_tool_failure("", {}, "媒体文件名不能为空", "missing_title", source, "manual")
        media_type = normalize_media_type(payload.get("media_type") or payload.get("type"))
        tmdbid = safe_int(payload.get("tmdbid") or payload.get("tmdb_id"), 0)
        if media_type == "unknown" or not tmdbid:
            return self._record_identifier_tool_failure(
                title,
                {},
                "请填写 movie/tv 和 TMDB ID",
                "missing_target",
                source,
                "manual",
            )
        target = {
            "media_type": media_type,
            "tmdbid": tmdbid,
            "season": safe_int(payload.get("season"), 0),
            "episode": safe_int(payload.get("episode"), 0),
        }
        return self._apply_identifier_rule(title, target, source, mode="manual")

    @staticmethod
    def _identifier_title_from_payload(payload: Dict[str, Any]) -> str:
        return str(
            payload.get("title")
            or payload.get("media_title")
            or payload.get("filename")
            or payload.get("candidate_title")
            or ""
        ).strip()

    def _apply_identifier_rule(self, title: str, target: Dict[str, Any], source: str, mode: str) -> Dict[str, Any]:
        target = dict(target or {})
        target["media_type"] = normalize_media_type(target.get("media_type") or target.get("type"))
        target["tmdbid"] = safe_int(target.get("tmdbid") or target.get("tmdb_id"), 0)
        if target["media_type"] == "unknown" or not target["tmdbid"]:
            return self._record_identifier_tool_failure(title, target, "缺少 movie/tv 或 TMDB ID", "missing_target", source, mode)
        if target["media_type"] == "tv":
            season, episode = self._parse_season_episode_from_title(title)
            if not safe_int(target.get("season"), 0) and season:
                target["season"] = season
            if not safe_int(target.get("episode"), 0) and episode:
                target["episode"] = episode

        tmdb_summary = self._load_tmdb_target_summary(target)
        if tmdb_summary.get("success") is False:
            return self._record_identifier_tool_failure(
                title,
                target,
                tmdb_summary.get("message") or "TMDB 没有查到可用数据",
                "tmdb_unavailable",
                source,
                mode,
            )
        if tmdb_summary.get("name"):
            target["name"] = target.get("name") or tmdb_summary.get("name")
        if tmdb_summary.get("year"):
            target["year"] = target.get("year") or tmdb_summary.get("year")

        try:
            lines = build_identifier_lines(title, target)
        except ValueError as exc:
            return self._record_identifier_tool_failure(title, target, str(exc), "invalid_target", source, mode)
        rules = [line for line in lines if validate_identifier_rule(line)]
        if not rules:
            return self._record_identifier_tool_failure(title, target, "生成的识别词规则无效", "invalid_rule", source, mode)

        rule = rules[0]
        try:
            applied = self._append_custom_identifiers([rule])
        except Exception as exc:
            return self._record_identifier_tool_failure(title, target, f"写入自定义识别词失败：{exc}", "write_failed", source, mode)

        recheck = self._recognize_identifier_title(title, target)
        success = bool(recheck.get("success"))
        if success:
            message = "已识别并写入自定义识别词" if applied.get("added") else "识别词已存在，再次识别已命中"
            status = "success"
            reason = ""
        else:
            message = recheck.get("message") or "识别词已写入，但再次识别未命中目标 TMDB"
            status = "failed"
            reason = recheck.get("reason") or "recognize_failed"

        record = build_identifier_record(
            subscribe_id=0,
            title=str(target.get("name") or title),
            candidate_title=title,
            target=target,
            added=applied.get("added") or [],
            source=source,
            status=status,
            message=message,
        )
        record["mode"] = mode
        record["rule"] = rule
        record["total_count"] = applied.get("total_count")
        record["recheck"] = recheck
        if reason:
            record["reason"] = reason
        self._ensure_store().append_identifier_record(record)
        return {"success": success, "message": message, "reason": reason, "data": record}

    def _record_identifier_tool_failure(
        self,
        title: str,
        target: Dict[str, Any],
        message: str,
        reason: str,
        source: str,
        mode: str,
    ) -> Dict[str, Any]:
        record = build_identifier_record(
            subscribe_id=0,
            title=str((target or {}).get("name") or title or ""),
            candidate_title=title,
            target=target or {},
            added=[],
            source=source,
            status="failed",
            message=message,
        )
        record["mode"] = mode
        record["reason"] = reason
        self._ensure_store().append_identifier_record(record)
        return {"success": False, "message": message, "reason": reason, "data": record}

    @staticmethod
    def _parse_season_episode_from_title(title: str) -> Tuple[int, int]:
        text = str(title or "")
        match = re.search(r"(?i)\bS(\d{1,2})E(\d{1,4})\b", text)
        if match:
            return safe_int(match.group(1), 0), safe_int(match.group(2), 0)
        match = re.search(r"(?i)\bS(\d{1,2})\b", text)
        if match:
            return safe_int(match.group(1), 0), 0
        return 0, 0

    def _record_identifier_failure(
        self,
        diagnosis: Dict[str, Any],
        candidate: Dict[str, Any],
        target: Dict[str, Any],
        message: str,
        reason: str,
        source: str,
    ) -> Dict[str, Any]:
        record = build_identifier_record(
            subscribe_id=safe_int(diagnosis.get("subscribe_id"), 0),
            title=str(diagnosis.get("title") or target.get("name") or ""),
            candidate_title=str(candidate.get("title") or ""),
            target=target,
            added=[],
            source=source,
            status="failed",
            message=message,
        )
        record["reason"] = reason
        self._ensure_store().append_identifier_record(record)
        return {"success": False, "message": message, "reason": reason, "data": record}

    def _resolve_diagnosis_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        diagnosis = payload.get("diagnosis")
        if isinstance(diagnosis, dict):
            return diagnosis
        subscribe_id = safe_int(payload.get("subscribe_id"), 0)
        tmdbid = safe_int(payload.get("tmdbid"), 0)
        for item in self._ensure_store().load_scan_results():
            if subscribe_id and safe_int(item.get("subscribe_id"), 0) == subscribe_id:
                return item
            if tmdbid and safe_int(item.get("tmdbid"), 0) == tmdbid:
                return item
        return {}

    @staticmethod
    def _resolve_candidate_payload(payload: Dict[str, Any], diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        candidate = payload.get("candidate")
        if isinstance(candidate, dict):
            return candidate
        candidates = diagnosis.get("candidates") or []
        candidate_id = str(payload.get("candidate_id") or "").strip()
        if candidate_id:
            for item in candidates:
                if str(item.get("candidate_id") or item.get("download_payload") or "") == candidate_id:
                    return item
        index = safe_int(payload.get("candidate_index"), -1)
        if 0 <= index < len(candidates):
            return candidates[index]
        if payload.get("candidate_title") or payload.get("title"):
            return {"title": payload.get("candidate_title") or payload.get("title")}
        return {}

    @staticmethod
    def _build_identifier_target(
        payload: Dict[str, Any], diagnosis: Dict[str, Any], candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        episodes = diagnosis.get("episodes") or []
        first_episode = episodes[0] if episodes else {}
        media_type = normalize_media_type(payload.get("media_type") or payload.get("type") or "tv")
        return {
            "name": str(payload.get("desired_name") or diagnosis.get("title") or "").strip(),
            "year": str(payload.get("desired_year") or payload.get("year") or "").strip(),
            "media_type": media_type,
            "tmdbid": safe_int(payload.get("tmdbid") or payload.get("tmdb_id") or diagnosis.get("tmdbid"), 0),
            "season": safe_int(payload.get("season") or candidate.get("season") or diagnosis.get("season"), 0),
            "episode": safe_int(payload.get("episode") or candidate.get("episode") or first_episode.get("episode"), 0),
        }

    def _load_tmdb_target_summary(self, target: Dict[str, Any]) -> Dict[str, Any]:
        tmdbid = safe_int(target.get("tmdbid"), 0)
        media_type = normalize_media_type(target.get("media_type"))
        if not tmdbid or media_type == "unknown":
            return {"success": False, "message": "缺少 TMDB ID 或媒体类型"}
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain

            mtype = MediaType.TV
            if media_type == "movie" and hasattr(MediaType, "MOVIE"):
                mtype = MediaType.MOVIE
            mediainfo = MediaChain().recognize_media(mtype=mtype, tmdbid=tmdbid)
            if not mediainfo:
                return {"success": False, "message": "TMDB 没有查到可用数据"}
            return {
                "success": True,
                "name": str(getattr(mediainfo, "title", "") or getattr(mediainfo, "name", "") or "").strip(),
                "year": str(getattr(mediainfo, "year", "") or "").strip(),
            }
        except Exception as exc:
            logger.warning(f"订阅下载增强校验 TMDB 目标失败 TMDB={tmdbid}: {exc}")
            return {"success": False, "message": f"TMDB 校验失败：{exc}"}

    def _identify_target_by_ai(self, title: str) -> Dict[str, Any]:
        try:
            from app.helper.llm import LLMHelper
        except Exception:
            try:
                from app.agent.llm import LLMHelper
            except Exception as exc:
                raise RuntimeError("AI 未配置或 LLMHelper 不可用") from exc

        llm = LLMHelper.get_llm(streaming=False)
        if hasattr(llm, "__await__"):
            try:
                llm = asyncio.run(llm)
            except RuntimeError:
                loop = asyncio.get_event_loop()
                llm = loop.run_until_complete(llm)
        prompt = "\n".join(
            [
                "你是 MoviePilot 媒体识别助手。",
                "请根据媒体文件名判断目标媒体，并只输出 JSON。",
                "JSON 字段：media_type 只能是 tv 或 movie；tmdbid 必须是 TMDB 数字 ID；name/year/season/episode 可选。",
                "不要输出 markdown，不要解释。",
                f"媒体文件名：{title}",
            ]
        )
        response = llm.invoke(prompt)
        content = str(getattr(response, "content", response) or "").strip()
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            content = content[start : end + 1]
        try:
            data = json.loads(content)
        except Exception as exc:
            raise RuntimeError("AI 返回不是可解析 JSON") from exc
        return {
            "media_type": normalize_media_type(data.get("media_type") or data.get("type")),
            "tmdbid": safe_int(data.get("tmdbid") or data.get("tmdb_id"), 0),
            "name": str(data.get("name") or data.get("title") or "").strip(),
            "year": str(data.get("year") or "").strip(),
            "season": safe_int(data.get("season"), 0),
            "episode": safe_int(data.get("episode"), 0),
        }

    def _recognize_identifier_title(self, title: str, target: Dict[str, Any]) -> Dict[str, Any]:
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain
            from app.core.metainfo import MetaInfo

            meta = MetaInfo(title)
            mediainfo = MediaChain().recognize_media(meta=meta, cache=False)
            recognized_tmdbid = safe_int(
                getattr(mediainfo, "tmdb_id", None) or getattr(mediainfo, "tmdbid", None),
                0,
            ) if mediainfo else 0
            target_tmdbid = safe_int(target.get("tmdbid"), 0)
            matched = bool(recognized_tmdbid and recognized_tmdbid == target_tmdbid)
            return {
                "success": matched,
                "message": "再次识别成功" if matched else "再次识别未命中目标 TMDB",
                "recognized_title": getattr(mediainfo, "title", "") if mediainfo else "",
                "tmdbid": recognized_tmdbid,
            }
        except Exception as exc:
            return {"success": False, "message": f"再次识别失败：{exc}", "reason": "recognize_failed"}

    def _suggest_identifier_lines_by_ai(self, title: str, target: Dict[str, Any]) -> List[str]:
        try:
            from app.helper.llm import LLMHelper
        except Exception:
            try:
                from app.agent.llm import LLMHelper
            except Exception as exc:
                raise RuntimeError("AI 未配置或 LLMHelper 不可用") from exc

        llm = LLMHelper.get_llm(streaming=False)
        if hasattr(llm, "__await__"):
            try:
                llm = asyncio.run(llm)
            except RuntimeError:
                loop = asyncio.get_event_loop()
                llm = loop.run_until_complete(llm)
        prompt = "\n".join(
            [
                "你是 MoviePilot 自定义识别词规则助手。",
                "请根据原始标题和目标信息生成 1 组尽量窄作用域、可直接用于 CustomIdentifiers 的规则。",
                "只输出规则行，不要 markdown。",
                "支持格式：屏蔽词；被替换词 => 替换词；前定位词 <> 后定位词 >> EP±N；组合规则。",
                "运算符两侧必须保留空格： => 、 <> 、 >> 、 && 。",
                "可使用强制 TMDB：{[tmdbid=xxx;type=tv/movie;s=1;e=1]}。",
                f"原始标题：{title}",
                f"目标：{target}",
            ]
        )
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        lines = []
        for raw in str(content or "").replace("```text", "```").splitlines():
            line = raw.strip().strip("`")
            if not line or line.lower().startswith(("```", "规则", "说明")):
                continue
            normalized = normalize_identifier_line(line)
            if normalized:
                lines.append(normalized)
        return lines

    def _append_custom_identifiers(self, lines: List[str]) -> Dict[str, Any]:
        from app.db.systemconfig_oper import SystemConfigOper

        oper = SystemConfigOper()
        key = getattr(SystemConfigKey, "CustomIdentifiers", "CustomIdentifiers")
        existing = oper.get(key) or []
        existing = self._flatten_words(existing)
        cleaned = []
        for line in lines:
            normalized = str(line or "").rstrip()
            if validate_identifier_rule(normalized):
                cleaned.append(normalized)
        added = dedupe_identifier_lines(existing, cleaned)
        if added:
            oper.set(key, added + existing)
            try:
                refresh_identifier_runtime_cache()
            except Exception as exc:
                logger.warning(f"订阅下载增强刷新识别词缓存失败: {exc}")
        return {"added": added, "total_count": len(existing) + len(added)}

    def _retry_identifier_recognition(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        candidates = diagnosis.get("candidates") or []
        candidate = candidates[0] if candidates else {}
        title = str(candidate.get("title") or diagnosis.get("title") or "").strip()
        if not title:
            return {"success": False, "message": "没有可再次识别的标题", "reason": "missing_title"}
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain
            from app.core.metainfo import MetaInfo

            meta = MetaInfo(title)
            mediainfo = MediaChain().recognize_media(meta=meta, cache=False)
            matched = bool(mediainfo and safe_int(getattr(mediainfo, "tmdb_id", 0), 0) == safe_int(diagnosis.get("tmdbid"), 0))
            return {
                "success": matched,
                "message": "再次识别成功" if matched else "再次识别仍未命中目标 TMDB",
                "data": {"added": [], "recognized_title": getattr(mediainfo, "title", "") if mediainfo else ""},
            }
        except Exception as exc:
            return {"success": False, "message": f"再次识别失败：{exc}", "reason": "recognize_failed"}

    def _start_moviepilot_subscribe_search(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        subscribe_id = safe_int(diagnosis.get("subscribe_id"), 0)
        if not subscribe_id:
            return {"success": False, "message": "缺少订阅 ID，无法触发 MP 原生订阅搜索"}
        try:
            from app.scheduler import Scheduler

            Scheduler().start(
                job_id="subscribe_search",
                sid=subscribe_id,
                state=None,
                manual=True,
            )
            return {
                "success": True,
                "message": f"已触发 MP 原生订阅搜索：{diagnosis.get('title') or subscribe_id}",
            }
        except Exception as exc:
            log_exception = getattr(logger, "exception", None)
            if callable(log_exception):
                log_exception("订阅下载增强触发 MP 原生订阅搜索失败")
            else:
                logger.warning(f"订阅下载增强触发 MP 原生订阅搜索失败: {exc}")
            return {"success": False, "message": f"触发 MP 原生订阅搜索失败：{exc}"}

    def _download_candidate(self, diagnosis: Dict[str, Any], index: int, event_data: Optional[Dict[str, Any]] = None):
        event_data = event_data or {}
        candidates = diagnosis.get("candidates") or []
        if not (0 <= index < len(candidates)):
            self._post_callback_message(event_data, title="订阅下载增强", text="候选资源不存在。", save_history=False)
            return
        candidate = candidates[index]
        candidate_id = candidate.get("download_payload") or candidate.get("candidate_id")
        context = self._download_contexts.get(str(candidate_id))
        if not context:
            result = self._start_moviepilot_subscribe_search(diagnosis)
            text = result.get("message") or "已触发 MP 原生订阅搜索"
            if result.get("success"):
                text = f"候选下载上下文已失效，{text}"
            else:
                text = f"候选下载上下文已失效，且{text}"
            self._post_callback_message(event_data, title="订阅下载增强", text=text, save_history=False)
            return
        try:
            from app.chain.download import DownloadChain

            DownloadChain().download_single(context=context, username=PLUGIN_ID)
            self._post_callback_message(event_data, title="订阅下载增强", text="已提交下载任务。", save_history=False)
        except Exception as exc:
            log_exception = getattr(logger, "exception", None)
            if callable(log_exception):
                log_exception("订阅下载增强提交候选资源下载失败")
            else:
                logger.warning(f"订阅下载增强提交候选资源下载失败: {exc}")
            self._post_callback_message(event_data, title="订阅下载增强", text=f"提交下载失败：{exc}", save_history=False)

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

    def _handle_ci_command_text(self, text: str, event_data: Dict[str, Any]):
        raw = str(text or "").strip()
        arg = raw[3:].strip() if raw.startswith("/ci") else raw
        if not arg:
            self._post_callback_message(event_data, title="自定义识别词", text="请发送：/ci 媒体文件名", save_history=False)
            return

        parts = arg.split()
        if parts:
            state = self._ensure_store().load_interaction(parts[0])
            if state and state.get("view") == "ci_tool":
                tmdbid = safe_int(parts[1] if len(parts) > 1 else None, 0)
                if not tmdbid:
                    self._post_callback_message(
                        event_data,
                        title="自定义识别词",
                        text=f"请回复：/ci {parts[0]} TMDBID",
                        save_history=False,
                    )
                    return
                result = self._identifier_manual(
                    {
                        "title": state.get("title"),
                        "media_type": state.get("manual_media_type") or "tv",
                        "tmdbid": tmdbid,
                    },
                    source="telegram",
                )
                self._update_ci_state_after_result(parts[0], state, result)
                self._post_callback_message(
                    event_data,
                    title="自定义识别词",
                    text=render_identifier_fix_result_text(result),
                    buttons=build_ci_done_menu(parts[0]),
                    save_history=False,
                )
                return

        if len(parts) >= 3 and parts[0].lower() in {"tv", "movie"} and safe_int(parts[1], 0):
            title = " ".join(parts[2:]).strip()
            token = self._save_ci_interaction(title)
            result = self._identifier_manual(
                {"title": title, "media_type": parts[0], "tmdbid": safe_int(parts[1], 0)},
                source="telegram",
            )
            state = self._ensure_store().load_interaction(token) or {"view": "ci_tool", "title": title}
            self._update_ci_state_after_result(token, state, result)
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=render_identifier_fix_result_text(result),
                buttons=build_ci_done_menu(token),
                save_history=False,
            )
            return

        token = self._save_ci_interaction(arg)
        self._post_callback_message(
            event_data,
            title="自定义识别词",
            text=f"媒体文件名：{arg}",
            buttons=build_ci_mode_menu(token),
            save_history=False,
        )

    def _save_ci_interaction(self, title: str) -> str:
        token = make_token({"ci": title, "created_at": datetime.now().isoformat(timespec="seconds")})
        self._ensure_store().save_interaction(
            token,
            {
                "view": "ci_tool",
                "title": str(title or "").strip(),
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds"),
            },
        )
        return token

    def _update_ci_state_after_result(self, token: str, state: Dict[str, Any], result: Dict[str, Any]):
        data = result.get("data") or {}
        if data.get("candidate_title"):
            state["title"] = data.get("candidate_title")
        if data.get("tmdbid"):
            state["last_target"] = {
                "tmdbid": data.get("tmdbid"),
                "media_type": data.get("media_type"),
                "season": data.get("season"),
                "episode": data.get("episode"),
                "name": data.get("title"),
            }
        self._ensure_store().save_interaction(token, state)

    def _retry_ci_recognition(self, state: Dict[str, Any]) -> Dict[str, Any]:
        title = str(state.get("title") or "").strip()
        target = state.get("last_target") or {}
        if not title or not target.get("tmdbid"):
            return {"success": False, "message": "没有可再次识别的记录", "reason": "missing_target", "data": {"added": []}}
        recheck = self._recognize_identifier_title(title, target)
        return {
            "success": bool(recheck.get("success")),
            "message": recheck.get("message") or "再次识别完成",
            "reason": recheck.get("reason") or ("" if recheck.get("success") else "recognize_failed"),
            "data": {"added": [], "recheck": recheck},
        }

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

            return SubscribeOper().list() or []
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

    @staticmethod
    def _describe_subscribe(subscribe: Any) -> str:
        title = str(getattr(subscribe, "name", "") or getattr(subscribe, "title", "") or "未知订阅").strip()
        subscribe_id = getattr(subscribe, "id", None)
        tmdbid = getattr(subscribe, "tmdbid", None)
        parts = [title]
        if subscribe_id:
            parts.append(f"ID={subscribe_id}")
        if tmdbid:
            parts.append(f"TMDB={tmdbid}")
        return " ".join(parts)

    def _resolve_subscribe_category(self, subscribe: Any) -> Optional[str]:
        tmdbid = int(getattr(subscribe, "tmdbid", 0) or 0)
        if not tmdbid:
            return None
        subscribe_label = self._describe_subscribe(subscribe)
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
            logger.warning(f"订阅下载增强识别订阅分类未命中 {subscribe_label}")
        except Exception as exc:
            logger.warning(f"订阅下载增强识别订阅分类失败 {subscribe_label}: {exc}")
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

    def _load_downloaded_episodes(self, tmdbid: int, season: int) -> set[int]:
        episodes: set[int] = set()
        try:
            from app.db.mediaserver_oper import MediaServerOper

            item = MediaServerOper().exists(tmdbid=tmdbid, mtype=MediaType.TV.value)
            if item:
                episodes.update(episodes_in_seasoninfo(getattr(item, "seasoninfo", None), season))
        except Exception as exc:
            logger.warning(f"订阅下载增强读取媒体库已下载集失败: {exc}")

        try:
            from app.db.transferhistory_oper import TransferHistoryOper

            histories = TransferHistoryOper().get_by(tmdbid=tmdbid, mtype=MediaType.TV.value) or []
            history_dicts = [
                {
                    "tmdbid": getattr(history, "tmdbid", None),
                    "season": getattr(history, "seasons", None),
                    "episodes": getattr(history, "episodes", None),
                }
                for history in histories
            ]
            episodes.update(episodes_in_transfer_history(history_dicts, tmdbid, season))
        except Exception as exc:
            logger.warning(f"订阅下载增强读取整理历史已下载集失败: {exc}")

        return {episode for episode in episodes if episode > 0}

    def _load_moviepilot_subscribe_sites(self, item: DiagnosisInput) -> List[str]:
        try:
            from app.chain.subscribe import SubscribeChain
            from app.db.subscribe_oper import SubscribeOper

            subscribe = SubscribeOper().get(safe_int(item.subscribe_id, 0))
            if not subscribe:
                return []
            return [str(site) for site in (SubscribeChain.get_sub_sites(subscribe) or [])]
        except Exception as exc:
            logger.warning(f"订阅下载增强读取 MP 订阅搜索站点失败：{item.title}，{exc}")
            return []

    def _search_torrents(self, item: DiagnosisInput, sites: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        try:
            from app.chain.search import SearchChain

            search_sites = item.sites if sites is None else sites
            site_ids = [int(site_id) for site_id in search_sites if str(site_id).isdigit()]
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

    def _context_to_candidate(self, context: Any, item: DiagnosisInput) -> Dict[str, Any]:
        torrent = getattr(context, "torrent_info", context)
        media_info = getattr(context, "media_info", None)
        meta_info = getattr(context, "meta_info", None)
        title = getattr(torrent, "title", None) or getattr(torrent, "name", None) or ""
        episodes = list(getattr(meta_info, "episode_list", None) or [])
        season_list = list(getattr(meta_info, "season_list", None) or [])
        candidate_id = self._remember_download_context(context, item, title)
        tmdb_id = safe_int(getattr(media_info, "tmdb_id", None), 0) if media_info else 0
        recognized = bool(
            getattr(context, "candidate_recognized", False)
            or getattr(context, "media_info_is_target", False)
            or (tmdb_id and tmdb_id == int(item.tmdbid or 0))
        )
        download_factor = getattr(torrent, "downloadvolumefactor", None)
        volume_factor = getattr(torrent, "volume_factor", None)
        if not volume_factor and download_factor is not None:
            try:
                if float(download_factor) == 0:
                    volume_factor = "Free"
                elif float(download_factor) < 1:
                    volume_factor = f"{int(float(download_factor) * 100)}%"
            except (TypeError, ValueError):
                volume_factor = ""
        return {
            "candidate_id": candidate_id,
            "site": str(getattr(torrent, "site", "") or ""),
            "site_name": getattr(torrent, "site_name", None),
            "title": title,
            "recognized": recognized,
            "season": season_list[0] if season_list else item.season,
            "episode": episodes[0] if episodes else 0,
            "episodes": episodes,
            "seeders": getattr(torrent, "seeders", 0),
            "peers": getattr(torrent, "peers", 0),
            "grabs": getattr(torrent, "grabs", 0),
            "size": getattr(torrent, "size", ""),
            "description": getattr(torrent, "description", "") or "",
            "pubdate": getattr(torrent, "pubdate", "") or "",
            "date_elapsed": getattr(torrent, "date_elapsed", "") or "",
            "freedate": getattr(torrent, "freedate", "") or "",
            "freedate_diff": getattr(torrent, "freedate_diff", "") or "",
            "volume_factor": volume_factor or "",
            "uploadvolumefactor": getattr(torrent, "uploadvolumefactor", None),
            "downloadvolumefactor": download_factor,
            "labels": list(getattr(torrent, "labels", None) or []),
            "page_url": getattr(torrent, "page_url", "") or "",
            "enclosure": getattr(torrent, "enclosure", "") or "",
            "free": bool(download_factor == 0),
            "download_payload": candidate_id,
        }

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
                load_downloaded_episodes=self._load_downloaded_episodes,
            )
        return self._scanner

    def _ensure_diagnoser(self) -> TorrentDiagnoser:
        if not self._diagnoser:
            self._diagnoser = TorrentDiagnoser(self._search_torrents)
        return self._diagnoser
