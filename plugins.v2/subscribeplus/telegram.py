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


def build_main_menu(
    token: str, allow_rule_update: bool, can_identifier_fix: bool = False
) -> List[List[Dict[str, str]]]:
    first_row = [{"text": "下载", "callback_data": make_callback("download", token)}]
    if allow_rule_update:
        first_row.append({"text": "调整规则", "callback_data": make_callback("rule", token)})
    rows = [first_row]
    rows.append([{"text": "PT范围搜索", "callback_data": make_callback("ptscope", token)}])
    rows.append([{"text": "暂缓3天", "callback_data": make_callback("snooze3d", token)}])
    rows.append(
        [
            {"text": "忽略本次", "callback_data": make_callback("ignore", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    )
    return rows


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


def build_ci_mode_menu(token: str) -> List[List[Dict[str, str]]]:
    return [
        [
            {"text": "自动处理", "callback_data": make_callback("ci-auto", token)},
            {"text": "手动处理", "callback_data": make_callback("ci-manual", token)},
        ],
        [{"text": "结束", "callback_data": make_callback("close", token)}],
    ]


def build_ci_manual_type_menu(token: str) -> List[List[Dict[str, str]]]:
    return [
        [
            {"text": "TV", "callback_data": make_callback("ci-tv", token)},
            {"text": "Movie", "callback_data": make_callback("ci-movie", token)},
        ],
        [
            {"text": "返回", "callback_data": make_callback("ci-back", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ],
    ]


def build_ci_wait_tmdb_menu(token: str) -> List[List[Dict[str, str]]]:
    return [
        [
            {"text": "返回", "callback_data": make_callback("ci-manual", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    ]


def build_ci_done_menu(token: str) -> List[List[Dict[str, str]]]:
    return [
        [{"text": "再次识别", "callback_data": make_callback("ci-retry", token)}],
        [
            {"text": "返回", "callback_data": make_callback("ci-back", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ],
    ]


def build_identifier_candidate_menu(token: str, candidates: List[Dict[str, Any]]) -> List[List[Dict[str, str]]]:
    buttons: List[List[Dict[str, str]]] = []
    for index, item in enumerate(candidates[:8], start=1):
        site = item.get("site_name") or item.get("site") or "PT"
        seeders = item.get("seeders", 0)
        buttons.append(
            [
                {
                    "text": f"{index}. {site} 做种 {seeders}",
                    "callback_data": make_callback(f"ident{index}", token),
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


def build_identifier_done_menu(back_token: str) -> List[List[Dict[str, str]]]:
    return [
        [{"text": "再次识别", "callback_data": make_callback("ident-retry", back_token)}],
        [
            {"text": "返回", "callback_data": make_callback("back", back_token)},
            {"text": "结束", "callback_data": make_callback("close", back_token)},
        ],
    ]


def render_rule_preview_text(preview: Dict[str, Any], selected_text: str = "") -> str:
    lines = []
    if selected_text:
        lines.append(f"已选择：{selected_text}")
    if preview.get("field") == "sites":
        old_sites = ", ".join(preview.get("old_site_names") or [str(item) for item in preview.get("old_sites") or []])
        new_sites = ", ".join(preview.get("new_site_names") or [str(item) for item in preview.get("new_sites") or []])
        lines.extend(
            [
                "是否添加到订阅站点？",
                f"添加前：{old_sites or 'MP 默认搜索站点'}",
                f"添加后：{new_sites or '-'}",
            ]
        )
    else:
        lines.extend(
            [
                "是否添加到订阅包含规则？",
                f"添加前：{preview.get('old_include') or '-'}",
                f"添加后：{preview.get('new_include') or '-'}",
            ]
        )
    return "\n".join(lines)


def render_identifier_fix_result_text(result: Dict[str, Any]) -> str:
    if not result.get("success"):
        return "\n".join(
            [
                "自动修正识别失败",
                f"失败原因：{result.get('message') or result.get('reason') or '未知'}",
            ]
        )

    data = result.get("data") or {}
    added = data.get("added") or []
    lines = [
        result.get("message") or "已识别并写入自定义识别词",
        "已写入识别词：",
    ]
    lines.extend(str(item) for item in added[:10])
    if not added:
        lines.append("没有新增，可能已有相同识别词。")
    return "\n".join(lines)


def _join_values(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, (list, tuple, set)):
        return " / ".join(str(item) for item in values if str(item).strip())
    return str(values).strip()


def _short_title(title: str, limit: int = 96) -> str:
    title = str(title or "").strip()
    if len(title) <= limit:
        return title
    return f"{title[:limit - 1]}…"


def _candidate_detail_lines(candidates: List[Dict[str, Any]], limit: int = 3) -> List[str]:
    lines = []
    for index, candidate in enumerate((candidates or [])[:limit], start=1):
        site = candidate.get("site_name") or candidate.get("site") or "未知站点"
        title = _short_title(candidate.get("title") or "-")
        platforms = _join_values(candidate.get("platforms")) or "-"
        groups = _join_values(candidate.get("release_groups")) or "-"
        specs = [candidate.get("quality"), candidate.get("resolution"), candidate.get("video_codec")]
        spec_text = " / ".join(str(item) for item in specs if str(item or "").strip()) or "-"
        seeders = candidate.get("seeders")
        volume = candidate.get("volume_factor") or ("Free" if candidate.get("free") else "")
        meta = f"平台：{platforms}；官组：{groups}；规格：{spec_text}"
        extras = []
        if seeders not in (None, ""):
            extras.append(f"做种：{seeders}")
        if volume:
            extras.append(f"优惠：{volume}")
        lines.append(f"{index}. [{site}] {title}")
        lines.append(meta + (f"；{'；'.join(extras)}" if extras else ""))
    if candidates and len(candidates) > limit:
        lines.append(f"... 还有 {len(candidates) - limit} 个候选，插件页可查看完整列表")
    return lines


def render_notification_text(item: Dict[str, Any]) -> str:
    episodes = item.get("episodes") or []
    episode_text = ", ".join(
        f"E{episode.get('episode')}({episode.get('air_date')})" for episode in episodes[:10]
    )
    sites = ", ".join(item.get("sites") or []) or "MP 默认搜索站点"
    candidates = item.get("candidates") or []
    lines = [
        f"剧名：{item.get('title')}",
        f"季号：S{item.get('season')}；缺失：{episode_text or '未知'}",
        f"诊断：{item.get('message') or item.get('reason')}",
        f"候选资源：{len(candidates)} 个",
    ]
    progress = item.get("subscription_site_progress") or []
    if progress:
        lines.append("订阅站点：")
        for row in progress[:5]:
            site_name = row.get("site_name") or row.get("site") or "订阅站点"
            latest = int(row.get("latest_episode") or 0)
            target = int(row.get("target_episode") or 0)
            if latest and target:
                lines.append(f"- {site_name}：最新疑似 E{latest:02d}，未发现 E{target:02d}")
            elif latest:
                lines.append(f"- {site_name}：最新疑似 E{latest:02d}")
    if candidates and progress:
        lines.append("其他站点候选：")
    if candidates:
        lines.extend(_candidate_detail_lines(candidates))
    lines.append(f"搜索站点：{sites}")
    return "\n".join(lines)
