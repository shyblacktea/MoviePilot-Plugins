from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


PLUGIN_ID = "SubscribePlus"
MAX_CALLBACK_BYTES = 64
CANDIDATE_PAGE_SIZE = 3
RESOURCE_PAGE_SIZE = 5


def make_token(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def make_callback(action: str, token: str) -> str:
    callback = f"[PLUGIN]{PLUGIN_ID}|{action}:{token}"
    if len(callback.encode("utf-8")) > MAX_CALLBACK_BYTES:
        raise ValueError("Telegram callback_data 超过长度限制")
    return callback


def _page_count(total: int, page_size: int) -> int:
    if total <= 0:
        return 1
    return max(1, (total + page_size - 1) // page_size)


def _clamp_page(page: int, total: int, page_size: int) -> int:
    return max(0, min(int(page or 0), _page_count(total, page_size) - 1))


def build_main_menu(
    token: str,
    allow_rule_update: bool,
    can_identifier_fix: bool = False,
    candidate_count: int = 0,
    candidate_page: int = 0,
    candidate_page_size: int = CANDIDATE_PAGE_SIZE,
    search_keyword_suggestion: str = "",
) -> List[List[Dict[str, str]]]:
    first_row = [{"text": "下载", "callback_data": make_callback("download", token)}]
    if allow_rule_update:
        first_row.append({"text": "调整规则", "callback_data": make_callback("rule", token)})
    rows = [first_row]
    pages = _page_count(candidate_count, candidate_page_size)
    if candidate_count > candidate_page_size and pages > 1:
        page = _clamp_page(candidate_page, candidate_count, candidate_page_size)
        pager = []
        if page > 0:
            pager.append({"text": "候选上一页", "callback_data": make_callback(f"cand{page}", token)})
        if page < pages - 1:
            pager.append({"text": "候选下一页", "callback_data": make_callback(f"cand{page + 2}", token)})
        if pager:
            rows.append(pager)
    rows.append([{"text": "搜索其他站点", "callback_data": make_callback("ptscope", token)}])
    if search_keyword_suggestion:
        rows.append([{"text": "添加搜索关键词", "callback_data": make_callback("keyword", token)}])
    rows.append([{"text": "暂缓3天", "callback_data": make_callback("snooze3d", token)}])
    rows.append(
        [
            {"text": "忽略本次", "callback_data": make_callback("ignore", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    )
    return rows


def build_keyword_confirm_menu(token: str) -> List[List[Dict[str, str]]]:
    return [
        [{"text": "确认添加", "callback_data": make_callback("keyword-confirm", token)}],
        [
            {"text": "返回", "callback_data": make_callback("open", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ],
    ]


def build_other_sites_menu(
    token: str,
    other_sites: List[Dict[str, str]],
) -> List[List[Dict[str, str]]]:
    """其他站点选择菜单：单选各站点 + 全部其他站点 + 返回。

    other_sites: [{"id": "13", "name": "春天"}, ...]，顺序即索引，回调用 pts<idx> 避免超长。
    """
    rows: List[List[Dict[str, str]]] = []
    if other_sites:
        rows.append([{"text": "全部其他站点", "callback_data": make_callback("ptsall", token)}])
    for idx, site in enumerate(other_sites[:16]):
        name = str(site.get("name") or site.get("id") or "站点")
        rows.append([{"text": name, "callback_data": make_callback(f"pts{idx}", token)}])
    if not other_sites:
        rows.append([{"text": "（无其他站点可搜）", "callback_data": make_callback("open", token)}])
    rows.append(
        [
            {"text": "返回", "callback_data": make_callback("open", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    )
    return rows


def build_resource_menu(
    token: str,
    candidates: List[Dict[str, Any]],
    page: int = 0,
    page_size: int = RESOURCE_PAGE_SIZE,
) -> List[List[Dict[str, str]]]:
    buttons: List[List[Dict[str, str]]] = []
    page = _clamp_page(page, len(candidates or []), page_size)
    start = page * page_size
    end = start + page_size
    for index, item in enumerate((candidates or [])[start:end], start=start + 1):
        site = item.get("site_name") or item.get("site") or "PT"
        seeders = item.get("seeders", 0)
        groups = item.get("release_groups") or []
        platforms = item.get("platforms") or []
        reso = str(item.get("resolution") or "").strip()
        parts = [str(site)]
        if groups:
            parts.append(str(groups[0]))
        if platforms:
            parts.append(str(platforms[0]))
        if reso:
            parts.append(reso)
        parts.append(f"做种{seeders}")
        text = _short_title(f"{index}." + "｜".join(parts), limit=40)
        buttons.append(
            [
                {
                    "text": text,
                    "callback_data": make_callback(f"pick{index}", token),
                }
            ]
        )
    pages = _page_count(len(candidates or []), page_size)
    if len(candidates or []) > page_size and pages > 1:
        pager = []
        if page > 0:
            pager.append({"text": "上一页", "callback_data": make_callback(f"rpage{page}", token)})
        if page < pages - 1:
            pager.append({"text": "下一页", "callback_data": make_callback(f"rpage{page + 2}", token)})
        if pager:
            buttons.append(pager)
    buttons.append(
        [
            {"text": "返回", "callback_data": make_callback("back", token)},
            {"text": "结束", "callback_data": make_callback("close", token)},
        ]
    )
    return buttons


def build_pending_menu(items: List[tuple[str, Dict[str, Any]]]) -> List[List[Dict[str, str]]]:
    buttons: List[List[Dict[str, str]]] = []
    for token, item in items[:20]:
        title = _short_title(item.get("title") or "未命名", limit=28)
        season = int(item.get("season") or 0)
        episodes = item.get("episodes") or []
        episode_text = "/".join(
            f"E{int(episode.get('episode') or 0):02d}"
            for episode in episodes[:3]
            if int(episode.get("episode") or 0)
        )
        suffix = f" S{season:02d} {episode_text}" if season or episode_text else ""
        buttons.append([{"text": f"{title}{suffix}", "callback_data": make_callback("open", token)}])
    buttons.append([{"text": "结束", "callback_data": make_callback("close", "spmenu")}])
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


def _candidate_detail_lines(
    candidates: List[Dict[str, Any]],
    limit: int = CANDIDATE_PAGE_SIZE,
    page: int = 0,
) -> List[str]:
    lines = []
    total = len(candidates or [])
    page = _clamp_page(page, total, limit)
    pages = _page_count(total, limit)
    start = page * limit
    end = start + limit
    if total > limit:
        lines.append(f"候选资源第 {page + 1}/{pages} 页")
    for index, candidate in enumerate((candidates or [])[start:end], start=start + 1):
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
    if total > end:
        lines.append(f"... 还有 {total - end} 个候选，可点下一页查看")
    return lines


def render_notification_text(
    item: Dict[str, Any],
    candidate_page: int = 0,
    candidate_page_size: int = CANDIDATE_PAGE_SIZE,
) -> str:
    episodes = item.get("episodes") or []
    episode_text = ", ".join(
        f"E{episode.get('episode')}({episode.get('air_date')})" for episode in episodes[:10]
    )
    site_display = item.get("site_names") or item.get("sites") or []
    sites = ", ".join(str(s) for s in site_display) or "MP 默认搜索站点"
    candidates = item.get("candidates") or []
    lines = [
        f"剧名：{item.get('title')}",
        f"季号：S{item.get('season')}；缺失：{episode_text or '未知'}",
        f"诊断：{item.get('message') or item.get('reason')}",
        f"候选资源：{len(candidates)} 个",
    ]
    if item.get("search_keyword_suggestion"):
        lines.append(f"建议搜索关键词：{item.get('search_keyword_suggestion')}")
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
        lines.extend(_candidate_detail_lines(candidates, limit=candidate_page_size, page=candidate_page))
    lines.append(f"搜索站点：{sites}")
    return "\n".join(lines)
