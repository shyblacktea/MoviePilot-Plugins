from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


PLUGIN_ID = "SubscribePlus"
MAX_CALLBACK_BYTES = 64


def make_token(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def make_callback(action: str, token: str) -> str:
    callback = f"[PLUGIN]{PLUGIN_ID}|{action}:{token}"
    if len(callback.encode("utf-8")) > MAX_CALLBACK_BYTES:
        raise ValueError("Telegram callback_data 超过长度限制")
    return callback


def build_main_menu(token: str, allow_rule_update: bool) -> List[List[Dict[str, str]]]:
    first_row = [{"text": "下载", "callback_data": make_callback("download", token)}]
    if allow_rule_update:
        first_row.append({"text": "调整规则", "callback_data": make_callback("rule", token)})
    return [
        first_row,
        [
            {"text": "忽略本次", "callback_data": make_callback("ignore", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ],
    ]


def build_resource_menu(token: str, candidates: List[Dict[str, Any]]) -> List[List[Dict[str, str]]]:
    buttons: List[List[Dict[str, str]]] = []
    for index, item in enumerate(candidates[:8], start=1):
        site = item.get("site_name") or item.get("site") or "PT"
        seeders = item.get("seeders", 0)
        buttons.append(
            [
                {
                    "text": f"{index}. {site} 做种 {seeders}",
                    "callback_data": make_callback(f"pick{index}", token),
                }
            ]
        )
    buttons.append(
        [
            {"text": "返回", "callback_data": make_callback("back", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    )
    return buttons


def build_rule_menu(token: str, suggestions: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    buttons = [
        [
            {
                "text": item.get("text") or item.get("value") or item.get("kind") or "规则",
                "callback_data": make_callback(f"rule{index}", token),
            }
        ]
        for index, item in enumerate(suggestions[:8], start=1)
    ]
    buttons.append(
        [
            {"text": "返回", "callback_data": make_callback("back", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    )
    return buttons


def build_rule_confirm_menu(confirm_token: str, back_token: str) -> List[List[Dict[str, str]]]:
    return [
        [{"text": "确认添加", "callback_data": make_callback("rule-confirm", confirm_token)}],
        [
            {"text": "返回", "callback_data": make_callback("rule", back_token)},
            {"text": "结束", "callback_data": make_callback("close", back_token)},
        ],
    ]


def build_rule_done_menu(back_token: str) -> List[List[Dict[str, str]]]:
    return [
        [
            {"text": "返回", "callback_data": make_callback("rule", back_token)},
            {"text": "结束", "callback_data": make_callback("close", back_token)},
        ]
    ]


def render_rule_preview_text(preview: Dict[str, Any], selected_text: str = "") -> str:
    lines = []
    if selected_text:
        lines.append(f"已选择：{selected_text}")
    lines.extend(
        [
            "是否添加到订阅包含规则？",
            f"添加前：{preview.get('old_include') or '-'}",
            f"添加后：{preview.get('new_include') or '-'}",
        ]
    )
    return "\n".join(lines)


def render_notification_text(item: Dict[str, Any]) -> str:
    episodes = item.get("episodes") or []
    episode_text = ", ".join(
        f"E{episode.get('episode')}({episode.get('air_date')})" for episode in episodes[:10]
    )
    sites = ", ".join(item.get("sites") or []) or "MP 默认搜索站点"
    return "\n".join(
        [
            f"剧名：{item.get('title')}",
            f"季号：S{item.get('season')}；缺失：{episode_text or '未知'}",
            f"诊断：{item.get('message') or item.get('reason')}",
            f"候选资源：{len(item.get('candidates') or [])} 个",
            f"搜索站点：{sites}",
        ]
    )
