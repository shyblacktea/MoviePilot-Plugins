"""完整的 F4 通知目标面板插件。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    from fastapi import Body
except Exception:  # pragma: no cover
    def Body(default=None, **kwargs):
        """提供无 FastAPI 测试环境的 Body 兼容函数。"""
        return default

from app.plugins import _PluginBase
from app.schemas.types import SystemConfigKey


class NotifyToGroupShy(_PluginBase):
    """独立承载完整 F4 通知目标面板。"""

    plugin_name = "我就想通知到群组！"
    plugin_desc = "管理资源入库、资源下载、添加订阅/订阅完成及订阅用户通知目标。"
    plugin_icon = "notifytogroupshy.png"
    plugin_version = "0.0.1"
    plugin_author = "shyblacktea"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "notifytogroupshy_"
    plugin_order = 999
    auth_level = 1

    _action_options = [
        {"title": "发群组", "value": "all"},
        {"title": "用户+管理员", "value": "user,admin"},
        {"title": "仅用户", "value": "user"},
        {"title": "仅管理员", "value": "admin"},
    ]
    _scene_types = {
        "download_action": "资源下载",
        "organize_action": "整理入库",
        "subscribe_action": "订阅",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """初始化插件实例。"""
        super().__init__(*args, **kwargs)
        self._config: Dict[str, Any] = {}
        self._actions: Dict[str, str] = {}

    def init_plugin(self, config: dict | None = None) -> None:
        """读取配置并同步宿主三类系统通知场景。"""
        config = dict(config or {})
        current = self._read_actions()
        valid = {item["value"] for item in self._action_options}
        self._actions = {
            key: str(config.get(key) or current.get(key) or "all").strip()
            for key in self._scene_types
        }
        self._actions = {
            key: value if value in valid else "all"
            for key, value in self._actions.items()
        }
        self._config = {
            "download_action": self._actions["download_action"],
            "organize_action": self._actions["organize_action"],
            "subscribe_action": self._actions["subscribe_action"],
            "notify_rules": self._normalize_rules(config.get("notify_rules")),
            "default_notify_target": self._normalize_targets(config.get("default_notify_target")),
        }
        if config:
            self._write_actions(self._actions)

    def get_state(self) -> bool:
        """返回插件可用状态。"""
        return True

    @staticmethod
    def get_render_mode() -> tuple[str, str]:
        """声明 Vue 联邦配置页面。"""
        return "vue", "dist/assets"

    def get_api(self) -> list[dict[str, Any]]:
        """注册完整 F4 面板所需的动态选项和保存接口。"""
        return [
            {"path": "/options", "endpoint": self.get_options_api, "methods": ["GET"], "auth": "bear", "summary": "获取 F4 通知目标选项"},
            {"path": "/save", "endpoint": self.save_api, "methods": ["POST"], "auth": "bear", "summary": "保存 F4 通知目标"},
        ]

    def get_form(self) -> tuple[list[dict], dict[str, Any]]:
        """Vue 模式下返回空 JSON 页面和当前配置模型。"""
        return [], dict(self._config)

    def get_page(self) -> list[dict]:
        """Vue 模式下由联邦 Page 组件渲染详情页。"""
        return []

    def stop_service(self) -> None:
        """释放插件资源；本插件没有后台服务。"""

    @staticmethod
    def _split_ids(value: Any) -> List[str]:
        """拆分逗号分隔的通知 ID。"""
        values = value if isinstance(value, (list, tuple, set)) else re.split(r"[,，]", str(value or ""))
        result: List[str] = []
        for item in values:
            text = str(item).strip()
            if text and text not in result:
                result.append(text)
        return result

    @classmethod
    def _normalize_target(cls, target: Any, default_prefix: str = "tg") -> str:
        """将通知目标规范化为带渠道前缀的值。"""
        raw = str(target or "").strip()
        if not raw:
            return ""
        if raw.startswith(("tg:", "qq:")):
            return raw
        if raw.startswith("group:"):
            return f"qq:{raw}"
        parts = re.split(r"\s+", raw, maxsplit=1)
        if len(parts) == 2 and re.fullmatch(r"-?\d+", parts[1].strip()):
            raw = parts[1].strip()
        prefix = default_prefix if default_prefix in {"tg", "qq"} else "tg"
        return f"{prefix}:{raw}"

    @classmethod
    def _normalize_targets(cls, value: Any) -> str:
        """规范化多目标并保存为逗号分隔字符串。"""
        result: List[str] = []
        for item in (re.split(r"[,，]", value) if isinstance(value, str) else (value or [])):
            target = cls._normalize_target(item)
            if target and target not in result:
                result.append(target)
        return ",".join(result)

    @classmethod
    def _normalize_rules(cls, value: Any) -> Dict[str, str]:
        """规范化按订阅用户名映射的通知目标。"""
        if not isinstance(value, dict):
            return {}
        result: Dict[str, str] = {}
        for username, targets in value.items():
            name = str(username or "").strip()
            normalized = cls._normalize_targets(targets)
            if name and normalized:
                result[name] = normalized
        return result

    def _load_notification_channels(self) -> List[Dict[str, Any]]:
        """读取启用的通知渠道及其目标配置。"""
        try:
            from app.application.notification import get_notification_configs

            return [
                {
                    "type": str(getattr(conf, "type", "") or "").strip().lower(),
                    "name": str(getattr(conf, "name", "") or ""),
                    "config": dict(getattr(conf, "config", None) or {}),
                }
                for conf in get_notification_configs(include_disabled=False)
            ]
        except Exception:
            return []

    @staticmethod
    def _channel_kind(channel_type: str) -> str:
        """将宿主通知渠道类型归一为 tg 或 qq。"""
        raw = str(channel_type or "").strip().lower()
        if raw in {"telegram", "tg"}:
            return "tg"
        if raw in {"qqbot", "qq"}:
            return "qq"
        return raw

    def _build_target_options(self) -> Dict[str, Any]:
        """从启用通知渠道构造群组、用户和管理员候选项。"""
        channels = self._load_notification_channels()
        ordered = sorted(
            channels,
            key=lambda item: 0 if item["type"] == "telegram" else (1 if item["type"] == "qqbot" else 2),
        )
        targets: List[Dict[str, str]] = []
        seen: set[str] = set()
        for channel in ordered:
            prefix = self._channel_kind(channel.get("type", ""))
            config = channel.get("config") or {}
            label = "Telegram" if prefix == "tg" else "QQ"
            if prefix == "tg":
                groups = self._split_ids(config.get("TELEGRAM_CHAT_ID"))
                admins = self._split_ids(config.get("TELEGRAM_ADMINS"))
                users = self._split_ids(config.get("TELEGRAM_USERS"))
                candidates = [
                    (item, f"[{label}] 群组 {item}", "group") for item in groups
                ] + [
                    (item, f"[{label}] 管理员 {item}", "admin") for item in admins
                ] + [
                    (item, f"[{label}] 用户白名单 {item}", "user") for item in users
                ]
                for item, title, source in candidates:
                    value = f"tg:{item}"
                    if value not in seen:
                        seen.add(value)
                        targets.append({"id": value, "title": title, "source": source, "channel": "tg"})
            elif prefix == "qq":
                groups = self._split_ids(config.get("QQ_GROUP_OPENID") or config.get("QQ_GROUP"))
                admins = self._split_ids(config.get("QQBOT_ADMINS"))
                users = self._split_ids(config.get("QQ_OPENID"))
                candidates = [
                    (f"group:{item}", f"[{label}] 群 {item}", "group") for item in groups
                ] + [
                    (item, f"[{label}] 管理员 {item}", "admin") for item in admins
                ] + [
                    (item, f"[{label}] 用户 {item}", "user") for item in users
                ]
                for item, title, source in candidates:
                    value = f"qq:{item}"
                    if value not in seen:
                        seen.add(value)
                        targets.append({"id": value, "title": title, "source": source, "channel": "qq"})
        return {"targets": targets}

    def _collect_usernames(self) -> List[str]:
        """读取当前订阅归属用户列表。"""
        try:
            from app.db.oper.subscribe import SubscribeOper

            result: List[str] = []
            for subscribe in SubscribeOper().list() or []:
                username = str(getattr(subscribe, "username", "") or "").strip()
                if username and username not in result:
                    result.append(username)
            return result
        except Exception:
            return []

    def get_options_api(self) -> Dict[str, Any]:
        """返回完整 F4 面板的场景、通知目标和订阅用户选项。"""
        data = self._build_target_options()
        data.update(
            {
                "actions": dict(self._actions),
                "options": list(self._action_options),
                "usernames": self._collect_usernames(),
                "rules": dict(self._config.get("notify_rules") or {}),
                "default_target": self._normalize_targets(self._config.get("default_notify_target")),
            }
        )
        return {"success": True, "data": data}

    def save_api(self, payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
        """保存完整 F4 面板配置并同步宿主系统通知开关。"""
        payload = payload or {}
        valid = {item["value"] for item in self._action_options}
        raw_actions = payload.get("actions") or {}
        actions = {
            key: str(raw_actions.get(key) or self._actions.get(key) or "all").strip()
            for key in self._scene_types
        }
        actions = {key: value if value in valid else "all" for key, value in actions.items()}
        rules = self._normalize_rules(payload.get("rules"))
        default_target = self._normalize_targets(payload.get("default_target"))
        config = {
            "download_action": actions["download_action"],
            "organize_action": actions["organize_action"],
            "subscribe_action": actions["subscribe_action"],
            "notify_rules": rules,
            "default_notify_target": default_target,
        }
        if not self.update_config(config):
            return {"success": False, "message": "F4 通知目标配置保存失败"}
        self.init_plugin(config)
        self._write_actions(actions)
        return {"success": True, "message": f"已保存系统通知目标和 {len(rules)} 条订阅用户映射"}

    def _read_actions(self) -> Dict[str, str]:
        """读取宿主 NotificationSwitchs 中的三类系统通知目标。"""
        result: Dict[str, str] = {}
        try:
            from app.db.systemconfig_oper import SystemConfigOper

            key = getattr(SystemConfigKey, "NotificationSwitchs", "NotificationSwitchs")
            switches = SystemConfigOper().get(key) or []
            by_type = {
                str(item.get("type") or "").strip(): str(item.get("action") or "").strip()
                for item in switches
                if isinstance(item, dict)
            }
            for config_key, scene_type in self._scene_types.items():
                result[config_key] = by_type.get(scene_type, "all")
        except Exception:
            result = {key: "all" for key in self._scene_types}
        return result

    def _write_actions(self, actions: Dict[str, str]) -> None:
        """只更新三类宿主系统通知目标，保留其它场景。"""
        from app.db.systemconfig_oper import SystemConfigOper

        key = getattr(SystemConfigKey, "NotificationSwitchs", "NotificationSwitchs")
        oper = SystemConfigOper()
        switches = oper.get(key) or []
        updates = {scene: actions[key] for key, scene in self._scene_types.items()}
        existing: set[str] = set()
        for item in switches:
            if not isinstance(item, dict):
                continue
            scene = str(item.get("type") or "").strip()
            if scene in updates:
                item["action"] = updates[scene]
                existing.add(scene)
        for scene, action in updates.items():
            if scene not in existing:
                switches.append({"type": scene, "action": action})
        oper.set(key, switches)
