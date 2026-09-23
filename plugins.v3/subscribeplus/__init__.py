from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import posixpath
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
    from app.sdk.events import eventmanager
    from app.sdk.logging import logger
    from app.plugins import _PluginBase
    from app.schemas.types import EventType, MediaType, MediaSource, NotificationType, SystemConfigKey
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
        TransferComplete = "transfer.complete"

    class MediaType:
        TV = type("TV", (), {"value": "电视剧"})()

    class SystemConfigKey:
        IndexerSites = "IndexerSites"
        CustomIdentifiers = "CustomIdentifiers"

from .diagnosis import TorrentDiagnoser, normalize_search_result
from .identifiers import (
    build_force_identifier_rule,
    build_force_identifier_block,
    build_identifier_lines,
    build_identifier_record,
    build_year_identifier_rule,
    build_year_identifier_block,
    identifier_anchor,
    dedupe_identifier_lines,
    dedupe_identifier_blocks,
    normalize_identifier_line,
    normalize_media_type,
    refresh_identifier_runtime_cache,
    safe_int,
    validate_identifier_rule,
)
from .models import (
    DEFAULT_MEDIA_SOURCE,
    DiagnosisInput,
    DiagnosisItem,
    PluginConfig,
    StaleEpisode,
    normalize_identity,
    subscribe_identity,
)
from .romaji import select_romaji_aliases, should_try_romaji_fallback
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

from .season_cleanup import (
    QB_CLEANUP_OFF,
    QB_CLEANUP_SOURCE,
    is_completed_by_air_date,
    is_season_pack_title,
    is_single_episode_title,
    normalize_qb_cleanup_mode,
    parse_episode_numbers,
)
from .sites import SiteResolver
from .storage import JsonStore
from .telegram import (
    build_ci_done_menu,
    build_ci_manual_type_menu,
    build_ci_mode_menu,
    build_ci_wait_tmdb_menu,
    build_keyword_confirm_menu,
    build_main_menu,
    build_other_sites_menu,
    build_pending_menu,
    build_resource_menu,
    build_rule_confirm_menu,
    build_rule_custom_menu,
    build_rule_dictionary_menu,
    build_rule_done_menu,
    build_rule_menu,
    build_scan_summary_menu,
    build_summary_back_menu,
    make_token,
    render_identifier_fix_result_text,
    render_notification_text,
    render_rule_preview_text,
    render_scan_summary_text,
)


PLUGIN_ID = "SubscribePlus"
TMDB_CACHE_TTL_HOURS = 6
TMDB_CACHE_RETENTION_DAYS = 90
TMDB_SOURCE_VALUES = {"themoviedb", "tmdb"}
# V3 解析入口名称；旧宿主仍使用私有名称。
PARSE_RESULT_ATTR = "_parse_result"
LEGACY_PARSE_RESULT_ATTR = "_SearchChain__parse_result"


class SubscribePlus(_PluginBase):
    plugin_name = "订阅下载增强"
    plugin_desc = "检测已播出但未入库的电视剧订阅，并分析 PT 资源、识别和订阅规则原因。（小k自用版）"
    plugin_icon = "https://raw.githubusercontent.com/shyblacktea/MoviePilot-Plugins/main/icons/subscribeplus.png"
    plugin_version = "1.1.7"
    plugin_author = "shyblacktea"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "subscribeplus_"
    plugin_order = 998
    auth_level = 1

    # 说明：这些成员在 init_plugin 中初始化实例属性；此处仅做类型注解，
    # 避免使用类级可变默认值（dict/list）导致多实例间状态共享的隐患。
    _config: Dict[str, Any]
    _plugin_config: PluginConfig
    _store: Optional[JsonStore]
    _site_resolver: Optional[SiteResolver]
    _scanner: Optional[SubscriptionScanner]
    _diagnoser: Optional[TorrentDiagnoser]
    _download_contexts: Dict[str, Any]
    _category_cache: Dict[str, str]
    _custom_release_groups_cache: List[str]

    def init_plugin(self, config: dict = None):
        self._config = config or {}
        self._plugin_config = PluginConfig.from_dict(self._config)
        self._store = JsonStore(self.get_data_path(PLUGIN_ID))
        try:
            self._store.prune_candidate_cache(self._plugin_config.candidate_cache_days)
        except Exception as exc:
            logger.warning(f"订阅下载增强清理候选缓存失败：{exc}")
        try:
            removed = self._store.prune_tmdb_cache(TMDB_CACHE_RETENTION_DAYS)
            if removed:
                logger.info(f"订阅下载增强清理 TMDB 日历缓存：删除 {removed} 条超过 {TMDB_CACHE_RETENTION_DAYS} 天的记录")
        except Exception as exc:
            logger.warning(f"订阅下载增强清理 TMDB 日历缓存失败：{exc}")
        self._site_resolver = SiteResolver(self._load_moviepilot_search_sites)
        self._scanner = SubscriptionScanner(
            load_subscribes=self._load_subscribes,
            load_episodes=self._load_episodes,
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
            },
            {
                "cmd": "/sp",
                "event": EventType.PluginAction,
                "desc": "订阅下载增强待处理列表",
                "category": "订阅下载增强",
                "data": {"action": "subscribeplus_pending"},
            },
            {
                "cmd": "/sprule",
                "event": EventType.PluginAction,
                "desc": "订阅下载增强自定义识别词增删",
                "category": "订阅下载增强",
                "data": {"action": "subscribeplus_rule_identifier"},
            },
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
        # 所有定时业务统一由主扫描入口串行执行，避免“1”和“2”各自扫描、
        # 重复提交整季包或并发处理同一个 qB/MV3 清理记录。
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
            {"path": "/config", "endpoint": self.get_config_api, "methods": ["GET"], "auth": "bear", "summary": "获取插件配置"},
            {"path": "/config", "endpoint": self.save_config_api, "methods": ["POST"], "auth": "bear", "summary": "保存插件配置"},
            {"path": "/categories", "endpoint": self.get_categories_api, "methods": ["GET"], "auth": "bear", "summary": "获取订阅二级分类"},
            {"path": "/sites", "endpoint": self.get_site_options_api, "methods": ["GET"], "auth": "bear", "summary": "获取可搜索 PT 站点"},
            {"path": "/scan", "endpoint": self.run_scan_api, "methods": ["POST"], "auth": "bear", "summary": "手动扫描订阅"},
            {"path": "/results", "endpoint": self.get_results_api, "methods": ["GET"], "auth": "bear", "summary": "获取最近诊断结果"},
            {"path": "/results/clear", "endpoint": self.clear_results_api, "methods": ["POST"], "auth": "bear", "summary": "清除最近诊断结果"},
            {"path": "/results/delete", "endpoint": self.delete_result_api, "methods": ["POST"], "auth": "bear", "summary": "删除单条诊断结果"},
            {"path": "/rule_records/clear", "endpoint": self.clear_rule_records_api, "methods": ["POST"], "auth": "bear", "summary": "清空规则修改记录"},
            {"path": "/rule_records/delete", "endpoint": self.delete_rule_record_api, "methods": ["POST"], "auth": "bear", "summary": "删除单条规则修改记录"},
            {"path": "/identifier_records/clear", "endpoint": self.clear_identifier_records_api, "methods": ["POST"], "auth": "bear", "summary": "清空识别词操作记录"},
            {"path": "/identifier_auto", "endpoint": self.identifier_auto_api, "methods": ["POST"], "auth": "bear", "summary": "自动识别并写入自定义识别词"},
            {"path": "/identifier_manual", "endpoint": self.identifier_manual_api, "methods": ["POST"], "auth": "bear", "summary": "按 TMDB 手动写入自定义识别词"},
            {"path": "/identifier_year", "endpoint": self.identifier_year_api, "methods": ["POST"], "auth": "bear", "summary": "按 TMDB 首播年份修正文件年份"},
            {"path": "/identifier_fix", "endpoint": self.identifier_fix_api, "methods": ["POST"], "auth": "bear", "summary": "兼容旧版识别修正入口"},
            {"path": "/identifiers", "endpoint": self.get_identifiers_api, "methods": ["GET"], "auth": "bear", "summary": "获取自定义识别词"},
            {"path": "/identifiers/add", "endpoint": self.add_identifier_api, "methods": ["POST"], "auth": "bear", "summary": "增加自定义识别词"},
            {"path": "/identifiers/delete", "endpoint": self.delete_identifier_api, "methods": ["POST"], "auth": "bear", "summary": "删除自定义识别词"},
            {"path": "/rule_suggestions", "endpoint": self.rule_suggestions_api, "methods": ["POST"], "auth": "bear", "summary": "生成订阅规则建议"},
            {"path": "/rule_preview", "endpoint": self.rule_preview_api, "methods": ["POST"], "auth": "bear", "summary": "生成规则修改预览"},
            {"path": "/rule_confirm", "endpoint": self.rule_confirm_api, "methods": ["POST"], "auth": "bear", "summary": "确认规则修改"},
            {"path": "/rule_dictionary", "endpoint": self.get_rule_dictionary_api, "methods": ["GET"], "auth": "bear", "summary": "获取自定义官组和平台"},
            {"path": "/rule_dictionary", "endpoint": self.save_rule_dictionary_api, "methods": ["POST"], "auth": "bear", "summary": "保存自定义官组和平台"},
            {"path": "/diagnose_one", "endpoint": self.diagnose_one_api, "methods": ["POST"], "auth": "bear", "summary": "manual single subscribe diagnosis"},
            {"path": "/notify_test", "endpoint": self.notify_test_api, "methods": ["POST"], "auth": "bear", "summary": "发送测试通知"},
            {"path": "/mv3_test", "endpoint": self.mv3_test_api, "methods": ["POST"], "auth": "bear", "summary": "只读测试 MV3 连通性"},
            {"path": "/season_pack/preview", "endpoint": self.season_pack_preview_api, "methods": ["POST"], "auth": "bear", "summary": "预览完播剧集整季包替换"},
        ]

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        return None, self._plugin_config.to_dict()

    def notify_test_api(self) -> Dict[str, Any]:
        """按当前默认通知目标发送一条测试 Telegram 消息。"""
        self._post_message_to_targets(
            self._default_notify_userids(),
            {"title": "SubscribePlus 测试通知", "text": "SubscribePlus Telegram 通知链路测试成功。"},
        )
        return {"success": True, "message": "测试通知已发送"}

    def mv3_test_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        """使用当前或页面临时填写的配置，只读测试 MV3 事件接口连通性。"""
        data = self._extract_payload(payload)
        mv3_url = str(data.get("mv3_url") or getattr(self._plugin_config, "mv3_url", "") or "").strip()
        mv3_token = str(
            data.get("mv3_api_token")
            or getattr(self._plugin_config, "mv3_api_token", "")
            or ""
        ).strip()
        base = self._mv3_base_url(mv3_url)
        if not base or not mv3_token:
            return {
                "success": False,
                "message": "请先填写 MV3 网站地址和 API Key",
                "data": {"configured": False, "read_only": True},
            }

        response = self._mv3_request(
            "GET",
            "monitor/events",
            params={"page": 1, "page_size": 1},
            base_url=base,
            token=mv3_token,
        )
        if response is None:
            return {
                "success": False,
                "message": "MV3 连通性测试失败，请检查地址、API Key 和网络",
                "data": {"configured": True, "read_only": True, "endpoint": f"{base}/monitor/events"},
            }
        return {
            "success": True,
            "message": "MV3 连通性测试成功（只读）",
            "data": {
                "configured": True,
                "read_only": True,
                "endpoint": f"{base}/monitor/events",
                "response_type": type(response).__name__,
            },
        }

    def get_page(self) -> Optional[List[dict]]:
        return None

    def stop_service(self):
        """插件停止/重载时清理内存态资源。

        定时任务由 MoviePilot 调度器统一注销；JsonStore 为即时落盘，无需 flush。
        这里主要清空插件持有的内存引用（下载上下文、分类/压制组缓存及各组件），
        避免重载后残留旧状态或对象引用无法回收。
        """
        try:
            if isinstance(getattr(self, "_download_contexts", None), dict):
                self._download_contexts.clear()
            if isinstance(getattr(self, "_category_cache", None), dict):
                self._category_cache.clear()
            if isinstance(getattr(self, "_custom_release_groups_cache", None), list):
                self._custom_release_groups_cache.clear()
        except Exception as exc:
            logger.warning(f"订阅下载增强停止服务清理缓存失败：{exc}")
        self._scanner = None
        self._diagnoser = None
        self._site_resolver = None

    def get_config_api(self) -> Dict[str, Any]:
        """
        获取当前插件配置（数据页入口复用配置 UI 时读取初始值）。

        :return: {success, data: 配置字典}
        """
        return {"success": True, "data": self._plugin_config.to_dict()}

    def season_pack_preview_api(self) -> Dict[str, Any]:
        """只读预览已完播订阅、整季包候选和可识别的旧 qB 单集任务。"""
        return {"success": True, "data": self.run_season_pack_replace(dry_run=True)}

    def save_config_api(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        保存插件配置（数据页入口复用配置 UI 时的保存通道）。

        与宿主配置页保存等效：持久化后重新初始化插件使新配置生效。

        :param payload: 完整配置字典
        :return: {success, message}
        """
        payload = payload or {}
        try:
            merged = {**self._plugin_config.to_dict(), **payload}
            normalized = PluginConfig.from_dict(merged).to_dict()
            self.update_config(normalized)
            self.init_plugin(normalized)
            return {"success": True, "message": "配置已保存"}
        except Exception as exc:
            logger.error(f"订阅下载增强保存配置失败：{exc}", exc_info=True)
            return {"success": False, "message": str(exc)}

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

    # ---------- 订阅通知投递兼容 ----------

    def _load_notification_channels(self) -> List[Dict[str, Any]]:
        """读取启用的消息通知渠道配置。

        :return: [{type, name, config}], type 形如 telegram/qqbot
        """
        try:
            from app.application.notification import get_notification_configs
        except Exception as exc:
            logger.warning(f"订阅下载增强读取通知渠道失败: {exc}")
            return []

    def _load_external_notify_config(self) -> Dict[str, Any]:
        """读取独立“我就想通知到群组！”插件保存的订阅通知映射。"""
        try:
            config = self.systemconfig.get("plugin.NotifyToGroupShy") or {}
            return config if isinstance(config, dict) else {}
        except Exception as exc:
            logger.warning(f"订阅下载增强读取独立通知目标配置失败: {exc}")
            return {}
        try:
            channels = []
            for conf in get_notification_configs(include_disabled=False):
                channels.append(
                    {
                        "type": str(getattr(conf, "type", "") or "").strip().lower(),
                        "name": str(getattr(conf, "name", "") or ""),
                        "config": dict(getattr(conf, "config", None) or {}),
                    }
                )
            return channels
        except Exception as exc:
            logger.warning(f"订阅下载增强解析通知渠道失败: {exc}")
            return []

    @staticmethod
    def _channel_kind(channel_type: str) -> str:
        """把渠道 type 归一化为 tg/qq 前缀。

        :param channel_type: 通知渠道类型，如 telegram/qqbot
        :return: tg 或 qq；无法识别返回原始类型
        """
        raw = str(channel_type or "").strip().lower()
        if raw in {"telegram", "tg"}:
            return "tg"
        if raw in {"qqbot", "qq"}:
            return "qq"
        return raw

    @staticmethod
    def _split_ids(value: Any) -> List[str]:
        """把逗号分隔的 ID 字符串拆成去空白、去重列表。"""
        result: List[str] = []
        for item in str(value or "").split(","):
            item = item.strip()
            if item and item not in result:
                result.append(item)
        return result

    @staticmethod
    def _normalize_target(target: str, default_prefix: str = "tg") -> str:
        """规范化通知目标值为带渠道前缀的格式。

        兼容旧版无前缀配置：旧版只支持 Telegram，裸 ID（含 QQ 已保存的
        group: 前缀）统一补成 default_prefix 前缀（默认 tg）。已带
        tg:/qq: 前缀的保持不变。

        :param target: 原始目标值（可能为空、裸 ID 或带前缀）
        :param default_prefix: 无前缀值按哪个渠道解析（默认 tg）
        :return: 带前缀目标值；空输入返回空串
        """
        raw = str(target or "").strip()
        if not raw:
            return ""
        if raw.startswith("tg:") or raw.startswith("qq:"):
            return raw
        # 兼容旧版 QQ 群保存值 group:{openid}：补 qq: 前缀而不是误判成 TG
        if raw.startswith("group:"):
            return f"qq:{raw}"
        # 兼容历史脏数据：形如「群组 -1003975240343」「管理员 123」「用户 456」的
        # 标题文本，提取末尾 ID 段；不影响其它形态。
        stripped = re.split(r"\s+", raw, maxsplit=1)
        if len(stripped) == 2 and re.fullmatch(r"-?\d+", stripped[1].strip()):
            raw = stripped[1].strip()
        prefix = str(default_prefix or "tg").strip().lower()
        if prefix not in ("tg", "qq"):
            prefix = "tg"
        return f"{prefix}:{raw}"

    @classmethod
    def _split_targets(cls, value: Any) -> List[str]:
        """把配置值拆成多个规范化的带渠道前缀目标（去空去重）。

        支持旧版单值、逗号/中文逗号分隔的多目标以及数组/元组输入，
        返回按原顺序去重后的目标列表；空输入返回空列表。

        :param value: 原始目标配置值（字符串或可迭代）
        :return: 规范化后的目标列表
        """
        if value is None:
            return []
        if isinstance(value, str):
            items = [item.strip() for item in re.split(r"[,，]", value) if item.strip()]
        elif isinstance(value, (list, tuple, set)):
            items = [str(item).strip() for item in value if str(item).strip()]
        else:
            items = []
        result: List[str] = []
        for item in items:
            normalized = cls._normalize_target(item)
            if normalized and normalized not in result:
                result.append(normalized)
        return result

    def get_results_api(self) -> Dict[str, Any]:
        store = self._ensure_store()
        return {
            "success": True,
            "data": {
                "items": self._prune_downloaded_scan_results(),
                "last_scan": store.load_scan_meta().get("last_scan_at"),
                "identifier_records": store.load_identifier_records()[:50],
                "rule_records": store.load_rule_records()[:50],
                "custom_identifiers": self._load_custom_identifiers(),
            },
        }

    def get_identifiers_api(self) -> Dict[str, Any]:
        """返回当前全局自定义识别词，供配置页和 Telegram 菜单同步展示。"""
        identifiers = self._load_custom_identifiers()
        return {
            "success": True,
            "data": {
                "count": len(identifiers),
                "identifiers": identifiers,
            },
        }

    def add_identifier_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        """增加一条或多条全局自定义识别词，并返回最新完整列表。"""
        data = self._extract_payload(payload)
        values = data.get("identifiers", data.get("identifier", ""))
        result = self._add_custom_identifier_values(values)
        return result

    def delete_identifier_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        """按规则文本删除全局自定义识别词，并返回最新完整列表。"""
        data = self._extract_payload(payload)
        values = data.get("identifiers", data.get("identifier", ""))
        result = self._delete_custom_identifier_values(values)
        return result

    def clear_results_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        self._ensure_store().clear_scan_results()
        return {"success": True}

    def delete_result_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        data = self._extract_payload(payload)
        result_id = str(data.get("result_id") or "").strip()
        if not result_id:
            return {"success": False, "message": "缺少 result_id"}
        ok = self._ensure_store().delete_scan_result(result_id)
        return {"success": ok, "message": "" if ok else "未找到对应诊断结果"}

    def clear_rule_records_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        self._ensure_store().clear_rule_records()
        return {"success": True}

    def clear_identifier_records_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        self._ensure_store().clear_identifier_records()
        return {"success": True}

    def delete_rule_record_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        data = self._extract_payload(payload)
        record_id = str(data.get("record_id") or "").strip()
        if not record_id:
            return {"success": False, "message": "缺少 record_id"}
        ok = self._ensure_store().delete_rule_record(record_id)
        return {"success": ok, "message": "" if ok else "未找到对应规则记录"}

    def run_scan_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        return self.run_scan(source="manual")

    def diagnose_one_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        notify_value = payload.get("notify", True)
        notify = str(notify_value).strip().lower() not in {"0", "false", "no", "off"}
        # 单条诊断也是用户主动点击的读取入口，和“刷新日历并扫描”一样强制更新日历。
        item, error = self._build_single_diagnosis_input(payload, force_refresh=True)
        if not item:
            return {"success": False, "count": 0, "message": error or "no diagnosable subscription item"}

        diagnosis = self._diagnose_item(item)
        results = [diagnosis.to_dict()] if diagnosis else []
        self._ensure_store().save_scan_results(results)
        if notify and self._plugin_config.notify_tg and results:
            self._notify_each_show(results)
        return {
            "success": True,
            "count": len(results),
            "source": "manual_one",
            "message": "diagnosis completed" if results else "moviepilot handled it or no notifiable candidate found",
            "data": results[0] if results else None,
        }

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

    def identifier_year_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        return self._identifier_year(payload, source="vue")

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
            platforms=self._custom_platforms_for_suggestions(),
        )
        return {"success": True, "data": {"items": suggestions}}

    def rule_confirm_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        payload = self._extract_payload(payload)
        token = payload.get("token") or payload.get("confirm_token")
        if not token:
            return {"success": False, "message": "缺少确认 token"}
        return self._rule_confirm(str(token))

    def get_rule_dictionary_api(self) -> Dict[str, Any]:
        """返回 SubscribePlus 自定义官组和平台词表。"""
        groups, platforms = self._load_rule_dictionary()
        return {
            "success": True,
            "data": {
                "release_groups": groups,
                "platforms": platforms,
            },
        }

    def save_rule_dictionary_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        """保存自定义官组和平台词表，并立即同步到 Telegram 规则建议。"""
        data = self._extract_payload(payload)
        groups = self._normalize_dictionary_values(data.get("release_groups"))
        platforms = self._normalize_dictionary_values(data.get("platforms"))
        try:
            self._save_rule_dictionary(groups, platforms)
            return {
                "success": True,
                "message": "自定义官组和平台已保存并同步",
                "data": {"release_groups": groups, "platforms": platforms},
            }
        except Exception as exc:
            logger.error(f"订阅下载增强保存自定义官组和平台失败: {exc}", exc_info=True)
            return {"success": False, "message": f"保存自定义官组和平台失败：{exc}"}

    @staticmethod
    def _normalize_dictionary_values(value: Any) -> List[str]:
        """把自定义官组或平台输入规范化为去重的关键词列表。"""
        if value is None:
            return []
        if isinstance(value, str):
            values = re.split(r"[,，\n]", value)
        elif isinstance(value, (list, tuple, set)):
            values = []
            for item in value:
                values.extend(re.split(r"[,，\n]", str(item or "")))
        else:
            values = [str(value)]
        result: List[str] = []
        seen = set()
        for item in values:
            text = re.sub(r"\s+", " ", str(item or "").strip())
            if not text or len(text) > 80:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(text)
        return result

    def _load_rule_dictionary(self) -> Tuple[List[str], List[str]]:
        """读取插件配置中的自定义官组和平台词表。"""
        config = getattr(self, "_plugin_config", PluginConfig.from_dict({}))
        return (
            self._normalize_dictionary_values(getattr(config, "custom_release_groups", [])),
            self._normalize_dictionary_values(getattr(config, "custom_platforms", [])),
        )

    def _save_rule_dictionary(self, release_groups: List[str], platforms: List[str]) -> None:
        """保存自定义官组和平台词表，并重建当前插件运行态。"""
        merged = self._plugin_config.to_dict()
        merged["custom_release_groups"] = list(release_groups)
        merged["custom_platforms"] = list(platforms)
        self.update_config(merged)
        self.init_plugin(merged)

    def _custom_platforms_for_suggestions(self) -> List[str]:
        """返回当前配置的自定义平台关键词。"""
        return self._load_rule_dictionary()[1]

    def run_scan(self, source: str = "manual") -> Dict[str, Any]:
        """执行唯一主扫描入口，并在定时扫描尾部串行维护整季包链路。"""
        config = self._plugin_config
        store = self._ensure_store()
        scanner = self._ensure_scanner()
        resolver = self._ensure_site_resolver()

        results = []
        # 手动扫描是用户明确要求刷新日历的入口；定时扫描使用固定缓存策略。
        force_calendar_refresh = source == "manual"
        inputs = scanner.scan(config, resolver, force_refresh=force_calendar_refresh)
        scan_stats = getattr(scanner, "last_scan_stats", {})
        logger.info(f"订阅下载增强扫描统计：{scan_stats}")
        logger.info(
            "订阅下载增强扫描结果："
            f"缺集订阅={len(inputs)}，本轮全部处理，"
            f"订阅={[item.title for item in inputs]}"
        )
        for item in inputs:
            diagnosis = self._diagnose_item(item)
            if not diagnosis:
                continue
            results.append(diagnosis.to_dict())

        store.save_scan_results(results)
        if config.notify_tg:
            self._notify_each_show(results)

        maintenance = None
        if source == "schedule" and config.season_pack_enabled:
            # 定时主扫描中串行执行“2”的维护逻辑；手动扫描只做诊断，
            # 避免打开页面或点击普通扫描时意外提交下载、删除任务或删除源文件。
            try:
                retry_result = self.poll_season_pack_watches()
                replace_result = self.run_season_pack_replace(dry_run=False)
                maintenance = {
                    "retry": retry_result,
                    "season_pack": replace_result,
                }
                logger.info(
                    "订阅下载增强主扫描整季包维护完成："
                    f"重试处理={retry_result.get('processed', 0)}，"
                    f"重试待处理={retry_result.get('pending', 0)}，"
                    f"整季包项数={len(replace_result.get('items') or [])}"
                )
            except Exception as exc:
                maintenance = {"success": False, "error": str(exc)}
                logger.warning(f"订阅下载增强主扫描整季包维护失败：{exc}")

        result = {"success": True, "count": len(results), "source": source}
        if maintenance is not None:
            result["maintenance"] = maintenance
        return result

    def run_season_pack_replace(self, dry_run: bool = False) -> Dict[str, Any]:
        """按最后一集播出日期搜索整季包，并可在下载成功后清理旧 qB 单集任务。"""
        if not dry_run and not self._plugin_config.season_pack_enabled:
            return {"dry_run": False, "enabled": False, "items": []}
        today = datetime.now().date()
        items = []
        for subscribe in self._load_subscribes() or []:
            if not self._is_tv_subscribe(subscribe):
                continue
            source, media_id = subscribe_identity(subscribe)
            season = safe_int(getattr(subscribe, "season", 0), 0)
            if not source or not media_id or not season:
                continue
            episodes = self._load_episodes(
                source,
                media_id,
                season,
                getattr(subscribe, "episode_group", None),
                force_refresh=False,
            )
            completed, final_episode, final_air_date = is_completed_by_air_date(
                episodes,
                today,
                self._plugin_config.delay_days,
            )
            if not completed:
                continue
            category = str(getattr(subscribe, "media_category", "") or "").strip()
            search_sites = self._ensure_site_resolver().resolve_for_category(self._plugin_config, category)
            item = DiagnosisInput(
                subscribe_id=safe_int(getattr(subscribe, "id", 0), 0),
                title=str(getattr(subscribe, "name", "") or getattr(subscribe, "title", "") or ""),
                tmdbid=safe_int(getattr(subscribe, "tmdbid", 0), 0),
                season=season,
                category=category,
                media_source=source,
                media_id=media_id,
                sites=search_sites,
                username=str(getattr(subscribe, "username", "") or ""),
            )
            old_tasks = self._find_qb_single_tasks(item, subscribe)
            if not old_tasks:
                continue
            pending_watch = next((
                watch
                for watch in self._ensure_store().load_season_pack_watches()
                if str(watch.get("media_source") or "") == source
                and str(watch.get("media_id") or "") == str(media_id)
                and safe_int(watch.get("season"), 0) == season
            ), None)
            if pending_watch:
                items.append({
                    "subscribe_id": item.subscribe_id,
                    "title": item.title,
                    "media_source": source,
                    "media_id": media_id,
                    "season": season,
                    "final_episode": final_episode,
                    "final_air_date": final_air_date,
                    "candidate": None,
                    "old_qb_tasks": old_tasks,
                    "action": "cleanup_pending",
                })
                continue
            candidates = self._search_torrents(item, sites=search_sites)
            pack = self._choose_season_pack_candidate(candidates, season, final_episode)
            result = {
                "subscribe_id": item.subscribe_id,
                "title": item.title,
                "media_source": source,
                "media_id": media_id,
                "season": season,
                "final_episode": final_episode,
                "final_air_date": final_air_date,
                "candidate": pack,
                "old_qb_tasks": old_tasks,
                "action": "preview",
            }
            if pack and not dry_run:
                try:
                    context = self._download_contexts.get(str(pack.get("download_payload")))
                    if context:
                        from app.chain.download import DownloadChain

                        DownloadChain().download_single(context=context, username=PLUGIN_ID)
                        result["action"] = "download_submitted"
                    else:
                        result["action"] = "candidate_context_missing"
                except Exception as exc:
                    result["action"] = "download_failed"
                    result["error"] = str(exc)
            items.append(result)
        return {"dry_run": dry_run, "enabled": self._plugin_config.season_pack_enabled, "items": items}

    @staticmethod
    def _is_tv_subscribe(subscribe: Any) -> bool:
        """判断订阅是否为电视剧。"""
        return str(getattr(subscribe, "type", "") or "").strip().lower() in {"电视剧", "tv", "episode"}

    @staticmethod
    def _choose_season_pack_candidate(candidates: List[Dict[str, Any]], season: int, final_episode: int) -> Optional[Dict[str, Any]]:
        """从搜索结果中选出识别正确且覆盖最终集的整季包。"""
        accepted = []
        for candidate in candidates or []:
            title = str(candidate.get("title") or "")
            if not candidate.get("recognized") or not is_season_pack_title(title, season):
                continue
            episodes = {safe_int(value, 0) for value in candidate.get("episodes") or []}
            title_season = SubscribePlus._title_season_number(title)
            if title_season and title_season != season:
                continue
            if not title_season and not episodes:
                continue
            if episodes and final_episode not in episodes:
                continue
            accepted.append(candidate)
        return max(
            accepted,
            key=lambda item: (bool(item.get("free")), safe_int(item.get("seeders"), 0), safe_int(item.get("grabs"), 0)),
            default=None,
        )

    @staticmethod
    def _path_key(value: Any) -> str:
        """将下载器路径规范化为可比较的键。"""
        text = str(value or "").strip().replace("\\", "/")
        if not text:
            return ""
        text = re.sub(r"/+", "/", text).rstrip("/")
        return text.casefold()

    @staticmethod
    def _media_title_key(value: Any) -> str:
        """移除季集、年份和发布信息，生成保守的剧名匹配键。"""
        text = str(value or "").strip()
        text = re.sub(r"\bS\d{1,2}(?:[\s._-]*E\d{1,4}(?:[\s._-]*E?\d{1,4})?)?.*$", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(?:19|20)\d{2}\b", " ", text)
        text = re.sub(r"\b(?:complete|全集|全季|整季|season\s*pack)\b", " ", text, flags=re.IGNORECASE)
        return re.sub(r"[^0-9A-Za-z\u3400-\u9fff]+", "", text).casefold()

    @staticmethod
    def _title_season_number(value: Any) -> int:
        """从种子标题中提取显式季号。"""
        match = re.search(r"\bS(\d{1,2})(?=[\s._-]*E|\b)", str(value or ""), re.IGNORECASE)
        return safe_int(match.group(1), 0) if match else 0

    @staticmethod
    def _torrent_completed(torrent: Any) -> bool:
        """判断 qB 任务是否已完整完成且不是缺文件状态。"""
        state = str(SubscribePlus._read_cleanup_value(torrent, "state") or "").strip().lower()
        try:
            progress = float(SubscribePlus._read_cleanup_value(torrent, "progress") or 0)
            amount_left = float(SubscribePlus._read_cleanup_value(torrent, "amount_left") or 0)
        except (TypeError, ValueError):
            return False
        return (
            progress >= 0.999999
            and amount_left <= 0
            and state not in {
                "allocating", "checkingdl", "checkingup", "downloading", "error",
                "forceddl", "missingfiles", "metadl", "moving", "queueddl",
                "stalleddl", "unknown",
            }
        )

    @staticmethod
    def _get_qb_client(downloader: str = ""):
        """按名称获取 qBittorrent 客户端；未指定名称时只取一个可用实例。"""
        from app.sdk.services import DownloaderHelper

        helper = DownloaderHelper()
        if downloader:
            service = helper.get_service(name=downloader, type_filter="qbittorrent")
            return (getattr(service, "instance", None) if service else None), downloader
        services = helper.get_services(type_filter="qbittorrent")
        for name, service in services.items():
            client = getattr(service, "instance", None)
            if client:
                return client, str(name)
        return None, ""

    def _find_qb_single_tasks_for_pack(
        self,
        title: str,
        season: int,
        total_episode: int,
        save_path: str,
        downloader: str = "",
        pack_hash: str = "",
    ) -> List[Dict[str, Any]]:
        """在一次 DownloadAdded 触发的 qB 查询中筛选旧单集任务。"""
        client, client_name = self._get_qb_client(downloader)
        if not client:
            return []
        tasks, error = client.get_torrents()
        if error:
            return []

        show_key = self._media_title_key(title)
        expected_path = self._path_key(save_path)
        pack_hash_key = str(pack_hash or "").strip().casefold()
        selected = []
        for task in tasks or []:
            task_hash = str(self._read_cleanup_value(task, "hash") or "").strip()
            task_title = str(self._read_cleanup_value(task, "name", "title") or "").strip()
            task_path = str(self._read_cleanup_value(task, "save_path") or "").strip()
            if not task_hash or task_hash.casefold() == pack_hash_key:
                continue
            if not self._torrent_completed(task):
                continue
            if not task_title or not is_single_episode_title(task_title):
                continue
            if self._title_season_number(task_title) != int(season or 0):
                continue
            task_show_key = self._media_title_key(task_title)
            if not show_key or task_show_key != show_key:
                continue
            task_path_key = self._path_key(task_path)
            if not expected_path or not task_path_key or task_path_key != expected_path:
                continue
            episodes = parse_episode_numbers(task_title)
            if len(episodes) != 1 or total_episode and any(episode > total_episode for episode in episodes):
                continue
            source_paths = []
            try:
                media_extensions = {
                    ".mp4", ".mkv", ".ts", ".iso", ".rmvb", ".avi", ".mov",
                    ".mpeg", ".mpg", ".wmv", ".3gp", ".asf", ".m4v", ".flv",
                    ".m2ts", ".strm", ".tp", ".f4v", ".webm",
                }
                try:
                    from app.sdk.config import settings

                    configured = getattr(settings, "RMT_MEDIAEXT", None) or []
                    media_extensions = {str(ext).lower() for ext in configured} or media_extensions
                except Exception:
                    pass
                for fileitem in client.get_files(task_hash) or []:
                    file_name = str(self._read_cleanup_value(fileitem, "name", "path") or "").strip()
                    file_name_key = file_name.replace("\\", "/")
                    file_episodes = parse_episode_numbers(file_name_key)
                    if (
                        not file_name
                        or Path(file_name_key).suffix.lower() not in media_extensions
                        or re.search(r"(?:^|[/._ -])sample(?:[/._ -]|$)", file_name_key, re.I)
                        or not file_episodes.intersection(episodes)
                    ):
                        continue
                    if file_name.startswith(("/", "\\")):
                        source_path = file_name_key
                    else:
                        source_path = posixpath.join(task_path.rstrip("/\\"), file_name_key)
                    source_paths.append(source_path)
            except Exception as exc:
                logger.warning(f"订阅下载增强读取旧 qB 源文件路径失败：{task_hash}，{exc}")
            selected.append({
                "hash": task_hash,
                "title": task_title,
                "save_path": task_path,
                "downloader": client_name,
                "episodes": sorted(episodes),
                "source_paths": list(dict.fromkeys(source_paths)),
            })
        return selected

    def _qb_save_path_for_hash(self, download_hash: str, downloader: str = "") -> str:
        """按新整季包 hash 读取 qB 保存目录，不读取 MP 下载历史。"""
        client, _ = self._get_qb_client(downloader)
        if not client or not download_hash:
            return ""
        try:
            tasks, error = client.get_torrents(ids=download_hash)
            if error or not tasks:
                return ""
            return str(self._read_cleanup_value(tasks[0], "save_path") or "").strip()
        except Exception as exc:
            logger.warning(f"订阅下载增强读取新整季包 qB 保存目录失败：{download_hash}，{exc}")
            return ""

    def _find_qb_single_tasks(self, item: DiagnosisInput, subscribe: Any) -> List[Dict[str, Any]]:
        """只读查找同保存目录下的旧 qB 单集任务，不包含源文件删除动作。"""
        try:
            return self._find_qb_single_tasks_for_pack(
                title=item.title,
                season=item.season,
                total_episode=0,
                save_path=str(getattr(subscribe, "save_path", "") or ""),
                downloader=str(getattr(subscribe, "downloader", "") or ""),
            )
        except Exception as exc:
            logger.warning(f"订阅下载增强读取旧 qB 单集任务失败：{item.title}，{exc}")
            return []


    def _build_single_diagnosis_input(
        self,
        payload: Dict[str, Any],
        force_refresh: bool = False,
    ) -> Tuple[Optional[DiagnosisInput], str]:
        subscribe_id = safe_int(payload.get("subscribe_id") or payload.get("sid") or payload.get("id"), 0)
        if not subscribe_id:
            return None, "missing subscribe_id"
        subscribe = self._get_subscribe(subscribe_id)
        if not subscribe:
            return None, f"subscription not found: {subscribe_id}"

        media_source, media_id = subscribe_identity(subscribe)
        tmdbid = safe_int(getattr(subscribe, "tmdbid", 0), 0) or (
            safe_int(media_id, 0) if media_source == DEFAULT_MEDIA_SOURCE else 0
        )
        season = safe_int(getattr(subscribe, "season", 0), 0)
        if not (media_id and season):
            return None, f"subscription misses media identity or season: {self._describe_subscribe(subscribe)}"

        title = str(getattr(subscribe, "name", "") or getattr(subscribe, "title", "") or "").strip()
        category = str(
            getattr(subscribe, "media_category", "")
            or getattr(subscribe, "category", "")
            or self._resolve_subscribe_category(subscribe)
            or ""
        ).strip()
        include = str(getattr(subscribe, "include", "") or "")
        episode_group = getattr(subscribe, "episode_group", None)
        sites = self._ensure_site_resolver().resolve_for_category(self._plugin_config, category)
        episode_number = safe_int(payload.get("episode") or payload.get("ep"), 0)

        if episode_number:
            downloaded, evidence = self._is_episode_downloaded(
                media_source, media_id, season, episode_number
            )
            if downloaded:
                return None, f"{title} S{season:02d}E{episode_number:02d} is already downloaded"
            air_date = ""
            for episode in self._load_episodes(
                media_source,
                media_id,
                season,
                episode_group,
                force_refresh=force_refresh,
            ):
                number = safe_int(episode.get("episode_number") or episode.get("episode"), 0)
                if number == episode_number:
                    air_date = str(episode.get("air_date") or "")
                    break
            return (
                DiagnosisInput(
                    subscribe_id=subscribe_id,
                    title=title,
                    tmdbid=tmdbid,
                    season=season,
                    category=category,
                    media_source=media_source,
                    media_id=media_id,
                    include=include,
                    sites=sites,
                    episodes=[
                        StaleEpisode(
                            season=season,
                            episode=episode_number,
                            air_date=air_date,
                            evidence=evidence or "manual single episode diagnosis",
                        )
                    ],
                    username=str(getattr(subscribe, "username", "") or ""),
                ),
                "",
            )

        single_config = PluginConfig.from_dict(self._plugin_config.to_dict())
        if category:
            single_config.selected_categories = [category]
        scanner = SubscriptionScanner(
            lambda: [subscribe],
            self._load_episodes,
            self._is_episode_downloaded,
            load_categories=self._load_tv_categories,
            resolve_subscribe_category=self._resolve_subscribe_category,
            load_downloaded_episodes=self._load_downloaded_episodes,
        )
        inputs = scanner.scan(
            single_config,
            self._ensure_site_resolver(),
            force_refresh=force_refresh,
        )
        if not inputs:
            return None, f"{title or subscribe_id} has no stale episode to diagnose"
        return inputs[0], ""

    def _diagnose_item(self, item: DiagnosisInput) -> Optional[DiagnosisItem]:
        result = self._diagnose_item_inner(item)
        if result is not None:
            self._fill_site_names(result)
        return result

    def _fill_site_names(self, result: DiagnosisItem) -> None:
        """将诊断结果里的站点 ID 解析为站点名称，供通知展示。"""
        try:
            resolver = self._ensure_site_resolver()
            if getattr(result, "sites", None) and not getattr(result, "site_names", None):
                result.site_names = resolver.names_for(result.sites)
        except Exception as exc:
            logger.warning(f"订阅下载增强解析搜索站点名称失败：{exc}")

    def _diagnose_item_inner(self, item: DiagnosisInput) -> Optional[DiagnosisItem]:
        mp_search = self._run_moviepilot_subscribe_search_for_item(item)
        mp_diagnosis = self._diagnose_with_moviepilot_subscription_scope(item, mp_search)
        if mp_diagnosis.candidates:
            if mp_diagnosis.reason == "downloadable":
                logger.info(
                    "订阅下载增强触发 MP 订阅搜索后发现可匹配资源，已交给 MP 下载处理："
                    f"{self._format_item_log_context(item)}"
                )
                return None
            return mp_diagnosis
        other_site_diagnosis = self._diagnose_other_sites_when_subscription_scope_missing(item, mp_search, mp_diagnosis)
        if other_site_diagnosis and other_site_diagnosis.candidates:
            return other_site_diagnosis
        logger.info(f"订阅下载增强：{item.title} 在 MP 订阅搜索范围内没有候选资源，不再执行插件 PT 范围兜底搜索")
        return None

    def _run_moviepilot_subscribe_search_for_item(self, item: DiagnosisInput) -> Dict[str, Any]:
        captured: Dict[str, Any] = {
            "matched_contexts": [],
            "diagnostic_contexts": [],
            "raw_torrents": [],
            "errors": [],
            "search_context": {},
            "romaji_keyword": "",
        }
        subscribe_id = safe_int(item.subscribe_id, 0)
        if not subscribe_id:
            return captured
        try:
            from app.chain.subscribe import SubscribeChain
            from app.chain.search import SearchChain
            from app.db.subscribe_oper import SubscribeOper

            parse_attr, original_parse_result = self._resolve_parse_result(SearchChain)
            if not original_parse_result:
                logger.warning(f"订阅下载增强无法挂载 MP 搜索结果解析钩子，跳过订阅搜索分析：{item.title}")
                return captured
            subscribe = SubscribeOper().get(subscribe_id)

            def wrapped_parse_result(
                search_self,
                torrents,
                mediainfo,
                keyword=None,
                rule_groups=None,
                season_episodes=None,
                custom_words=None,
                filter_params=None,
                include_candidates=False,
                diagnostics=None,
                candidate_filter=None,
            ):
                raw_torrents = list(torrents or [])
                captured["raw_torrents"].extend(raw_torrents)
                captured["search_context"] = {
                    "mediainfo": copy.deepcopy(mediainfo),
                    "season_episodes": copy.deepcopy(season_episodes),
                    "custom_words": copy.deepcopy(custom_words),
                    "filter_params": copy.deepcopy(filter_params),
                    "rule_groups": copy.deepcopy(rule_groups),
                }
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
                        include_candidates=include_candidates,
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
                    include_candidates=include_candidates,
                    diagnostics=diagnostics,
                    candidate_filter=candidate_filter,
                )
                captured["matched_contexts"].extend(matched_contexts or [])
                return matched_contexts

            setattr(SearchChain, parse_attr, wrapped_parse_result)
            try:
                SubscribeChain().search(sid=subscribe_id, state=None, manual=False)
                subscribe_keyword = str(getattr(subscribe, "keyword", "") or "").strip() if subscribe else ""
                if subscribe and should_try_romaji_fallback(subscribe_keyword, captured["matched_contexts"]):
                    self._append_romaji_fallback_results(
                        item=item,
                        captured=captured,
                        subscribe=subscribe,
                        search_chain=SearchChain(),
                        original_parse_result=original_parse_result,
                    )
            finally:
                setattr(SearchChain, parse_attr, original_parse_result)
        except Exception as exc:
            captured["errors"].append(str(exc))
            logger.warning(f"订阅下载增强触发 MP 订阅搜索失败：{item.title} ID={subscribe_id}，{exc}")
        return captured

    @staticmethod
    def _resolve_parse_result(search_chain_cls: Any) -> Tuple[str, Any]:
        """定位宿主搜索结果解析入口。

        V3 把解析实现从私有名称 `__parse_result` 改名为 `_parse_result`，
        旧名回退用于兼容仍保留私有名称的宿主。
        """
        for attr in (PARSE_RESULT_ATTR, LEGACY_PARSE_RESULT_ATTR):
            candidate = getattr(search_chain_cls, attr, None)
            if callable(candidate):
                return attr, candidate
        return "", None

    def _append_romaji_fallback_results(
        self,
        item: DiagnosisInput,
        captured: Dict[str, Any],
        subscribe: Any,
        search_chain: Any,
        original_parse_result: Any,
    ) -> None:
        search_context = captured.get("search_context") or {}
        mediainfo = search_context.get("mediainfo")
        if not mediainfo:
            return
        aliases = list(getattr(mediainfo, "names", None) or [])
        aliases.extend(
            value
            for value in (
                getattr(mediainfo, "original_title", None),
                getattr(mediainfo, "original_name", None),
            )
            if value
        )
        romaji_aliases = select_romaji_aliases(aliases)
        if not romaji_aliases:
            logger.info(f"订阅下载增强未找到可用罗马音别名：{self._format_item_log_context(item)}")
            return

        from app.chain.subscribe import SubscribeChain

        site_ids = [
            int(site)
            for site in (SubscribeChain.get_sub_sites(subscribe) or [])
            if str(site).isdigit()
        ]
        for alias in romaji_aliases:
            try:
                title_contexts = search_chain.search_by_title(
                    title=alias,
                    sites=site_ids or None,
                    cache_local=False,
                ) or []
                torrents = [getattr(context, "torrent_info", context) for context in title_contexts]
                if not torrents:
                    continue
                captured["raw_torrents"].extend(torrents)
                diagnostic_contexts = original_parse_result(
                    search_chain,
                    list(torrents),
                    copy.deepcopy(mediainfo),
                    keyword=alias,
                    rule_groups=[],
                    season_episodes=copy.deepcopy(search_context.get("season_episodes")),
                    custom_words=copy.deepcopy(search_context.get("custom_words")),
                    filter_params=None,
                ) or []
                matched_contexts = original_parse_result(
                    search_chain,
                    list(torrents),
                    copy.deepcopy(mediainfo),
                    keyword=alias,
                    rule_groups=copy.deepcopy(search_context.get("rule_groups")),
                    season_episodes=copy.deepcopy(search_context.get("season_episodes")),
                    custom_words=copy.deepcopy(search_context.get("custom_words")),
                    filter_params=copy.deepcopy(search_context.get("filter_params")),
                ) or []
                captured["diagnostic_contexts"].extend(diagnostic_contexts)
                captured["matched_contexts"].extend(matched_contexts)
                if diagnostic_contexts or matched_contexts:
                    captured["romaji_keyword"] = alias
                    logger.info(
                        "订阅下载增强罗马音补搜命中："
                        f"{self._format_item_log_context(item)}，关键词={alias}，"
                        f"匹配={len(matched_contexts)}，诊断={len(diagnostic_contexts)}"
                    )
                if matched_contexts:
                    break
            except Exception as exc:
                captured["errors"].append(f"{alias}: {exc}")
                logger.warning(f"订阅下载增强罗马音补搜失败：{item.title}，关键词={alias}，{exc}")

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
            if mp_search.get("romaji_keyword"):
                matched_diagnosis.reason = "romaji_keyword_found"
                matched_diagnosis.message = "自动使用 TMDB 罗马音别名补搜到符合订阅规则的资源"
                matched_diagnosis.source = "romaji_fallback"
                matched_diagnosis.search_keyword_suggestion = str(mp_search.get("romaji_keyword") or "")
                return matched_diagnosis
            matched_diagnosis.reason = "downloadable"
            matched_diagnosis.message = "MP 订阅搜索结果中存在可匹配资源，已交给 MP 订阅搜索处理"
            return matched_diagnosis

        # V3 的 __parse_result 会在返回前再次应用宿主过滤；诊断必须使用
        # 捕获的原始 torrent，否则“不匹配规则但集数正确”的资源会消失。
        diagnostic_candidates = [
            self._raw_torrent_to_search_result(raw, scoped_item)
            for raw in (mp_search.get("raw_torrents") or [])
        ]
        # 原始站点结果通常没有 media_info；集数通知不应因此丢失，
        # 只要标题能解析到目标集，就允许进入诊断候选。
        for candidate in diagnostic_candidates:
            if candidate.get("title") and not candidate.get("recognized"):
                candidate["recognized"] = True
        diagnostic_item = replace(scoped_item, include="")
        diagnostic_result = TorrentDiagnoser(lambda _item: diagnostic_candidates).diagnose(diagnostic_item)
        if diagnostic_result.candidates:
            diagnostic_result.reason = "rule_blocked"
            diagnostic_result.message = "MP 订阅搜索结果中存在季集正确资源，但被订阅规则或过滤条件拦截"
            if mp_search.get("romaji_keyword"):
                diagnostic_result.source = "romaji_fallback"
                diagnostic_result.search_keyword_suggestion = str(mp_search.get("romaji_keyword") or "")
                diagnostic_result.message = "自动使用 TMDB 罗马音别名补搜到季集正确资源，但仍被订阅规则或过滤条件拦截"
            return diagnostic_result

        return DiagnosisItem(
            subscribe_id=scoped_item.subscribe_id,
            title=scoped_item.title,
            tmdbid=scoped_item.tmdbid,
            season=scoped_item.season,
            category=scoped_item.category,
            media_source=scoped_item.media_source,
            media_id=scoped_item.media_id,
            reason="no_pt_resource",
            message="MP 订阅搜索结果中没有覆盖目标集的候选资源",
            episodes=[episode.to_dict() for episode in scoped_item.episodes],
            sites=scoped_item.sites,
            username=scoped_item.username,
        )

    @staticmethod
    def _episode_numbers_from_item(item: DiagnosisInput) -> List[int]:
        values: List[int] = []
        for episode in item.episodes or []:
            number = safe_int(getattr(episode, "episode", 0), 0)
            if number and number not in values:
                values.append(number)
        return values

    @staticmethod
    def _raw_torrent_to_search_result(raw: Any, item: DiagnosisInput) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        torrent = getattr(raw, "torrent_info", raw)
        meta_info = getattr(raw, "meta_info", None)
        media_info = getattr(raw, "media_info", None)
        episodes = list(getattr(meta_info, "episode_list", None) or [])
        season_list = list(getattr(meta_info, "season_list", None) or [])
        title = getattr(torrent, "title", None) or getattr(torrent, "name", None) or ""
        source, identity = SubscribePlus._item_identity(item)
        return {
            "site": str(getattr(torrent, "site", "") or ""),
            "site_name": getattr(torrent, "site_name", None),
            "title": title,
            "recognized": bool(
                getattr(raw, "candidate_recognized", False)
                or getattr(raw, "media_info_is_target", False)
                or SubscribePlus._context_matches_item(media_info, source, identity)
            ),
            "season": season_list[0] if season_list else item.season,
            "episode": episodes[0] if episodes else 0,
            "episodes": episodes,
            "seeders": getattr(torrent, "seeders", 0),
            "size": getattr(torrent, "size", ""),
        }

    def _build_subscription_site_progress(
        self, item: DiagnosisInput, mp_search: Dict[str, Any], subscription_sites: List[str]
    ) -> List[Dict[str, Any]]:
        target_episode = max(self._episode_numbers_from_item(item) or [0])
        if not target_episode:
            return []
        subscription_set = {str(site) for site in subscription_sites or []}
        latest_by_site: Dict[str, Dict[str, Any]] = {}
        for raw in mp_search.get("raw_torrents") or []:
            normalized = normalize_search_result(self._raw_torrent_to_search_result(raw, item))
            site = str(normalized.get("site") or "")
            if subscription_set and site not in subscription_set:
                continue
            if safe_int(normalized.get("season"), item.season) not in (0, safe_int(item.season, 0)):
                continue
            episodes = [
                safe_int(episode, 0)
                for episode in (normalized.get("episodes") or [])
                if safe_int(episode, 0)
            ]
            if not episodes and safe_int(normalized.get("episode"), 0):
                episodes = [safe_int(normalized.get("episode"), 0)]
            latest_episode = max(episodes or [0])
            if not latest_episode or latest_episode >= target_episode:
                continue
            current = latest_by_site.get(site)
            if current and safe_int(current.get("latest_episode"), 0) >= latest_episode:
                continue
            latest_by_site[site] = {
                "site": site,
                "site_name": normalized.get("site_name") or site or "订阅站点",
                "latest_episode": latest_episode,
                "target_episode": target_episode,
                "seeders": safe_int(normalized.get("seeders"), 0),
            }
        return sorted(
            latest_by_site.values(),
            key=lambda item: (safe_int(item.get("latest_episode"), 0), str(item.get("site_name") or "")),
            reverse=True,
        )

    def _diagnose_other_sites_when_subscription_scope_missing(
        self, item: DiagnosisInput, mp_search: Dict[str, Any], mp_diagnosis: DiagnosisItem
    ) -> Optional[DiagnosisItem]:
        subscription_sites = [str(site) for site in (mp_diagnosis.sites or self._load_moviepilot_subscribe_sites(item))]
        configured_sites = self._ensure_site_resolver().resolve_for_category(self._plugin_config, item.category)
        subscription_set = set(subscription_sites)
        other_sites = [str(site) for site in configured_sites if str(site) not in subscription_set]
        if not other_sites:
            return None

        scoped_item = replace(item, sites=other_sites)
        result = TorrentDiagnoser(self._search_torrents).diagnose(scoped_item)
        if not result.candidates:
            return None

        original_reason = result.reason
        if result.reason in {"downloadable", "rule_blocked"}:
            result.reason = "site_scope_blocked"
            result.message = "订阅站点暂无目标集，其他 PT 站点存在目标集资源"
            if original_reason == "rule_blocked":
                result.message += "，但可能仍被订阅包含规则拦截"
        elif result.reason == "recognition_issue":
            result.message = "订阅站点暂无目标集，其他 PT 站点存在目标集资源，但识别异常"

        result.source = "plugin_pt_scope"
        result.original_reason = original_reason
        result.sites = other_sites
        result.site_names = self._ensure_site_resolver().names_for(other_sites)
        result.subscription_sites = subscription_sites
        result.subscription_site_names = self._ensure_site_resolver().names_for(subscription_sites)
        result.subscription_site_progress = self._build_subscription_site_progress(item, mp_search, subscription_sites)
        logger.info(
            "订阅下载增强发现订阅站点缺集但其他站点存在目标集："
            f"{self._format_item_log_context(item)}，订阅站点={','.join(subscription_sites) or '-'}，"
            f"其他站点={','.join(other_sites)}，"
            f"目标集候选={len(result.candidates)}，搜索统计={result.search_stats}"
        )
        return result

    def _compute_other_sites(self, diagnosis: Dict[str, Any]) -> List[Dict[str, str]]:
        """计算"其他站点"（PT 搜索范围 - 订阅站点），返回 [{id, name}]。"""
        resolver = self._ensure_site_resolver()
        category = str(diagnosis.get("category") or "")
        configured = resolver.resolve_for_category(self._plugin_config, category)
        subscription_sites = set(str(s) for s in (diagnosis.get("subscription_sites") or []))
        name_map = resolver.name_map()
        others = []
        for site_id in configured:
            if str(site_id) in subscription_sites:
                continue
            others.append({"id": str(site_id), "name": name_map.get(str(site_id), str(site_id))})
        return others

    def _manual_pt_scope_diagnosis(
        self, diagnosis: Dict[str, Any], only_sites: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        subscribe_id = safe_int(diagnosis.get("subscribe_id"), 0)
        season = safe_int(diagnosis.get("season"), 0)
        tmdbid = safe_int(diagnosis.get("tmdbid"), 0)
        media_source, media_id = normalize_identity(
            diagnosis.get("media_source"), diagnosis.get("media_id")
        )
        if not media_id and tmdbid:
            # 旧诊断快照只有 tmdbid，按 TMDB 来源回放。
            media_source, media_id = DEFAULT_MEDIA_SOURCE, str(tmdbid)
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
        if not (subscribe_id and season and media_id and title and episodes):
            failed = dict(diagnosis)
            failed.update(
                {
                    "reason": "search_failed",
                    "message": "搜索其他站点失败：当前通知缺少订阅、媒体身份、季或缺失集信息",
                    "candidates": [],
                }
            )
            return failed

        subscribe = self._get_subscribe(subscribe_id)
        include = str(getattr(subscribe, "include", "") or diagnosis.get("include") or "")
        category = str(diagnosis.get("category") or getattr(subscribe, "media_category", "") or "")
        resolver = self._ensure_site_resolver()
        if only_sites:
            sites = [str(s) for s in only_sites]
        else:
            # 默认搜"其他站点"（PT 搜索范围 - 订阅站点），与自动诊断语义一致
            sites = [str(s.get("id")) for s in self._compute_other_sites(diagnosis)]
        item = DiagnosisInput(
            subscribe_id=subscribe_id,
            title=title,
            tmdbid=tmdbid,
            season=season,
            category=category,
            media_source=media_source,
            media_id=media_id,
            include=include,
            sites=sites,
            episodes=episodes,
            username=str(getattr(subscribe, "username", "") or ""),
        )
        result = TorrentDiagnoser(self._search_torrents).diagnose(item).to_dict()
        result["source"] = "plugin_pt_scope"
        result["sites"] = sites
        result["site_names"] = resolver.names_for(sites)
        site_label = "、".join(result["site_names"]) or "无其他站点"
        stamp = datetime.now().strftime("%H:%M")
        base = result.get("message") or result.get("reason") or ""
        result["message"] = f"搜索其他站点完成（{stamp}）：{site_label}，命中 {len(result.get('candidates') or [])} 个候选"
        return result

    def _notify_each_show(self, results: List[Dict[str, Any]]):
        store = self._ensure_store()
        pending = []
        for item in results:
            ignore_key = self._ignore_key(item)
            if store.is_notification_suppressed(ignore_key):
                continue
            pending.append(item)
        if not pending:
            return

        # 扫描结果不再按队列逐条弹出。按通知目标分组，保证不同订阅用户的
        # 映射仍然生效；同一目标只收到一条本轮扫描汇总消息。
        groups: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
        for item in pending:
            targets = tuple(self._resolve_notify_userids(item))
            groups.setdefault(targets, []).append(item)
        for userids, items in groups.items():
            self._notify_scan_summary(items, list(userids))

    def _notify_scan_summary(self, items: List[Dict[str, Any]], userids: List[str]) -> None:
        """发送一条扫描结果汇总，并保存编号选择所需的交互状态。

        :param items: 当前通知目标对应的诊断项
        :param userids: Telegram 通知目标列表
        """
        summary_token = self._save_scan_summary(items)
        message_kwargs = {
            "mtype": NotificationType.Plugin if NotificationType else None,
            "title": "订阅下载增强：扫描结果",
            "text": render_scan_summary_text(items),
            "buttons": build_scan_summary_menu(summary_token, len(items)),
            "save_history": False,
        }
        try:
            self._post_message_to_targets(userids, message_kwargs)
        except Exception as exc:
            logger.warning(f"订阅下载增强发送扫描汇总失败: {exc}")

    @staticmethod
    def _notification_title(item: Any = None) -> str:
        if isinstance(item, dict):
            title = str(item.get("title") or "").strip()
        else:
            title = str(item or "").strip()
        return f"订阅下载增强：{title}" if title else "订阅下载增强"

    def _notify_next_queued_show(self):
        store = self._ensure_store()
        while True:
            item = store.pop_notification_queue()
            if not item:
                return
            ignore_key = self._ignore_key(item)
            if store.is_notification_suppressed(ignore_key):
                continue
            token = self._save_interaction(item)
            try:
                message_kwargs = {
                    "mtype": NotificationType.Plugin if NotificationType else None,
                    "title": self._notification_title(item),
                    "text": render_notification_text(item),
                    "buttons": build_main_menu(
                        token,
                        self._plugin_config.allow_tg_rule_update,
                        can_identifier_fix=item.get("reason") == "recognition_issue",
                        candidate_count=len(item.get("candidates") or []),
                        search_keyword_suggestion=item.get("search_keyword_suggestion") or "",
                        notification_suppression_days=self._plugin_config.notification_suppression_days,
                    ),
                    "save_history": False,
                }
                self._post_message_to_targets(
                    self._resolve_notify_userids(item),
                    message_kwargs,
                )
            except Exception as exc:
                logger.warning(f"订阅下载增强发送通知失败: {exc}")
            return

    @staticmethod
    def _target_to_userid(target: str) -> Optional[str]:
        """把带渠道前缀的目标值转成宿主 post_message 可用的 userid。

        规则：
        - 空值返回 None；
        - tg:xxx → xxx（TG 原生 Chat/用户 ID）；
        - qq:group:xxx → group:xxx（QQ 群 userid 约定）；
        - qq:xxx → xxx（QQ 私聊 openid）；
        - 无前缀裸值按 TG 原生值透传（兼容旧版）。

        :param target: 带渠道前缀的目标值
        :return: 宿主 userid；空输入返回 None
        """
        raw = str(target or "").strip()
        if not raw:
            return None
        if raw.startswith("qq:"):
            return raw[len("qq:"):]
        if raw.startswith("tg:"):
            raw = raw[len("tg:"):]
            return raw or None
        # 兼容历史脏数据（未重新保存前的旧映射）：形如「群组 -1003975240343」，
        # 提取末尾纯数字段作为 TG userid。
        parts = re.split(r"\s+", raw, maxsplit=1)
        if len(parts) == 2 and re.fullmatch(r"-?\d+", parts[1].strip()):
            return parts[1].strip()
        return raw or None

    def _default_group_chat_id(self) -> str:
        """读取通知渠道默认群组 Chat ID（TG 的 TELEGRAM_CHAT_ID 或 QQ 群）。

        供未命中「订阅通知管理」映射且未配置默认目标时兜底使用，确保通知
        落在群组而非 user/admin 私聊路由。返回带渠道前缀的目标值。

        :return: 群组目标值（tg:xxx / qq:group:xxx）；无可用渠道返回空串
        """
        channels = self._load_notification_channels()
        if not channels:
            return ""
        ordered = sorted(
            channels,
            key=lambda item: 0 if item["type"] == "telegram" else (1 if item["type"] == "qqbot" else 2),
        )
        for channel in ordered:
            if not isinstance(channel, dict):
                continue
            prefix = self._channel_kind(channel.get("type", "") if isinstance(channel, dict) else "")
            config = channel.get("config") or {}
            if prefix == "tg":
                ids = self._split_ids(config.get("TELEGRAM_CHAT_ID"))
                if ids:
                    return f"tg:{ids[0]}"
            elif prefix == "qq":
                ids = self._split_ids(config.get("QQ_GROUP_OPENID") or config.get("QQ_GROUP"))
                if ids:
                    return f"qq:group:{ids[0]}"
        return ""

    def _default_notify_userids(self) -> List[str]:
        """解析无订阅归属用户的默认通知目标 userid 列表。

        优先级：配置的默认目标（可多选） > 通知渠道默认群组。确保插件主动
        通知（全集包清理等）不会因缺少 userid 而落入 user/admin 私聊路由。
        返回的 userid 为宿主原生格式（已剥离渠道前缀），按序去重。

        :return: 目标 userid 列表；无可用目标返回空列表
        """
        external_config = self._load_external_notify_config()
        targets = self._split_targets(str(external_config.get("default_notify_target") or "").strip())
        if not targets:
            fallback = self._default_group_chat_id()
            targets = [fallback] if fallback else []
        userids: List[str] = []
        for target in targets:
            userid = self._target_to_userid(target)
            if userid and userid not in userids:
                userids.append(userid)
        return userids

    def _resolve_notify_userids(self, item: Dict[str, Any]) -> List[str]:
        """按订阅归属用户解析通知目标 userid 列表（支持多目标）。

        优先级：订阅通知管理映射（可多选） > 配置的默认目标（可多选） >
        通知渠道默认群组。返回宿主原生 userid（个人 ID 或群组 Chat ID），
        确保通知不会因缺少 userid 而落入 user/admin 私聊路由。

        :param item: 通知诊断项
        :return: 目标 userid 列表；无可用目标返回空列表
        """
        username = str(item.get("username") or "").strip()
        rules = self._load_external_notify_config().get("notify_rules") or {}
        raw_targets: List[str] = []
        if username:
            raw_targets = self._split_targets(str(rules.get(username) or "").strip())
        if not raw_targets:
            return self._default_notify_userids()
        userids: List[str] = []
        for target in raw_targets:
            userid = self._target_to_userid(target)
            if userid and userid not in userids:
                userids.append(userid)
        return userids

    def _post_message_to_targets(
        self,
        userids: List[str],
        message_kwargs: Dict[str, Any],
    ) -> None:
        """把同一条消息逐个发送到多个目标 userid。

        宿主 Telegram 发送按单 chat_id 处理，多目标由插件循环投递实现；
        不传 userid 的目标交由宿主默认路由（群）处理，避免与既有交互消息
        语义冲突。

        :param userids: 目标 userid 列表（已去重）
        :param message_kwargs: post_message 关键字参数（不含 userid）
        """
        if not userids:
            self.post_message(**message_kwargs)
            return
        for userid in userids:
            try:
                self.post_message(userid=userid, **message_kwargs)
            except Exception as exc:
                logger.warning(f"订阅下载增强发送通知到 {userid} 失败: {exc}")

    if eventmanager:
        @eventmanager.register(EventType.DownloadAdded)
        def handle_download_added(self, event):
            """监听订阅最终集整季包，先全选新包并登记后续清理。"""
            try:
                self._remember_season_pack_download(event)
            except Exception as exc:
                logger.warning(f"订阅下载增强登记整季包监听失败：{exc}")

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
            if str(action).strip().startswith("/sprule"):
                self._handle_sprule_command_text(str(action), event_data)
                return
            if str(action).strip().startswith("/sp"):
                self._handle_sp_command_text(str(action), event_data)
                return
            if not str(action).startswith(f"[PLUGIN]{PLUGIN_ID}|") and plugin_id != PLUGIN_ID:
                return
            self._handle_callback(str(action), event_data)

        @eventmanager.register(EventType.PluginAction)
        def handle_plugin_action(self, event):
            event_data = getattr(event, "event_data", None) or {}
            action = event_data.get("action") or (event_data.get("data") or {}).get("action")
            if action == "subscribeplus_pending":
                self._handle_sp_command_text("/sp", event_data)
                return
            if action == "subscribeplus_rule_identifier":
                args = event_data.get("arg_str") or event_data.get("args") or event_data.get("text") or ""
                if isinstance(args, (list, tuple)):
                    args = " ".join(str(item) for item in args)
                self._handle_sprule_command_text(
                    f"/sprule {str(args or '').strip()}".strip(),
                    event_data,
                )
                return
            if action != "subscribeplus_ci":
                return
            args = event_data.get("arg_str") or event_data.get("args") or event_data.get("text") or ""
            if isinstance(args, (list, tuple)):
                args = " ".join(str(item) for item in args)
            text = str(args or "").strip()
            self._handle_ci_command_text(f"/ci {text}".strip(), event_data)

        @eventmanager.register(EventType.TransferComplete)
        def handle_transfer_complete(self, event):
            try:
                self._prune_downloaded_scan_results()
            except Exception as exc:
                logger.warning(f"订阅下载增强入库后刷新诊断结果失败: {exc}")
            self._handle_transfer_complete_cleanup(event)

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
            state = self._ensure_store().load_interaction(token)
            self._ensure_store().delete_interaction(token)
            if state and state.get("summary_token"):
                self._ensure_store().delete_interaction(str(state.get("summary_token")))
            elif state and state.get("view") == "scan_summary":
                # 新的扫描汇总关闭后只删除这条汇总消息，不推进旧式通知队列。
                pass
            elif token != "spmenu":
                self._notify_next_queued_show()
            if not self._delete_callback_message(event_data):
                self._post_callback_message(event_data, title="订阅下载增强", text="已关闭本次交互。", save_history=False)
            return
        state = self._ensure_store().load_interaction(token)
        if not state:
            self._post_callback_message(event_data, title="订阅下载增强", text="交互已过期，请重新扫描。", save_history=False)
            return

        if op == "summary":
            summary_token = str(state.get("summary_token") or "").strip()
            summary_state = self._ensure_store().load_interaction(summary_token) if summary_token else None
            if not summary_state or summary_state.get("view") != "scan_summary":
                self._post_callback_message(event_data, title="订阅下载增强", text="扫描汇总已过期，请重新扫描。", save_history=False)
                return
            # 返回汇总时保留详情 token：旧详情消息上的按钮仍需可用，
            # 删除 token 会让它们直接命中「交互已过期」分支。
            state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
            self._ensure_store().save_interaction(token, state)
            items = summary_state.get("items") or []
            self._post_callback_message(
                event_data,
                title="订阅下载增强：扫描结果",
                text=render_scan_summary_text(items),
                buttons=build_scan_summary_menu(summary_token, len(items)),
                save_history=False,
            )
            return

        if op.startswith("show") and op[4:].isdigit() and state.get("view") == "scan_summary":
            index = int(op[4:]) - 1
            items = state.get("items") or []
            if not (0 <= index < len(items)):
                self._post_callback_message(event_data, title="订阅下载增强", text="汇总中的项目不存在。", save_history=False)
                return
            diagnosis = items[index]
            detail_token = self._save_interaction(diagnosis, summary_token=token)
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(
                    detail_token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                    candidate_count=len(diagnosis.get("candidates") or []),
                    search_keyword_suggestion=diagnosis.get("search_keyword_suggestion") or "",
                    notification_suppression_days=self._plugin_config.notification_suppression_days,
                    summary_token=token,
                ),
                save_history=False,
            )
            return

        diagnosis = state.get("diagnosis") or {}
        if op in {
            "rule",
            "rule-confirm",
            "rule-dict",
            "rule-dict-add-group",
            "rule-dict-delete-group",
            "rule-dict-add-platform",
            "rule-dict-delete-platform",
            "rule-custom",
            "rule-custom-add",
            "rule-custom-delete",
        } and not self._plugin_config.allow_tg_rule_update:
            self._post_callback_message(
                event_data,
                title="订阅下载增强",
                text="Telegram 修改订阅规则功能未授权，请先在插件配置中开启。",
                save_history=False,
            )
            return
        if op == "open":
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(
                    token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                    candidate_count=len(diagnosis.get("candidates") or []),
                    search_keyword_suggestion=diagnosis.get("search_keyword_suggestion") or "",
                    notification_suppression_days=self._plugin_config.notification_suppression_days,
                    summary_token=state.get("summary_token") or "",
                ),
                save_history=False,
            )
            return
        if op.startswith("cand"):
            page = max(safe_int(op.replace("cand", ""), 1) - 1, 0)
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=render_notification_text(diagnosis, candidate_page=page),
                buttons=build_main_menu(
                    token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                    candidate_count=len(diagnosis.get("candidates") or []),
                    candidate_page=page,
                    search_keyword_suggestion=diagnosis.get("search_keyword_suggestion") or "",
                    notification_suppression_days=self._plugin_config.notification_suppression_days,
                    summary_token=state.get("summary_token") or "",
                ),
                save_history=False,
            )
            return
        if op.startswith("rpage"):
            page = max(safe_int(op.replace("rpage", ""), 1) - 1, 0)
            self._post_callback_message(
                event_data,
                title=f"选择下载：{diagnosis.get('title')}",
                text="请选择要下载的候选资源。",
                buttons=build_resource_menu(token, diagnosis.get("candidates") or [], page=page),
                save_history=False,
            )
            return
        if op == "suppress":
            days = int(getattr(self._plugin_config, "notification_suppression_days", 0) or 0)
            if days <= 0:
                self._post_callback_message(
                    event_data,
                    title=self._notification_title(diagnosis),
                    text="通知抑制已关闭，请在插件“清理与候选”中设置大于 0 的通知抑制天数。",
                    save_history=False,
                )
                return
            until = (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")
            self._ensure_store().save_notification_suppression(self._ignore_key(diagnosis), until)
            # 抑制通知不等于关闭交互：保留详情 token，旧详情消息上的
            # 「返回汇总」等按钮继续可用。
            state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
            self._ensure_store().save_interaction(token, state)
            summary_token = str(state.get("summary_token") or "").strip()
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=f"已设置 {days} 天内不通知，直到 {until}",
                buttons=build_summary_back_menu(token) if summary_token else None,
                save_history=False,
            )
            self._notify_next_queued_show()
            return
        if op == "keyword":
            suggestion = str(diagnosis.get("search_keyword_suggestion") or "").strip()
            if not suggestion:
                self._post_callback_message(
                    event_data,
                    title=self._notification_title(diagnosis),
                    text="当前诊断没有可添加的罗马音搜索关键词。",
                    save_history=False,
                )
                return
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=(
                    "是否将以下罗马音写入该订阅的搜索关键词？\n"
                    f"{suggestion}\n\n只修改搜索关键词，不修改站点、包含规则或其他订阅设置。"
                ),
                buttons=build_keyword_confirm_menu(token),
                save_history=False,
            )
            return
        if op == "keyword-confirm":
            suggestion = str(diagnosis.get("search_keyword_suggestion") or "").strip()
            subscribe_id = safe_int(diagnosis.get("subscribe_id"), 0)
            if not suggestion or not subscribe_id:
                self._post_callback_message(
                    event_data,
                    title=self._notification_title(diagnosis),
                    text="缺少订阅或罗马音关键词，无法保存。",
                    save_history=False,
                )
                return
            try:
                result = self._update_subscribe(subscribe_id, {"keyword": suggestion})
                subscribe = self._get_subscribe(subscribe_id)
                saved_keyword = str(getattr(subscribe, "keyword", "") or "").strip() if subscribe else ""
                if not result.get("updated") or saved_keyword != suggestion:
                    raise RuntimeError("MoviePilot 回读的搜索关键词与写入值不一致")
                diagnosis["search_keyword_suggestion"] = ""
                state["diagnosis"] = diagnosis
                state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
                self._ensure_store().save_interaction(token, state)
                logger.info(
                    "订阅下载增强已写入订阅搜索关键词："
                    f"订阅ID={subscribe_id}，关键词={suggestion}"
                )
                self._post_callback_message(
                    event_data,
                    title=self._notification_title(diagnosis),
                    text=f"已添加订阅搜索关键词：{suggestion}",
                    buttons=build_main_menu(
                        token,
                        self._plugin_config.allow_tg_rule_update,
                        can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                        candidate_count=len(diagnosis.get("candidates") or []),
                        notification_suppression_days=self._plugin_config.notification_suppression_days,
                    ),
                    save_history=False,
                )
            except Exception as exc:
                self._post_callback_message(
                    event_data,
                    title=self._notification_title(diagnosis),
                    text=f"添加订阅搜索关键词失败：{exc}",
                    buttons=build_keyword_confirm_menu(token),
                    save_history=False,
                )
            return
        if op == "download":
            if diagnosis.get("source") in {"plugin_pt_scope", "romaji_fallback"}:
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
                        title=self._notification_title(diagnosis),
                        text="插件 PT 范围搜索没有可下载候选资源。",
                        buttons=build_main_menu(
                            token,
                            self._plugin_config.allow_tg_rule_update,
                            can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                            candidate_count=len(diagnosis.get("candidates") or []),
                            search_keyword_suggestion=diagnosis.get("search_keyword_suggestion") or "",
                            notification_suppression_days=self._plugin_config.notification_suppression_days,
                            summary_token=state.get("summary_token") or "",
                        ),
                        save_history=False,
                    )
                return
            result = self._start_moviepilot_subscribe_search(diagnosis)
            # 触发订阅搜索后同样保留详情 token，避免旧详情消息按钮立即失效。
            state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
            self._ensure_store().save_interaction(token, state)
            summary_token = str(state.get("summary_token") or "").strip()
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=result.get("message") or ("Started MP subscribe search" if result.get("success") else "Failed to start MP subscribe search"),
                buttons=build_summary_back_menu(token) if summary_token else None,
                save_history=False,
            )
            self._notify_next_queued_show()
            return
        if op == "ptscope":
            # 弹出"其他站点"选择菜单（PT 搜索范围 - 订阅站点），不立即搜索
            other_sites = self._compute_other_sites(diagnosis)
            state["other_sites"] = other_sites
            state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
            self._ensure_store().save_interaction(token, state)
            if other_sites:
                site_label = "、".join(s.get("name") for s in other_sites)
                text = f"选择要搜索的其他站点（订阅站点之外）：\n可搜站点：{site_label}"
            else:
                text = "没有可搜索的其他站点。订阅站点已覆盖 PT 搜索范围内的全部站点。"
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=text,
                buttons=build_other_sites_menu(token, other_sites),
                save_history=False,
            )
            return
        if op == "ptsall" or (op.startswith("pts") and op[3:].isdigit()):
            other_sites = state.get("other_sites") or self._compute_other_sites(diagnosis)
            if op == "ptsall":
                only_sites = [str(s.get("id")) for s in other_sites]
            else:
                idx = int(op[3:])
                only_sites = [str(other_sites[idx].get("id"))] if 0 <= idx < len(other_sites) else []
            diagnosis = self._manual_pt_scope_diagnosis(diagnosis, only_sites=only_sites)
            state["diagnosis"] = diagnosis
            state["expires_at"] = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
            self._ensure_store().save_interaction(token, state)
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(
                    token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                    candidate_count=len(diagnosis.get("candidates") or []),
                    search_keyword_suggestion=diagnosis.get("search_keyword_suggestion") or "",
                    notification_suppression_days=self._plugin_config.notification_suppression_days,
                    summary_token=state.get("summary_token") or "",
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
                platforms=self._custom_platforms_for_suggestions(),
            )
            custom_groups, custom_platforms = self._load_rule_dictionary()
            self._post_callback_message(
                event_data,
                title=f"调整订阅规则：{diagnosis.get('title')}",
                text="请选择要添加的官组、平台关键词或 PT 站点。",
                buttons=build_rule_menu(
                    token,
                    suggestions,
                    custom_identifier_count=len(self._load_custom_identifiers()),
                    custom_release_group_count=len(custom_groups),
                    custom_platform_count=len(custom_platforms),
                ),
                save_history=False,
            )
            return
        if op == "rule-dict":
            groups, platforms = self._load_rule_dictionary()
            self._post_callback_message(
                event_data,
                title="自定义官组/平台",
                text=(
                    f"当前自定义官组（{len(groups)}）：{', '.join(groups) or '无'}\n"
                    f"当前自定义平台（{len(platforms)}）：{', '.join(platforms) or '无'}\n\n"
                    "通过下方按钮查看命令格式，修改后会同步到本插件的网页规则建议和 Telegram 菜单。"
                ),
                buttons=build_rule_dictionary_menu(token, len(groups), len(platforms)),
                save_history=False,
            )
            return
        if op in {
            "rule-dict-add-group",
            "rule-dict-delete-group",
            "rule-dict-add-platform",
            "rule-dict-delete-platform",
        }:
            command = {
                "rule-dict-add-group": "/sprule TOKEN add-group 关键词",
                "rule-dict-delete-group": "/sprule TOKEN del-group 关键词",
                "rule-dict-add-platform": "/sprule TOKEN add-platform 关键词",
                "rule-dict-delete-platform": "/sprule TOKEN del-platform 关键词",
            }[op].replace("TOKEN", token)
            self._post_callback_message(
                event_data,
                title="自定义官组/平台",
                text=f"请发送命令：\n{command}\n\n关键词支持空格，确认后立即同步网页和 Telegram 规则建议。",
                buttons=build_rule_dictionary_menu(
                    token,
                    len(self._load_rule_dictionary()[0]),
                    len(self._load_rule_dictionary()[1]),
                ),
                save_history=False,
            )
            return
        if op == "rule-custom":
            identifiers = self._load_custom_identifiers()
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=(
                    f"当前全局自定义识别词：{len(identifiers)} 条\n"
                    "新增或删除请使用 /sprule TOKEN add|del 规则。"
                ),
                buttons=build_rule_custom_menu(token, len(identifiers)),
                save_history=False,
            )
            return
        if op in {"rule-custom-add", "rule-custom-delete"}:
            verb = "add" if op.endswith("add") else "del"
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=f"请发送命令：\n/sprule {token} {verb} 规则文本",
                buttons=build_rule_custom_menu(token, len(self._load_custom_identifiers())),
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
        if re.fullmatch(r"rule\d+", op):
            index = int(op.replace("rule", "") or 0) - 1
            suggestions = build_rule_suggestions(
                diagnosis.get("candidates") or [],
                release_groups=self._release_groups_for_diagnosis(diagnosis),
                platforms=self._custom_platforms_for_suggestions(),
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
        if op == "back":
            self._post_callback_message(
                event_data,
                title=self._notification_title(diagnosis),
                text=render_notification_text(diagnosis),
                buttons=build_main_menu(
                    token,
                    self._plugin_config.allow_tg_rule_update,
                    can_identifier_fix=diagnosis.get("reason") == "recognition_issue",
                    candidate_count=len(diagnosis.get("candidates") or []),
                    search_keyword_suggestion=diagnosis.get("search_keyword_suggestion") or "",
                    notification_suppression_days=self._plugin_config.notification_suppression_days,
                    summary_token=state.get("summary_token") or "",
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
            name_map: Dict[int, str] = {}
            for site in self._ensure_site_resolver().available_sites():
                sid = str(site.get("id") or "")
                if sid.isdigit():
                    name_map[int(sid)] = site.get("name") or sid
            preview = build_rule_preview(subscribe, pattern, source=source, name_map=name_map)
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
            return self._record_identifier_tool_failure("", {}, "媒体文件名不能为空", "missing_title", source, "force")
        media_type = normalize_media_type(payload.get("media_type") or payload.get("type"))
        tmdbid = safe_int(payload.get("tmdbid") or payload.get("tmdb_id"), 0)
        if media_type == "unknown" or not tmdbid:
            return self._record_identifier_tool_failure(
                title,
                {},
                "请填写 movie/tv 和 TMDB ID",
                "missing_target",
                source,
                "force",
            )
        target = {
            "media_type": media_type,
            "tmdbid": tmdbid,
        }
        return self._apply_manual_identifier_rule(title, target, source, mode="force")

    def _identifier_year(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        title = self._identifier_title_from_payload(payload)
        if not title:
            return self._record_identifier_tool_failure("", {}, "媒体文件名不能为空", "missing_title", source, "year")
        media_type = normalize_media_type(payload.get("media_type") or payload.get("type"))
        tmdbid = safe_int(payload.get("tmdbid") or payload.get("tmdb_id"), 0)
        if media_type == "unknown" or not tmdbid:
            return self._record_identifier_tool_failure(
                title,
                {},
                "请填写 movie/tv 和 TMDB ID",
                "missing_target",
                source,
                "year",
            )
        return self._apply_manual_identifier_rule(
            title,
            {"media_type": media_type, "tmdbid": tmdbid},
            source,
            mode="year",
        )

    def _apply_manual_identifier_rule(
        self, title: str, target: Dict[str, Any], source: str, mode: str
    ) -> Dict[str, Any]:
        target = dict(target or {})
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
        target["name"] = tmdb_summary.get("name") or ""
        target["year"] = tmdb_summary.get("year") or ""
        # 手动模式由用户显式指定 TMDB ID，门禁只做记录与提示，不阻断写入。
        precheck = self._precheck_identifier_target(
            title, target, media_info=tmdb_summary.get("media_info")
        )
        try:
            if mode == "year":
                block = build_year_identifier_block(title, target)
            else:
                block = build_force_identifier_block(title, target)
            rule = block[-1]
        except ValueError as exc:
            return self._record_identifier_tool_failure(
                title, target, str(exc), "invalid_rule", source, mode
            )

        try:
            applied = self._append_custom_identifiers(block)
        except Exception as exc:
            return self._record_identifier_tool_failure(
                title,
                target,
                f"写入自定义识别词失败：{exc}",
                "write_failed",
                source,
                mode,
            )

        recheck = self._recognize_identifier_title(title, target)
        success = bool(recheck.get("success"))
        if success:
            message = "已写入强制绑定规则" if mode == "force" else "已写入年份修正规则"
            if not applied.get("added"):
                message = "识别词已存在，再次识别已命中"
            reason = ""
            status = "success"
        else:
            message = recheck.get("message") or "识别词已写入，但再次识别未命中目标 TMDB"
            reason = recheck.get("reason") or "recognize_failed"
            status = "failed"
        if not precheck.get("aligned"):
            message = f"{message}（提示：{precheck.get('message') or '写前校验未通过'}）"

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
        record.update(
            {
                "mode": mode,
                "rule": "\n".join(block),
                "total_count": applied.get("total_count"),
                "precheck": precheck,
                "recheck": recheck,
            }
        )
        if reason:
            record["reason"] = reason
        self._ensure_store().append_identifier_record(record)
        return {"success": success, "message": message, "reason": reason, "data": record}

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
        # 季集只用于记录展示，不再写入识别词规则本身，避免把季集钉死在某一集。
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

        precheck = self._precheck_identifier_target(
            title, target, media_info=tmdb_summary.get("media_info")
        )
        if not precheck.get("aligned"):
            return self._record_identifier_tool_failure(
                title,
                target,
                precheck.get("message") or "写前校验未通过",
                precheck.get("reason") or "precheck_failed",
                source,
                mode,
            )

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
        record["precheck"] = precheck
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

    @staticmethod
    def _format_episode_number(episode: int) -> str:
        return f"E{episode:02d}" if episode else ""

    @classmethod
    def _format_episode_summary(cls, episodes: List[Any]) -> str:
        values: List[str] = []
        for raw in episodes or []:
            if isinstance(raw, dict):
                episode = safe_int(raw.get("episode"), 0)
            else:
                episode = safe_int(getattr(raw, "episode", 0), 0)
            label = cls._format_episode_number(episode)
            if label and label not in values:
                values.append(label)
        return "/".join(values)

    @classmethod
    def _format_download_log_context(
        cls,
        title: str,
        subscribe_id: int = 0,
        tmdbid: int = 0,
        season: int = 0,
        episodes: Optional[List[Any]] = None,
        media_source: str = "",
        media_id: str = "",
    ) -> str:
        fields = [f"剧名={str(title or '').strip() or '未知'}"]
        if subscribe_id:
            fields.append(f"订阅ID={subscribe_id}")
        if media_source and media_id:
            fields.append(f"{media_source}:{media_id}")
        elif tmdbid:
            fields.append(f"TMDB={tmdbid}")
        if season:
            fields.append(f"S{season:02d}")
        episode_summary = cls._format_episode_summary(episodes or [])
        if episode_summary:
            fields.append(f"缺失={episode_summary}")
        return "，".join(fields)

    @classmethod
    def _format_item_log_context(cls, item: DiagnosisInput) -> str:
        source, identity = SubscribePlus._item_identity(item)
        return cls._format_download_log_context(
            title=item.title,
            subscribe_id=safe_int(item.subscribe_id, 0),
            tmdbid=safe_int(item.tmdbid, 0),
            season=safe_int(item.season, 0),
            episodes=list(item.episodes or []),
            media_source=source,
            media_id=identity,
        )

    @classmethod
    def _format_diagnosis_log_context(cls, diagnosis: Dict[str, Any], candidate: Optional[Dict[str, Any]] = None) -> str:
        episodes = list(diagnosis.get("episodes") or [])
        if candidate and safe_int(candidate.get("episode"), 0):
            episodes.append(candidate)
        media_source, media_id = normalize_identity(
            diagnosis.get("media_source"), diagnosis.get("media_id")
        )
        if not media_id and safe_int(diagnosis.get("tmdbid") or diagnosis.get("tmdb_id"), 0):
            media_source = DEFAULT_MEDIA_SOURCE
            media_id = str(safe_int(diagnosis.get("tmdbid") or diagnosis.get("tmdb_id"), 0))
        return cls._format_download_log_context(
            title=str(diagnosis.get("title") or ""),
            subscribe_id=safe_int(diagnosis.get("subscribe_id"), 0),
            tmdbid=safe_int(diagnosis.get("tmdbid") or diagnosis.get("tmdb_id"), 0),
            season=safe_int((candidate or {}).get("season") or diagnosis.get("season"), 0),
            episodes=episodes,
            media_source=media_source,
            media_id=media_id,
        )

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
        media_source, media_id = normalize_identity(
            payload.get("media_source"), payload.get("media_id")
        )
        if not media_id and tmdbid:
            media_source, media_id = DEFAULT_MEDIA_SOURCE, str(tmdbid)
        for item in self._ensure_store().load_scan_results():
            if subscribe_id and safe_int(item.get("subscribe_id"), 0) == subscribe_id:
                return item
            if media_id and self._diagnosis_identity_matches(item, media_source, media_id):
                return item
        return {}

    @staticmethod
    def _diagnosis_identity_matches(item: Dict[str, Any], media_source: str, media_id: str) -> bool:
        """判断诊断快照的媒体身份是否命中目标，兼容只有 tmdbid 的旧快照。"""
        if not media_id:
            return False
        snapshot_source, snapshot_id = normalize_identity(
            item.get("media_source"), item.get("media_id")
        )
        if not snapshot_id:
            legacy = safe_int(item.get("tmdbid"), 0)
            if legacy:
                snapshot_source, snapshot_id = DEFAULT_MEDIA_SOURCE, str(legacy)
        return bool(snapshot_id) and snapshot_source == media_source and snapshot_id == media_id

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
            mediainfo = MediaChain().recognize_media(mtype=mtype, media_source=MediaSource.TMDB, media_id=str(tmdbid))
            if not mediainfo:
                return {"success": False, "message": "TMDB 没有查到可用数据"}
            return {
                "success": True,
                "name": str(getattr(mediainfo, "title", "") or getattr(mediainfo, "name", "") or "").strip(),
                "year": str(getattr(mediainfo, "year", "") or "").strip(),
                "media_info": mediainfo,
            }
        except Exception as exc:
            logger.warning(f"订阅下载增强校验 TMDB 目标失败 TMDB={tmdbid}: {exc}")
            return {"success": False, "message": f"TMDB 校验失败：{exc}"}

    @staticmethod
    def _run_coro_sync(coro: Any) -> Any:
        """同步执行协程，兼容当前线程已存在运行中事件循环的情况。

        asyncio.run 在已有运行中的事件循环里会抛 RuntimeError；此时
        loop.run_until_complete 同样会因为循环正在运行而失败，因此改用独立
        线程运行 asyncio.run，避免 "event loop is already running"。
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # 当前线程没有运行中的事件循环，直接同步执行
            return asyncio.run(coro)
        # 已在运行中的事件循环里，切换到独立线程执行，避免阻塞/报错
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()

    @classmethod
    def _get_llm_sync(cls):
        """获取可同步调用的 LLM 实例。

        兼容 app.helper.llm 与 app.agent.llm 两个导入路径，并在 get_llm
        返回协程时安全地同步等待其结果。
        """
        try:
            from app.agent.llm import LLMHelper
        except Exception:
            try:
                from app.agent.llm import LLMHelper
            except Exception as exc:
                raise RuntimeError("AI 未配置或 LLMHelper 不可用") from exc

        llm = LLMHelper.get_llm(streaming=False)
        if hasattr(llm, "__await__"):
            llm = cls._run_coro_sync(llm)
        return llm

    def _identify_target_by_ai(self, title: str) -> Dict[str, Any]:
        llm = self._get_llm_sync()
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

    def _recognize_raw_title(self, title: str) -> Dict[str, Any]:
        """用宿主自身识别链路解析原始标题，返回 TMDB、类型与媒体信息。

        写前门禁与写后复验都复用这一条路径，保证两次判断口径一致。
        """
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain
            from app.sdk.media import MetaInfo

            meta = MetaInfo(title)
            mediainfo = MediaChain().recognize_media(meta=meta, cache=False)
        except Exception as exc:
            return {"success": False, "message": f"识别失败：{exc}", "reason": "recognize_failed"}
        if not mediainfo:
            return {
                "success": True,
                "recognized": False,
                "tmdbid": 0,
                "media_type": "unknown",
                "title": "",
                "media_info": None,
            }
        return {
            "success": True,
            "recognized": True,
            "tmdbid": safe_int(
                getattr(mediainfo, "tmdb_id", None) or getattr(mediainfo, "tmdbid", None),
                0,
            ),
            "media_type": normalize_media_type(
                getattr(mediainfo, "type", None) or getattr(mediainfo, "media_type", None)
            ),
            "title": str(getattr(mediainfo, "title", "") or ""),
            "media_info": mediainfo,
        }

    def _recognize_identifier_title(self, title: str, target: Dict[str, Any]) -> Dict[str, Any]:
        """写后复验：确认写入的识别词让宿主重新识别到目标 TMDB。"""
        raw = self._recognize_raw_title(title)
        if raw.get("success") is False:
            return {
                "success": False,
                "message": raw.get("message") or "再次识别失败",
                "reason": raw.get("reason") or "recognize_failed",
            }
        recognized_tmdbid = safe_int(raw.get("tmdbid"), 0)
        expected_tmdbid = safe_int(target.get("tmdbid"), 0)
        matched = bool(recognized_tmdbid and recognized_tmdbid == expected_tmdbid)
        return {
            "success": matched,
            "message": "再次识别成功" if matched else "再次识别未命中目标 TMDB",
            "recognized_title": raw.get("title") or "",
            "tmdbid": recognized_tmdbid,
        }

    @staticmethod
    def _normalize_match_text(value: Any) -> str:
        """归一化文本用于名称比对：去括号噪声、统一小写、只保留字母数字与汉字。"""
        text = str(value or "").lower()
        text = re.sub(r"[\[\]【】（）()]", "", text)
        return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)

    def _collect_tmdb_target_names(
        self,
        target: Dict[str, Any],
        media_info: Any = None,
        include_ai_names: bool = False,
    ) -> List[str]:
        """收集目标媒体的可用名称，默认只取 TMDB 权威名称。

        AI 给出的 name/title 通常直接来自文件名，参与比对会形成同义反复，
        无法发现「AI 编造 TMDB ID」的情况，因此默认排除；仅在显式要求时使用。
        """
        raw_names: List[Any] = []
        if include_ai_names:
            raw_names.extend([target.get("name"), target.get("title")])
        for attr in (
            "title",
            "en_title",
            "original_title",
            "original_name",
            "hk_title",
            "tw_title",
            "sg_title",
        ):
            if media_info is not None:
                raw_names.append(getattr(media_info, attr, None))
        if media_info is not None:
            raw_names.extend(getattr(media_info, "names", None) or [])
        names: List[str] = []
        for item in raw_names:
            normalized = self._normalize_match_text(item)
            if normalized and normalized not in names:
                names.append(normalized)
        return names

    def _precheck_identifier_target(
        self, title: str, target: Dict[str, Any], media_info: Any = None
    ) -> Dict[str, Any]:
        """写前门禁：用宿主识别结果与 TMDB 名称别名校验 AI 目标是否可信。

        1) 宿主已识别出其它 TMDB ID：判定为冲突，拒绝写入全局识别词；
        2) 宿主未识别出结果：要求文件名锚点与目标 TMDB ID 解出的权威名称/别名存在
           文本交集，否则判定目标不可信，同样不写入。比对只用 TMDB 侧名称，不使用
           AI 自述名称，避免与文件名同义反复、放过被编造的 TMDB ID。
        """
        media_type = normalize_media_type(target.get("media_type") or target.get("type"))
        tmdbid = safe_int(target.get("tmdbid") or target.get("tmdb_id"), 0)
        raw = self._recognize_raw_title(title)
        recognized_tmdbid = safe_int(raw.get("tmdbid"), 0)
        result: Dict[str, Any] = {
            "recognized_tmdbid": recognized_tmdbid,
            "recognized_title": str(raw.get("title") or ""),
            "recognized_type": normalize_media_type(raw.get("media_type")),
        }
        if raw.get("success") is False:
            result.update(
                {
                    "aligned": True,
                    "verified_by": "recognize_error",
                    "reason": "",
                    "message": "宿主识别不可用，跳过写前校验并交由写后复验确认",
                }
            )
            return result
        if recognized_tmdbid:
            if recognized_tmdbid == tmdbid:
                result.update(
                    {
                        "aligned": True,
                        "verified_by": "recognize_tmdbid",
                        "reason": "",
                        "message": "与宿主识别结果一致",
                    }
                )
            else:
                result.update(
                    {
                        "aligned": False,
                        "verified_by": "recognize_tmdbid",
                        "reason": "ai_mismatch",
                        "message": (
                            f"拒绝写入：宿主识别为 TMDB {recognized_tmdbid}，"
                            f"与目标 TMDB {tmdbid} 不一致"
                        ),
                    }
                )
            return result
        anchor = self._normalize_match_text(identifier_anchor(title, media_type))
        matched_name = ""
        for name in self._collect_tmdb_target_names(target, media_info):
            if len(name) < 3:
                continue
            if name in anchor or (len(anchor) >= 3 and anchor in name):
                matched_name = name
                break
        if matched_name:
            result.update(
                {
                    "aligned": True,
                    "verified_by": "title_alias",
                    "matched_name": matched_name,
                    "reason": "",
                    "message": "宿主未识别，但文件名与目标名称/别名匹配",
                }
            )
        else:
            result.update(
                {
                    "aligned": False,
                    "verified_by": "title_alias",
                    "reason": "ai_unverified",
                    "message": "拒绝写入：宿主未识别且文件名与目标媒体名称/别名无交集，目标不可信",
                }
            )
        return result

    def _suggest_identifier_lines_by_ai(self, title: str, target: Dict[str, Any]) -> List[str]:
        llm = self._get_llm_sync()
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
        # 写入前先从数据库刷新配置快照：宿主快照可能落后于外部（网关/界面）写入，
        # 直接用旧快照做「新增 + 旧值」会把别处刚加的识别词覆盖掉。
        try:
            oper.load_snapshot()
        except Exception as exc:
            logger.warning(f"订阅下载增强刷新系统配置快照失败，继续使用当前快照: {exc}")
        existing = oper.get(key) or []
        existing = self._flatten_words(existing)
        added = dedupe_identifier_blocks(existing, lines)
        if added:
            # 识别词按顺序应用，新规则必须置顶才能优先生效。
            oper.set(key, added + existing)
            try:
                refresh_identifier_runtime_cache()
            except Exception as exc:
                logger.warning(f"订阅下载增强刷新识别词缓存失败: {exc}")
        return {"added": added, "total_count": len(existing) + len(added)}

    def _load_custom_identifiers(self) -> List[str]:
        """读取并清洗全局自定义识别词，保留宿主原有顺序。"""
        try:
            from app.db.systemconfig_oper import SystemConfigOper

            key = getattr(SystemConfigKey, "CustomIdentifiers", "CustomIdentifiers")
            values = self._flatten_words(SystemConfigOper().get(key))
            result: List[str] = []
            for value in values:
                normalized = normalize_identifier_line(value)
                if normalized and normalized not in result:
                    result.append(normalized)
            return result
        except Exception as exc:
            logger.warning(f"订阅下载增强读取自定义识别词失败: {exc}")
            return []

    def _add_custom_identifier_values(self, values: Any) -> Dict[str, Any]:
        """把用户提交的识别词追加到全局词表，并刷新运行时缓存。"""
        candidates = self._flatten_words(values)
        lines = [normalize_identifier_line(value) for value in candidates]
        lines = [value for value in lines if value and validate_identifier_rule(value)]
        if not lines:
            return {"success": False, "message": "请提供有效的自定义识别词规则"}
        try:
            applied = self._append_custom_identifiers(lines)
            identifiers = self._load_custom_identifiers()
            return {
                "success": True,
                "message": f"已增加 {len(applied.get('added') or [])} 条自定义识别词",
                "data": {
                    "added": applied.get("added") or [],
                    "count": len(identifiers),
                    "identifiers": identifiers,
                },
            }
        except Exception as exc:
            logger.error(f"订阅下载增强增加自定义识别词失败: {exc}", exc_info=True)
            return {"success": False, "message": f"增加自定义识别词失败：{exc}"}

    def _delete_custom_identifier_values(self, values: Any) -> Dict[str, Any]:
        """从全局词表删除用户指定的识别词，并刷新运行时缓存。"""
        candidates = {
            normalize_identifier_line(value)
            for value in self._flatten_words(values)
            if normalize_identifier_line(value)
        }
        if not candidates:
            return {"success": False, "message": "请提供要删除的自定义识别词规则"}
        try:
            from app.db.systemconfig_oper import SystemConfigOper

            key = getattr(SystemConfigKey, "CustomIdentifiers", "CustomIdentifiers")
            current = self._flatten_words(SystemConfigOper().get(key))
            kept = [value for value in current if normalize_identifier_line(value) not in candidates]
            removed = len(current) - len(kept)
            if removed:
                SystemConfigOper().set(key, kept or None)
                try:
                    refresh_identifier_runtime_cache()
                except Exception as exc:
                    logger.warning(f"订阅下载增强刷新识别词缓存失败: {exc}")
            identifiers = self._load_custom_identifiers()
            return {
                "success": True,
                "message": f"已删除 {removed} 条自定义识别词" if removed else "未找到要删除的自定义识别词",
                "data": {
                    "removed": removed,
                    "count": len(identifiers),
                    "identifiers": identifiers,
                },
            }
        except Exception as exc:
            logger.error(f"订阅下载增强删除自定义识别词失败: {exc}", exc_info=True)
            return {"success": False, "message": f"删除自定义识别词失败：{exc}"}

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
            from app.sdk.media import MetaInfo

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
            logger.info(
                "订阅下载增强触发 MP 原生订阅搜索成功："
                f"{self._format_diagnosis_log_context(diagnosis)}"
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
        from_cache = False
        if not context:
            # 内存上下文丢失（如插件重载/重启），尝试从本地缓存重建
            try:
                cached = self._ensure_store().load_candidate_cache(
                    str(candidate_id),
                    self._plugin_config.candidate_cache_days,
                )
                if cached:
                    context = self._rebuild_context_from_cache(cached)
                    from_cache = bool(context)
            except Exception as exc:
                logger.warning(f"订阅下载增强读取候选缓存失败: {exc}")
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
            logger.info(
                "订阅下载增强提交候选资源下载成功："
                f"{self._format_diagnosis_log_context(diagnosis, candidate)}，"
                f"站点={candidate.get('site_name') or candidate.get('site') or '未知'}，"
                f"候选={candidate.get('title') or candidate_id or '未知'}，"
                f"来源={'本地缓存重建' if from_cache else '内存上下文'}"
            )
            done_text = "已提交下载任务（缓存重建）。" if from_cache else "已提交下载任务。"
            self._post_callback_message(event_data, title="订阅下载增强", text=done_text, save_history=False)
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

    def _handle_transfer_complete_cleanup(self, _event):
        """整季包统一由 DownloadAdded 处理，TransferComplete 不再重复清理。"""
        return

    def _remember_season_pack_download(self, event) -> None:
        """登记命中最终播出集的整季包，并立即将 qB 文件全部设为下载。"""
        config = getattr(self, "_plugin_config", PluginConfig.from_dict({}))
        qb_mode = normalize_qb_cleanup_mode(getattr(config, "season_pack_qb_cleanup", QB_CLEANUP_OFF))
        if not config.enabled or not config.season_pack_enabled:
            return
        event_data = getattr(event, "event_data", None) or {}
        if not isinstance(event_data, dict):
            return
        context = event_data.get("context")
        meta = self._read_cleanup_value(context, "meta_info")
        media = self._read_cleanup_value(context, "media_info")
        torrent = self._read_cleanup_value(context, "torrent_info")
        if not context or not meta or not media or not torrent:
            return
        media_type = self._read_cleanup_value(media, "type", "media_type")
        media_type_text = str(getattr(media_type, "value", media_type) or "").strip().lower()
        if media_type_text not in {str(MediaType.TV.value).lower(), "tv", "电视剧"}:
            return
        media_source, media_id = self._object_identity(media)
        season = safe_int(
            self._read_cleanup_value(meta, "begin_season", "season_seq", "season"),
            0,
        )
        if not season:
            seasons = self._read_cleanup_value(meta, "season_list") or []
            season = safe_int(seasons[0], 0) if seasons else 0
        title = str(self._read_cleanup_value(torrent, "title") or "").strip()
        title_episodes = parse_episode_numbers(title)
        episodes = set(title_episodes)
        episodes.update(
            parse_episode_numbers(self._read_cleanup_value(meta, "episode_list"))
        )
        episodes.update(parse_episode_numbers(event_data.get("episodes")))
        if not (media_source and media_id and season and title):
            return
        season_completed, final_episode, final_air_date = is_completed_by_air_date(
            self._load_episodes(
                media_source,
                media_id,
                season,
                self._read_cleanup_value(media, "episode_group"),
                force_refresh=False,
            ),
            datetime.now().date(),
            config.delay_days,
        )
        is_pack = is_season_pack_title(title, season)
        if not season_completed or not final_episode or not is_pack:
            return
        if title_episodes and final_episode not in title_episodes:
            # 标题明确给出集数范围时，必须由标题本身覆盖最终集；
            # 不能用 MP 事件中的分集信息把 E01-E06 之类部分包扩成整季包。
            return
        if not title_episodes:
            # 对明确的 Sxx/Complete 整季包，标题没有逐集范围时按播出日历补齐。
            episodes = set(range(1, final_episode + 1))
        episodes = {episode for episode in episodes if 0 < episode <= final_episode}
        if final_episode not in episodes or len(episodes) < 2:
            return
        download_hash = str(event_data.get("hash") or event_data.get("download_hash") or "").strip()
        if not download_hash:
            return
        downloader = str(event_data.get("downloader") or "").strip()
        current = {
            "download_hash": download_hash,
            "downloader": downloader,
            "torrent_name": title,
            "seasons": f"S{season:02d}",
            "episodes": ",".join(f"E{episode:02d}" for episode in sorted(episodes)),
            "media_source": media_source,
            "media_id": media_id,
        }
        full_download = self._ensure_season_pack_full_download(current, event_data)
        if not full_download.get("ok"):
            logger.info(
                f"订阅下载增强跳过整季包替换：qB 全部文件未成功设为下载，hash={download_hash}"
            )
            return
        if not config.enabled or not config.season_pack_enabled or qb_mode == QB_CLEANUP_OFF:
            return
        save_path = self._qb_save_path_for_hash(download_hash, downloader)
        old_tasks = self._find_qb_single_tasks_for_pack(
            title=title,
            season=season,
            total_episode=final_episode,
            save_path=save_path,
            downloader=downloader,
            pack_hash=download_hash,
        )
        watch = {
            "download_hash": download_hash,
            "downloader": downloader,
            "torrent_name": title,
            "media_source": media_source,
            "media_id": media_id,
            "season": season,
            "final_episode": final_episode,
            "final_air_date": final_air_date,
            "episodes": sorted(episodes),
            "old_tasks": old_tasks,
            "full_download": full_download,
            "cleanup_mode": qb_mode,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        cleanup_result = self._process_old_qb_tasks(old_tasks, qb_mode)
        if cleanup_result["pending_tasks"]:
            watch["old_tasks"] = cleanup_result["pending_tasks"]
            self._ensure_store().save_season_pack_watch(watch)
            logger.warning(
                "订阅下载增强整季包旧任务清理未全部结束，保留精确任务等待重试："
                f"{title}，qB失败={cleanup_result['qb'].get('failed', 0)}，"
                f"MV3失败={cleanup_result['mv3'].get('failed', 0)}"
            )
        else:
            self._ensure_store().delete_season_pack_watch(download_hash)
        logger.info(
            "订阅下载增强登记最终播出集整季包："
            f"{title} S{season:02d}E{final_episode:02d} hash={download_hash}，"
            f"旧 qB 任务={len(old_tasks)}，已清理={cleanup_result['qb'].get('ok', 0)}，"
            f"MV3整理记录={cleanup_result['mv3'].get('ok', 0)}，"
            f"全选={'成功' if full_download.get('ok') else '失败'}"
        )

    @staticmethod
    def _object_identity(value: Any) -> Tuple[str, str]:
        """从媒体对象读取规范媒体来源和原生 ID。"""
        source, identity = normalize_identity(
            SubscribePlus._read_cleanup_value(value, "media_source"),
            SubscribePlus._read_cleanup_value(value, "media_id"),
        )
        if source and identity:
            return source, identity
        legacy = safe_int(SubscribePlus._read_cleanup_value(value, "tmdb_id", "tmdbid"), 0)
        return (DEFAULT_MEDIA_SOURCE, str(legacy)) if legacy else ("", "")


    def poll_season_pack_watches(self) -> Dict[str, Any]:
        """重试 DownloadAdded 后尚未成功删除的旧 qB 任务和源文件。"""
        config = getattr(self, "_plugin_config", PluginConfig.from_dict({}))
        qb_mode = normalize_qb_cleanup_mode(getattr(config, "season_pack_qb_cleanup", QB_CLEANUP_OFF))
        if (
            not config.enabled
            or not config.season_pack_enabled
            or qb_mode == QB_CLEANUP_OFF
        ):
            return {"success": True, "processed": 0, "pending": 0}
        processed = 0
        pending = 0
        for watch in self._ensure_store().load_season_pack_watches():
            old_tasks = watch.get("old_tasks") or []
            watch_mode = normalize_qb_cleanup_mode(watch.get("cleanup_mode") or qb_mode)
            result = self._process_old_qb_tasks(old_tasks, watch_mode)
            if result["pending_tasks"]:
                watch["old_tasks"] = result["pending_tasks"]
                self._ensure_store().save_season_pack_watch(watch)
                pending += 1
                continue
            self._ensure_store().delete_season_pack_watch(str(watch.get("download_hash") or ""))
            processed += 1
            logger.info(
                "订阅下载增强旧 qB 整季包清理重试成功："
                f"hash={watch.get('download_hash')}，qB任务={result['qb'].get('ok', 0)}，"
                f"MV3整理记录={result['mv3'].get('ok', 0)}"
            )
        return {"success": True, "processed": processed, "pending": pending}

    def _process_old_qb_tasks(self, tasks: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
        """逐任务幂等清理；source 模式由 qB 直接删除任务及其源文件。"""
        cleanup_mode = normalize_qb_cleanup_mode(mode)
        task_list = [dict(task) for task in tasks or [] if str(task.get("hash") or "").strip()]
        pending_tasks: List[Dict[str, Any]] = []
        delete_file = cleanup_mode == QB_CLEANUP_SOURCE
        qb_result = {"ok": 0, "failed": 0, "hashes": [], "failed_hashes": [], "delete_file": delete_file}
        mv3_result = {"ok": 0, "failed": 0, "paths": [], "failed_paths": [], "event_ids": []}

        for task in task_list:
            if cleanup_mode == QB_CLEANUP_SOURCE:
                # MV3 只补充查询整理记录，不参与删除决策；即使 MV3 不可达，
                # qB 仍按用户选择直接删除精确匹配的任务及源文件。
                source_result = self._query_mv3_old_sources([task])
                for key in ("paths", "failed_paths", "event_ids"):
                    mv3_result[key].extend(source_result.get(key) or [])
                mv3_result["ok"] += int(source_result.get("ok") or 0)
                mv3_result["failed"] += int(source_result.get("failed") or 0)

            if not task.get("qb_deleted"):
                one_qb = self._delete_old_qb_tasks([task], delete_file=delete_file)
                for key in ("hashes", "failed_hashes"):
                    qb_result[key].extend(one_qb.get(key) or [])
                qb_result["ok"] += int(one_qb.get("ok") or 0)
                qb_result["failed"] += int(one_qb.get("failed") or 0)
                qb_result["delete_file"] = bool(one_qb.get("delete_file"))
                if one_qb.get("failed"):
                    pending_tasks.append(task)
                    continue
                task["qb_deleted"] = True

        return {
            "pending_tasks": pending_tasks,
            "qb": qb_result,
            "mv3": mv3_result,
        }

    def _delete_old_qb_tasks(
        self,
        tasks: List[Dict[str, Any]],
        delete_file: bool = False,
    ) -> Dict[str, Any]:
        """按精确 hash 删除旧 qB 任务，可由 qB 同时删除其源文件。"""
        grouped: Dict[str, List[str]] = {}
        for task in tasks or []:
            task_hash = str(task.get("hash") or "").strip()
            if task_hash:
                grouped.setdefault(str(task.get("downloader") or ""), []).append(task_hash)
        ok, failed = [], []
        for downloader, hashes in grouped.items():
            try:
                client, _ = self._get_qb_client(downloader)
                if client and client.delete_torrents(delete_file=delete_file, ids=hashes):
                    ok.extend(hashes)
                else:
                    failed.extend(hashes)
            except Exception as exc:
                failed.extend(hashes)
                logger.warning(f"订阅下载增强删除旧 qB 任务失败：{downloader}，{exc}")
        return {
            "ok": len(ok),
            "failed": len(failed),
            "hashes": ok,
            "failed_hashes": failed,
            "delete_file": delete_file,
        }

    @staticmethod
    def _normalize_fs_path(value: Any) -> str:
        """规范化路径，仅用于 MV3 事件的完整路径精确比较。"""
        text = str(value or "").strip().replace("\\", "/")
        return re.sub(r"/+", "/", text).rstrip("/")

    def _mv3_base_url(self, value: Optional[str] = None) -> str:
        """返回 MV3 API 根地址；配置填写网站地址，不包含 /api/v1。"""
        base = str(
            value if value is not None else getattr(self._plugin_config, "mv3_url", "")
            or ""
        ).strip().rstrip("/")
        if base.endswith("/api/v1"):
            base = base[:-7].rstrip("/")
        return f"{base}/api/v1" if base else ""

    def _mv3_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Optional[Any]:
        """使用 MV3 X-API-Key 调用只读整理记录接口。"""
        base = base_url or self._mv3_base_url()
        api_token = str(
            token if token is not None else getattr(self._plugin_config, "mv3_api_token", "")
            or ""
        ).strip()
        if not base or not api_token:
            logger.info("订阅下载增强未配置 MV3 网站地址或 API Token，跳过整理记录补充查询")
            return None
        try:
            from app.sdk.network import RequestUtils

            headers = {"X-API-Key": api_token, "Accept": "application/json"}
            request = RequestUtils(
                headers=headers,
                timeout=20,
                verify=base.lower().startswith("https://"),
            )
            url = f"{base}/{str(path).lstrip('/')}"
            if method.upper() != "GET":
                raise ValueError(f"unsupported read-only MV3 method: {method}")
            response = request.get_res(url, params=params or {})
            if response is None or not 200 <= int(response.status_code) < 300:
                logger.warning(f"订阅下载增强 MV3 请求失败：{method} {path} status={getattr(response, 'status_code', None)}")
                return None
            if not response.content:
                return {"_http_success": True}
            return response.json()
        except Exception as exc:
            logger.warning(f"订阅下载增强 MV3 请求异常：{method} {path}，{exc}")
            return None

    @staticmethod
    def _mv3_items(payload: Any) -> List[Dict[str, Any]]:
        """兼容 MV3 API 外层 data 与分页 items/results 包装。"""
        value = payload
        if isinstance(value, dict):
            value = value.get("data", value)
        if isinstance(value, dict):
            value = value.get("items") or value.get("results") or value.get("records") or value.get("data") or []
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _mv3_total(payload: Any) -> Optional[int]:
        """读取 MV3 已知分页响应中的 total。"""
        value = payload
        if isinstance(value, dict):
            value = value.get("data", value)
        if not isinstance(value, dict):
            return None
        total = value.get("total")
        try:
            return max(0, int(total)) if total is not None else None
        except (TypeError, ValueError):
            return None

    def _mv3_events_for_path(self, path: str) -> List[Dict[str, Any]]:
        """按源文件名分页查询 MV3 事件，随后由调用方严格比较完整路径。"""
        keyword = Path(str(path)).name
        if not keyword:
            return []
        result: List[Dict[str, Any]] = []
        for page in range(1, 101):
            payload = self._mv3_request(
                "GET",
                "monitor/events",
                params={"page": page, "page_size": 100, "keyword": keyword, "status": "processed"},
            )
            items = self._mv3_items(payload)
            if not items:
                break
            result.extend(items)
            total = self._mv3_total(payload)
            if total is not None and len(result) >= total:
                break
            if total is None and len(items) < 100:
                break
        return result

    def _mv3_path_is_processed(self, path: str) -> bool:
        """确认路径对应的 MV3 整理事件状态为 processed。"""
        normalized = self._normalize_fs_path(path)
        return any(
            self._normalize_fs_path(item.get("file_path") or item.get("path")) == normalized
            and str(item.get("status") or "").lower() == "processed"
            for item in self._mv3_events_for_path(path)
        )

    def _query_mv3_old_sources(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按精确源路径查询 MV3 整理记录，但不通过 MV3 删除任何文件或事件。"""
        result = {"ok": 0, "failed": 0, "paths": [], "failed_paths": [], "event_ids": []}
        for task in tasks or []:
            source_paths = list(dict.fromkeys(task.get("source_paths") or []))
            if not source_paths:
                result["failed"] += 1
                result["failed_paths"].append(f"task:{task.get('hash') or 'unknown'}")
                logger.warning(
                    "订阅下载增强旧 qB 任务没有可补充查询的源路径："
                    f"{task.get('hash') or '-'}"
                )
                continue
            for path in source_paths:
                normalized = self._normalize_fs_path(path)
                matched = [
                    item for item in self._mv3_events_for_path(path)
                    if self._normalize_fs_path(item.get("file_path") or item.get("path")) == normalized
                    and str(item.get("status") or "").lower() == "processed"
                ]
                matched_ids = list(dict.fromkeys(
                    item.get("id") or item.get("event_id")
                    for item in matched
                    if item.get("id") or item.get("event_id")
                ))
                if len(matched_ids) != 1:
                    result["failed"] += 1
                    result["failed_paths"].append(path)
                    logger.warning(
                        "订阅下载增强 MV3 processed 精确事件不是唯一一条，仅记录查询结果，qB 仍按配置处理："
                        f"{path}，匹配={len(matched_ids)}"
                    )
                    continue
                event_id = matched_ids[0]
                result["ok"] += 1
                result["paths"].append(path)
                result["event_ids"].append(event_id)
        return result

    def _ensure_season_pack_full_download(self, current, event_data: Dict[str, Any]) -> Dict[str, Any]:
        download_hash = self._resolve_cleanup_download_hash(current, event_data)
        if not download_hash:
            return {"ok": False, "reason": "missing download hash", "file_count": 0}

        downloader = self._resolve_cleanup_downloader_name(current, event_data)
        try:
            from app.sdk.services import DownloaderHelper

            helper = DownloaderHelper()
            if downloader:
                service = helper.get_service(name=downloader, type_filter="qbittorrent")
            else:
                services = helper.get_services(type_filter="qbittorrent")
                service = next(iter(services.values()), None) if services else None
            qbittorrent = getattr(service, "instance", None) or service
            if not qbittorrent or not hasattr(qbittorrent, "get_files"):
                return {
                    "ok": False,
                    "reason": "qBittorrent downloader not found",
                    "file_count": 0,
                    "downloader": downloader,
                }

            files = list(qbittorrent.get_files(download_hash) or [])
            if len(files) <= 1:
                logger.info(
                    f"订阅下载增强跳过整季包全包下载：单文件种子非整季包，hash={download_hash}，files={len(files)}"
                )
                return {
                    "ok": False,
                    "reason": "single-file torrent, skip full download",
                    "file_count": len(files),
                    "downloader": downloader,
                    "hash": download_hash,
                }
            file_ids = []
            for position, fileitem in enumerate(files):
                file_index = self._torrent_file_index(fileitem, position)
                if file_index is not None:
                    file_ids.append(str(file_index))
            if not file_ids:
                return {
                    "ok": False,
                    "reason": "torrent files not found",
                    "file_count": 0,
                    "downloader": downloader,
                    "hash": download_hash,
                }

            joined_file_ids = "|".join(file_ids)
            if not qbittorrent.set_files(torrent_hash=download_hash, file_ids=joined_file_ids, priority=1):
                return {
                    "ok": False,
                    "reason": "set file priority failed",
                    "file_count": len(file_ids),
                    "downloader": downloader,
                    "hash": download_hash,
                }
            qbittorrent.start_torrents(download_hash)
            logger.info(
                f"订阅下载增强已将整季包 qB 文件全部设为下载：hash={download_hash}，files={len(file_ids)}"
            )
            return {
                "ok": True,
                "reason": "selected all files",
                "file_count": len(file_ids),
                "downloader": downloader,
                "hash": download_hash,
            }
        except Exception as exc:
            logger.warning(f"订阅下载增强设置整季包 qB 全包下载失败：hash={download_hash}，{exc}")
            return {
                "ok": False,
                "reason": str(exc),
                "file_count": 0,
                "downloader": downloader,
                "hash": download_hash,
            }

    @staticmethod
    def _resolve_cleanup_download_hash(current, event_data: Dict[str, Any]) -> str:
        return str(
            getattr(current, "download_hash", "")
            or event_data.get("download_hash")
            or event_data.get("hash")
            or ""
        )

    @classmethod
    def _resolve_cleanup_downloader_name(cls, current, event_data: Dict[str, Any]) -> str:
        sources = [event_data, current]
        for key in ("download", "download_info", "torrent", "torrent_info", "transferinfo"):
            value = event_data.get(key)
            if value:
                sources.append(value)
        for source in sources:
            value = cls._read_cleanup_value(source, "downloader", "downloader_name", "download_source")
            if value:
                return str(value)
        return ""

    @staticmethod
    def _read_cleanup_value(source, *names: str):
        for name in names:
            if isinstance(source, dict):
                value = source.get(name)
            else:
                value = getattr(source, name, None)
            if value:
                return value
        return None

    @classmethod
    def _torrent_file_index(cls, fileitem, fallback: int) -> int:
        value = cls._read_cleanup_value(fileitem, "index", "id")
        if value is None:
            return fallback
        return safe_int(value, fallback)

    def _handle_sp_command_text(self, text: str, event_data: Dict[str, Any]):
        store = self._ensure_store()
        items = []
        for item in self._prune_downloaded_scan_results():
            ignore_key = self._ignore_key(item)
            # JsonStore 没有 is_ignored（旧「永久忽略」语义已改为限期通知抑制），
            # 这里与通知队列、诊断推送两处保持一致，统一按抑制期判断。
            if store.is_notification_suppressed(ignore_key):
                continue
            items.append(item)

        if not items:
            self._post_callback_message(
                event_data,
                title="订阅下载增强",
                text="当前没有待处理诊断结果。",
                save_history=False,
            )
            return

        menu_items = []
        lines = [f"当前待处理诊断：{len(items)} 部"]
        for item in items[:20]:
            token = self._save_interaction(item)
            menu_items.append((token, item))
            episodes = item.get("episodes") or []
            episode_text = "/".join(
                f"E{safe_int(episode.get('episode'), 0):02d}"
                for episode in episodes[:3]
                if safe_int(episode.get("episode"), 0)
            )
            season = safe_int(item.get("season"), 0)
            suffix = f" S{season:02d} {episode_text}" if season or episode_text else ""
            lines.append(f"- {item.get('title') or '未命名'}{suffix}")
        if len(items) > 20:
            lines.append(f"... 还有 {len(items) - 20} 部未列出")

        self._post_callback_message(
            event_data,
            title="订阅下载增强待处理诊断",
            text="\n".join(lines),
            buttons=build_pending_menu(menu_items),
            save_history=False,
        )

    def _handle_sprule_command_text(self, text: str, event_data: Dict[str, Any]):
        """处理 Telegram 的 `/sprule` 词表和自定义识别词命令。"""
        raw = str(text or "").strip()
        if raw.startswith("/sprule"):
            raw = raw[len("/sprule"):].strip()
        parts = raw.split(maxsplit=2)
        if len(parts) < 2:
            self._post_callback_message(
                event_data,
                title="SubscribePlus 规则词表",
                text=(
                    "用法：\n"
                    "/sprule TOKEN add-group 关键词\n"
                    "/sprule TOKEN del-group 关键词\n"
                    "/sprule TOKEN add-platform 关键词\n"
                    "/sprule TOKEN del-platform 关键词\n"
                    "/sprule TOKEN add 识别词规则\n"
                    "/sprule TOKEN del 识别词规则"
                ),
                save_history=False,
            )
            return

        token = str(parts[0] or "").strip()
        operation = str(parts[1] or "").strip().lower()
        value = str(parts[2] if len(parts) > 2 else "").strip()
        state = self._ensure_store().load_interaction(token)
        if not state:
            self._post_callback_message(
                event_data,
                title="SubscribePlus 规则词表",
                text="交互 token 无效或已过期，请从最新诊断通知中重新打开菜单。",
                save_history=False,
            )
            return
        if not self._plugin_config.allow_tg_rule_update:
            self._post_callback_message(
                event_data,
                title="SubscribePlus 规则词表",
                text="Telegram 修改订阅规则功能未授权，请先在插件配置中开启。",
                save_history=False,
            )
            return
        if not value:
            self._post_callback_message(
                event_data,
                title="SubscribePlus 规则词表",
                text="关键词或识别词规则不能为空，请重新发送完整命令。",
                save_history=False,
            )
            return

        if operation in {"add", "del", "delete"}:
            result = (
                self._add_custom_identifier_values(value)
                if operation == "add"
                else self._delete_custom_identifier_values(value)
            )
            identifiers = self._load_custom_identifiers()
            self._post_callback_message(
                event_data,
                title="自定义识别词",
                text=result.get("message") or "自定义识别词操作完成。",
                buttons=build_rule_custom_menu(token, len(identifiers)),
                save_history=False,
            )
            return

        operation_aliases = {
            "add-group": ("group", True),
            "del-group": ("group", False),
            "delete-group": ("group", False),
            "add-platform": ("platform", True),
            "del-platform": ("platform", False),
            "delete-platform": ("platform", False),
        }
        target = operation_aliases.get(operation)
        if not target:
            self._post_callback_message(
                event_data,
                title="SubscribePlus 规则词表",
                text="未知操作，请使用 add-group、del-group、add-platform、del-platform、add 或 del。",
                save_history=False,
            )
            return

        kind, adding = target
        groups, platforms = self._load_rule_dictionary()
        values = groups if kind == "group" else platforms
        normalized = self._normalize_dictionary_values(value)
        if not normalized:
            self._post_callback_message(
                event_data,
                title="SubscribePlus 规则词表",
                text="关键词无效：不能为空且长度不能超过 80 个字符。",
                buttons=build_rule_dictionary_menu(token, len(groups), len(platforms)),
                save_history=False,
            )
            return
        changed = []
        if adding:
            existing = {item.casefold() for item in values}
            for item in normalized:
                if item.casefold() not in existing:
                    values.append(item)
                    existing.add(item.casefold())
                    changed.append(item)
            label = "官组" if kind == "group" else "平台"
            message = f"已新增{label}：{', '.join(changed) or '均已存在'}"
        else:
            targets = {item.casefold() for item in normalized}
            kept = [item for item in values if item.casefold() not in targets]
            changed = [item for item in values if item.casefold() in targets]
            values[:] = kept
            label = "官组" if kind == "group" else "平台"
            message = f"已删除{label}：{', '.join(changed) or '未找到'}"
        self._save_rule_dictionary(groups, platforms)
        self._post_callback_message(
            event_data,
            title="自定义官组/平台",
            text=message + "\n已同步到网页规则建议和 Telegram 菜单。",
            buttons=build_rule_dictionary_menu(token, len(groups), len(platforms)),
            save_history=False,
        )

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

    def _save_interaction(self, diagnosis: Dict[str, Any], summary_token: str = "") -> str:
        """保存单条诊断交互，可选记录返回的扫描汇总 token。

        :param diagnosis: 单条诊断项
        :param summary_token: 来源扫描汇总 token
        :return: 单条详情交互 token
        """
        token = make_token(
            {
                "subscribe_id": diagnosis.get("subscribe_id"),
                "tmdbid": diagnosis.get("tmdbid"),
                "media_source": diagnosis.get("media_source"),
                "media_id": diagnosis.get("media_id"),
                "season": diagnosis.get("season"),
                "created_at": diagnosis.get("created_at"),
                "summary_token": summary_token,
            }
        )
        state = {
            "view": "main",
            "diagnosis": diagnosis,
            "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds"),
        }
        if summary_token:
            state["summary_token"] = summary_token
        self._ensure_store().save_interaction(
            token,
            state,
        )
        return token

    def _save_scan_summary(self, items: List[Dict[str, Any]]) -> str:
        """保存一次扫描的汇总状态并返回汇总 token。

        :param items: 扫描诊断项列表
        :return: 汇总交互 token
        """
        created_at = datetime.now().isoformat(timespec="microseconds")
        token = make_token(
            {
                "view": "scan_summary",
                "created_at": created_at,
                "items": [
                    {
                        "subscribe_id": item.get("subscribe_id"),
                        "season": item.get("season"),
                        "created_at": item.get("created_at"),
                    }
                    for item in items
                ],
            }
        )
        self._ensure_store().save_interaction(
            token,
            {
                "view": "scan_summary",
                "items": items,
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds"),
            },
        )
        return token

    @staticmethod
    def _ignore_key(item: Dict[str, Any]) -> str:
        episodes = ",".join(str(episode.get("episode")) for episode in item.get("episodes") or [])
        return f"{item.get('subscribe_id')}:{item.get('season')}:{episodes}"

    def _refresh_scan_result_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """按当前媒体库/整理历史复核单条诊断结果，剔除已入库的集。

        返回值：仍有缺集时返回更新后的诊断项；全部已入库时返回 None。
        """
        tmdbid = safe_int(item.get("tmdbid"), 0)
        media_source, media_id = normalize_identity(
            item.get("media_source"), item.get("media_id")
        )
        if not media_id and tmdbid:
            # 旧快照只保存了 tmdbid，按 TMDB 来源回放。
            media_source, media_id = DEFAULT_MEDIA_SOURCE, str(tmdbid)
        season = safe_int(item.get("season"), 0)
        episodes = item.get("episodes") or []
        if not media_id or not season or not episodes:
            return item
        try:
            downloaded = self._load_downloaded_episodes(media_source, media_id, season)
        except Exception as exc:
            logger.warning(f"订阅下载增强复核已入库集失败: {exc}")
            return item
        if not downloaded:
            return item
        remaining = [ep for ep in episodes if safe_int(ep.get("episode"), 0) not in downloaded]
        if not remaining:
            return None
        if len(remaining) == len(episodes):
            return item
        updated = dict(item)
        updated["episodes"] = remaining
        return updated

    def _prune_downloaded_scan_results(self) -> List[Dict[str, Any]]:
        """遍历诊断快照，剔除已入库的集与已完成的诊断项，并回写存储。"""
        store = self._ensure_store()
        results = store.load_scan_results()
        if not results:
            return results
        refreshed: List[Dict[str, Any]] = []
        changed = False
        for item in results:
            updated = self._refresh_scan_result_item(item)
            if updated is None:
                changed = True
                continue
            if updated is not item:
                changed = True
            refreshed.append(updated)
        if changed:
            store.replace_scan_results(refreshed)
        return refreshed

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

        oper = SubscribeOper()
        subscribe = oper.update(subscribe_id, payload)
        current = oper.get(subscribe_id) if subscribe else None
        confirmed = bool(subscribe and current)
        if confirmed:
            for key, expected in payload.items():
                actual = getattr(current, key, None)
                if key == "sites":
                    actual = [int(item) for item in (actual or [])]
                    expected = [int(item) for item in (expected or [])]
                elif isinstance(expected, str):
                    actual = str(actual or "")
                    expected = str(expected or "")
                if actual != expected:
                    confirmed = False
                    break
        return {"id": subscribe_id, "updated": confirmed}

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
        groups.extend(self._load_rule_dictionary()[0])
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
                from app.sdk.network import SitesHelper

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
        """读取宿主分类策略中启用的电视剧二级分类。

        优先读取 MoviePilot V3 分类策略（systemconfig MediaClassificationPolicy
        的 active.categories，media_type=电视剧 且 enabled），兼容旧版
        MediaChain().media_category() 以支持旧宿主回退。
        """
        categories: List[str] = []
        try:
            from app.db.systemconfig_oper import SystemConfigOper

            key = getattr(SystemConfigKey, "MediaClassificationPolicy", None)
            if key is not None:
                policy = SystemConfigOper().get(key) or {}
                active = policy.get("active") or {}
                raw_categories = active.get("categories") or []
                categories = [
                    str(item.get("name") or "").strip()
                    for item in raw_categories
                    if isinstance(item, dict)
                    and str(item.get("media_type") or "").strip() == MediaType.TV.value
                    and item.get("enabled", True) is not False
                    and str(item.get("name") or "").strip()
                ]
        except Exception:
            categories = []
        if categories:
            return categories
        try:
            try:
                from app.chain.media import MediaChain
            except Exception:
                from app.chain import MediaChain

            raw_categories = (MediaChain().media_category() or {}).get(MediaType.TV.value) or []
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
        media_source, media_id = subscribe_identity(subscribe)
        parts = [title]
        if subscribe_id:
            parts.append(f"ID={subscribe_id}")
        if media_id:
            parts.append(f"{media_source or DEFAULT_MEDIA_SOURCE}:{media_id}")
        return " ".join(parts)

    def _resolve_subscribe_category(self, subscribe: Any) -> Optional[str]:
        """按订阅的规范媒体身份解析媒体库二级分类。

        V3 起订阅主身份为 media_source + media_id，tmdbid 只作为旧宿主兼容
        回落；分类读取优先 library_category（V3 规范字段），并兼容 category。
        """
        media_source, media_id = subscribe_identity(subscribe)
        if not media_id:
            return None
        subscribe_label = self._describe_subscribe(subscribe)
        episode_group = getattr(subscribe, "episode_group", None) or ""
        cache_key = f"{media_source}:{media_id}:{episode_group}"
        if cache_key in self._category_cache:
            return self._category_cache[cache_key]
        try:
            try:
                from app.chain.media import MediaChain
                from app.schemas.media import normalize_media_source
            except Exception:
                from app.chain import MediaChain
                from app.schemas.media import normalize_media_source

            source = normalize_media_source(media_source)
            if not source:
                logger.warning(f"订阅下载增强识别订阅分类失败（未知媒体来源）{subscribe_label}")
                return None
            mediainfo = MediaChain().recognize_media(
                mtype=MediaType.TV,
                media_source=source,
                media_id=str(media_id),
                episode_group=episode_group or None,
            )
            category = str(
                getattr(mediainfo, "library_category", "")
                or getattr(mediainfo, "category", "")
                or ""
            ).strip()
            if category:
                self._category_cache[cache_key] = category
                return category
            logger.warning(f"订阅下载增强识别订阅分类未命中 {subscribe_label}")
        except Exception as exc:
            logger.warning(f"订阅下载增强识别订阅分类失败 {subscribe_label}: {exc}")
        return None

    @staticmethod
    def _tmdb_cache_is_fresh(cached: Optional[Dict[str, Any]], cache_hours: int = TMDB_CACHE_TTL_HOURS) -> bool:
        """判断插件保存的 TMDB 季集日历是否仍在配置的缓存期限内。"""
        if not isinstance(cached, dict) or cache_hours <= 0:
            return False
        updated_at = cached.get("updated_at")
        if not updated_at:
            return False
        try:
            return datetime.fromisoformat(str(updated_at)) >= datetime.now() - timedelta(hours=cache_hours)
        except (TypeError, ValueError):
            return False

    def _load_episodes(
        self,
        media_source: str,
        media_id: str,
        season: int,
        episode_group: Optional[str],
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """读取某季日历，按缓存期限自动更新，手动扫描可强制刷新。

        只有 TMDB 来源有独立的分集日历接口；Bangumi、AniList 等来源改用
        统一识别结果中的季集清单，避免把非 TMDB 的媒体 ID 当作 TMDB ID 使用。
        """
        cache_key = f"{media_source}:{media_id}:{season}:{episode_group or ''}"
        cached = self._ensure_store().load_tmdb_cache(cache_key)
        cached_episodes = cached.get("episodes") if isinstance(cached, dict) else None
        if (
            not force_refresh
            and isinstance(cached_episodes, list)
            and self._tmdb_cache_is_fresh(cached)
        ):
            return cached["episodes"]
        try:
            normalized = self._fetch_episodes(media_source, media_id, season, episode_group)
            if not normalized:
                # 空日历通常是数据源暂无数据，保留旧缓存避免扫描结果整体消失。
                return cached_episodes if isinstance(cached_episodes, list) else []
            self._ensure_store().save_tmdb_cache(
                cache_key,
                {"episodes": normalized, "updated_at": datetime.now().isoformat(timespec="seconds")},
            )
            return normalized
        except Exception as exc:
            logger.warning(
                f"订阅下载增强读取剧集日历失败 {media_source}:{media_id} S{season}: {exc}"
            )
            # TMDB 临时不可用时保留旧日历，避免一次网络故障让扫描结果整体消失。
            if isinstance(cached_episodes, list):
                return cached_episodes
            return []


    def _fetch_episodes(
        self,
        media_source: str,
        media_id: str,
        season: int,
        episode_group: Optional[str],
    ) -> List[Dict[str, Any]]:
        """按媒体来源获取某季的分集与播出日期。"""
        if str(media_source or "").strip().lower() in TMDB_SOURCE_VALUES and str(media_id).strip().isdigit():
            from app.chain.tmdb import TmdbChain

            episodes = TmdbChain().tmdb_episodes(
                tmdbid=int(media_id),
                season=season,
                episode_group=episode_group,
            ) or []
            return [
                {
                    "episode_number": getattr(episode, "episode_number", None)
                    or getattr(episode, "episode", None),
                    "air_date": str(getattr(episode, "air_date", "") or ""),
                }
                for episode in episodes
            ]
        return self._fetch_source_episodes(media_source, media_id, season, episode_group)

    def _fetch_source_episodes(
        self,
        media_source: str,
        media_id: str,
        season: int,
        episode_group: Optional[str],
    ) -> List[Dict[str, Any]]:
        """从非 TMDB 来源的识别结果推导季集清单。

        这类来源没有分集播出日历，只能按季整体判断：使用分集自带的播出
        日期，缺失时回落该季的发行日期；连季级日期都拿不到时返回空日历，
        避免把尚未播出的集误判为已播出。
        """
        try:
            from app.chain.media import MediaChain
            from app.schemas.media import normalize_media_source
        except Exception:
            from app.chain import MediaChain
            from app.schemas.media import normalize_media_source

        source = normalize_media_source(media_source)
        if not source:
            return []
        mediainfo = MediaChain().recognize_media(
            mtype=MediaType.TV,
            media_source=source,
            media_id=str(media_id),
            episode_group=episode_group or None,
        )
        if not mediainfo:
            return []
        episode_numbers = sorted(
            int(number)
            for number in ((getattr(mediainfo, "seasons", None) or {}).get(season) or [])
            if str(number).isdigit() and int(number) > 0
        )
        if not episode_numbers:
            return []
        season_air_date = str(
            getattr(mediainfo, "release_date", "") or getattr(mediainfo, "first_air_date", "") or ""
        )
        if not season_air_date:
            logger.info(
                "订阅下载增强：非 TMDB 来源缺少季播出日期，跳过日历构建 "
                f"{media_source}:{media_id} S{season}"
            )
            return []
        return [
            {"episode_number": number, "air_date": season_air_date}
            for number in episode_numbers
        ]

    @staticmethod
    def _season_labels(season: int) -> List[str]:
        value = safe_int(season, 0)
        if not value:
            return []
        return list(dict.fromkeys([f"S{value:02d}", f"S{value}"]))

    @staticmethod
    def _history_status_ok(history: Any) -> bool:
        return getattr(history, "status", True) is not False

    @staticmethod
    def _history_identity(history: Any) -> str:
        return str(getattr(history, "id", None) or getattr(history, "dest", None) or id(history))

    def _load_transfer_history_dicts(
        self,
        media_source: str,
        media_id: str,
        season: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """按规范媒体身份读取整理历史，供已入库集判定使用。"""
        from app.db.transferhistory_oper import TransferHistoryOper
        from app.schemas.media import normalize_media_source

        oper = TransferHistoryOper()
        source = normalize_media_source(media_source)
        identity = str(media_id or "").strip()
        if not source or not identity:
            return []
        histories = []
        seen = set()

        def add(items: List[Any]):
            for history in items or []:
                if not self._history_status_ok(history):
                    continue
                key = self._history_identity(history)
                if key in seen:
                    continue
                seen.add(key)
                histories.append(history)

        if season:
            for label in self._season_labels(season):
                add(oper.get_by(
                    media_source=source,
                    media_id=identity,
                    mtype=MediaType.TV.value,
                    season=label,
                ) or [])
        if not histories:
            add(oper.get_by(
                media_source=source,
                media_id=identity,
                mtype=MediaType.TV.value,
            ) or [])

        return [
            {
                "media_source": str(getattr(history, "media_source", "") or ""),
                "media_id": str(getattr(history, "media_id", "") or ""),
                "season": getattr(history, "seasons", None),
                "episodes": getattr(history, "episodes", None),
            }
            for history in histories
        ]

    def _is_episode_downloaded(
        self,
        media_source: str,
        media_id: str,
        season: int,
        episode: int,
    ) -> tuple[bool, str]:
        try:
            item = self._load_mediaserver_item(media_source, media_id)
            seasoninfo = getattr(item, "seasoninfo", None) if item else None
            if episode_in_seasoninfo(seasoninfo, season, episode):
                return True, "媒体库缓存已命中"
        except Exception as exc:
            logger.warning(f"订阅下载增强查询媒体库缓存失败: {exc}")

        try:
            history_dicts = self._load_transfer_history_dicts(media_source, media_id, season)
            if episode_in_transfer_history(history_dicts, media_source, media_id, season, episode):
                return True, "整理历史已命中"
        except Exception as exc:
            logger.warning(f"订阅下载增强查询整理历史失败: {exc}")

        return False, "媒体库缓存和整理历史均未命中"

    def _load_downloaded_episodes(self, media_source: str, media_id: str, season: int) -> set[int]:
        episodes: set[int] = set()
        try:
            item = self._load_mediaserver_item(media_source, media_id)
            if item:
                episodes.update(episodes_in_seasoninfo(getattr(item, "seasoninfo", None), season))
        except Exception as exc:
            logger.warning(f"订阅下载增强读取媒体库已下载集失败: {exc}")

        try:
            history_dicts = self._load_transfer_history_dicts(media_source, media_id, season)
            episodes.update(
                episodes_in_transfer_history(history_dicts, media_source, media_id, season)
            )
        except Exception as exc:
            logger.warning(f"订阅下载增强读取整理历史已下载集失败: {exc}")

        return {episode for episode in episodes if episode > 0}

    def _load_mediaserver_item(self, media_source: str, media_id: str) -> Any:
        """按规范媒体身份读取媒体库缓存条目。

        V3 的 MediaServerOper.exists 只认 media_source/media_id 或 title，
        旧的 tmdbid 参数会静默返回 None，因此这里统一使用规范身份。
        """
        from app.db.mediaserver_oper import MediaServerOper
        from app.schemas.media import normalize_media_source

        source = normalize_media_source(media_source)
        identity = str(media_id or "").strip()
        if not source or not identity:
            return None
        return MediaServerOper().exists(
            media_source=source,
            media_id=identity,
            mtype=MediaType.TV.value,
        )

    @staticmethod
    def _item_identity(item: Any) -> Tuple[str, str]:
        """读取诊断项的规范媒体身份，缺字段时回落其 TMDB 兼容字段。"""
        source, identity = normalize_identity(
            getattr(item, "media_source", None),
            getattr(item, "media_id", None),
        )
        if source and identity:
            return source, identity
        legacy = safe_int(getattr(item, "tmdbid", 0), 0)
        if legacy:
            return DEFAULT_MEDIA_SOURCE, str(legacy)
        return "", ""

    @staticmethod
    def _context_matches_item(media_info: Any, media_source: str, media_id: str) -> bool:
        """判断搜索上下文识别出的媒体是否就是目标媒体。"""
        if not media_info or not media_id:
            return False
        try:
            from app.schemas.media import normalize_media_source, resolve_media_identity
        except Exception:
            return False
        source, identity = resolve_media_identity(media=media_info)
        if source and identity:
            return str(source) == str(media_source or "").strip().lower() and identity == str(media_id)
        # 兼容识别结果只回填 tmdb_id 的场景。
        if str(media_source or "").strip().lower() in TMDB_SOURCE_VALUES:
            return str(safe_int(getattr(media_info, "tmdb_id", None), 0) or "") == str(media_id)
        return False

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
            from app.schemas.media import normalize_media_source

            search_sites = item.sites if sites is None else sites
            site_ids = [int(site_id) for site_id in search_sites if str(site_id).isdigit()]
            source, identity = self._item_identity(item)
            media_source = normalize_media_source(source)
            if not media_source or not identity:
                logger.warning(
                    f"订阅下载增强搜索 PT 资源失败：缺少规范媒体身份 {self._format_item_log_context(item)}"
                )
                return []
            coro = SearchChain().async_search_by_id(
                media_source=media_source,
                media_id=identity,
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
                    or self._context_matches_item(media_info, source, identity)
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
        source, identity = self._item_identity(item)
        recognized = bool(
            getattr(context, "candidate_recognized", False)
            or getattr(context, "media_info_is_target", False)
            or self._context_matches_item(media_info, source, identity)
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
        source, identity = self._item_identity(item)
        raw = (
            f"{item.subscribe_id}:{source}:{identity}:{item.season}:{title}:"
            f"{len(self._download_contexts)}"
        )
        candidate_id = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        self._download_contexts[candidate_id] = context
        if len(self._download_contexts) > 300:
            for old_key in list(self._download_contexts.keys())[:100]:
                self._download_contexts.pop(old_key, None)
        # 持久化候选下载所需的最小字段，供内存上下文丢失后重建下载
        try:
            self._save_candidate_download_cache(candidate_id, context, item, title)
        except Exception as exc:
            logger.warning(f"订阅下载增强缓存候选下载信息失败: {exc}")
        return candidate_id

    def _save_candidate_download_cache(self, candidate_id: str, context: Any, item: DiagnosisInput, title: str):
        config = getattr(self, "_plugin_config", None)
        cache_days = int(getattr(config, "candidate_cache_days", 3) or 0)
        if cache_days <= 0:
            return
        torrent = getattr(context, "torrent_info", context)
        meta_info = getattr(context, "meta_info", None)
        media_source, media_id = self._item_identity(item)
        payload = {
            "candidate_id": candidate_id,
            "subscribe_id": int(getattr(item, "subscribe_id", 0) or 0),
            "tmdbid": int(getattr(item, "tmdbid", 0) or 0),
            "media_source": media_source,
            "media_id": media_id,
            "season": int(getattr(item, "season", 0) or 0),
            "title": title or getattr(torrent, "title", "") or "",
            "site": getattr(torrent, "site", None),
            "site_name": getattr(torrent, "site_name", None),
            "enclosure": getattr(torrent, "enclosure", "") or "",
            "page_url": getattr(torrent, "page_url", "") or "",
            "size": getattr(torrent, "size", "") or "",
            "seeders": getattr(torrent, "seeders", 0),
            "pubdate": getattr(torrent, "pubdate", "") or "",
            "description": getattr(torrent, "description", "") or "",
            "imdbid": getattr(torrent, "imdbid", "") or "",
            "episodes": list(getattr(meta_info, "episode_list", None) or []),
            "cached_at": datetime.now().isoformat(timespec="seconds"),
            "expires_at": (datetime.now() + timedelta(days=cache_days)).isoformat(timespec="seconds"),
        }
        if not payload["enclosure"]:
            # 没有种子直链无法重建下载，跳过缓存
            return
        self._ensure_store().save_candidate_cache(candidate_id, payload)

    def _rebuild_context_from_cache(self, cached: Dict[str, Any]) -> Any:
        """用缓存的最小字段重建下载 Context。"""
        from app.sdk.media import Context, TorrentInfo
        from app.sdk.media import MetaInfo

        title = str(cached.get("title") or "")
        if not cached.get("enclosure"):
            return None
        torrent = TorrentInfo()
        torrent.title = title
        torrent.enclosure = cached.get("enclosure") or ""
        torrent.page_url = cached.get("page_url") or ""
        torrent.site = cached.get("site")
        torrent.site_name = cached.get("site_name")
        torrent.size = cached.get("size") or 0
        torrent.seeders = cached.get("seeders") or 0
        torrent.pubdate = cached.get("pubdate") or ""
        torrent.description = cached.get("description") or ""
        try:
            torrent.imdbid = cached.get("imdbid") or ""
        except Exception:
            pass
        meta = MetaInfo(title)
        media = None
        try:
            media_source, media_id = normalize_identity(
                cached.get("media_source"), cached.get("media_id")
            )
            if not media_id and cached.get("tmdbid"):
                # 旧缓存只有 tmdbid，按 TMDB 来源回放。
                media_source, media_id = DEFAULT_MEDIA_SOURCE, str(int(cached.get("tmdbid")))
            if media_id:
                from app.schemas.media import normalize_media_source
                from app.schemas.types import MediaType

                try:
                    from app.chain.media import MediaChain
                except Exception:
                    from app.chain import MediaChain
                source = normalize_media_source(media_source)
                if source:
                    media = MediaChain().recognize_media(
                        meta=meta,
                        media_source=source,
                        media_id=str(media_id),
                        mtype=MediaType.TV,
                        cache=True,
                    )
        except Exception as exc:
            logger.warning(f"订阅下载增强重建候选媒体信息失败，将按种子信息下载: {exc}")
        context = Context(meta_info=meta, media_info=media, torrent_info=torrent)
        return context

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
                self._load_episodes,
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
