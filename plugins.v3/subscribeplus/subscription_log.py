"""把插件对单个订阅的处理日志并入宿主原生的「订阅活动」日志，并提供回读。

宿主自 MoviePilot V3 起为每个订阅维护独立日志 ``subscriptions/{id}.log``，
「订阅活动」页面可直接查看与下载。本模块做两件事：

1. :func:`log_scope` —— 在诊断某个订阅时把本插件输出的日志绑定到该订阅的
   日志文件，用户在原生日志里就能按订阅看到「搜索 → 插件诊断 → 下载」的完整链路，
   不必再去全局 ``moviepilot.log`` 里捞。
2. :func:`tail` —— 回读该订阅日志的尾部，供插件页面直接展示。

宿主接口不可用时全部静默降级，绝不因为日志能力缺失影响扫描主流程。
"""
from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Any, Optional

#: 写入订阅日志时使用的来源标识（出现在日志作用域里）。
LOG_SOURCE = "subscribeplus"

#: 单次回读的最大行数与最大字节数，避免超大日志撑爆前端。
MAX_TAIL_LINES = 1000
MAX_TAIL_BYTES = 200_000


def _as_id(subscribe_id: Any) -> int:
    """把订阅 ID 归一化为正整数，非法值返回 0。"""
    try:
        value = int(str(subscribe_id).strip())
    except (TypeError, ValueError):
        return 0
    return value if value > 0 else 0


def log_scope(subscribe_id: Any, source: str = LOG_SOURCE) -> contextlib.AbstractContextManager:
    """返回把日志绑定到指定订阅的作用域；宿主不支持时返回空上下文。"""
    sid = _as_id(subscribe_id)
    if not sid:
        return contextlib.nullcontext()
    try:
        from app.application.subscription.observability import subscription_log_scope
    except Exception:
        return contextlib.nullcontext()
    try:
        return subscription_log_scope(sid, source)
    except Exception:
        return contextlib.nullcontext()


def _log_root() -> Optional[Path]:
    """返回宿主日志根目录；读取失败返回 None。"""
    try:
        from app.sdk.config import settings

        raw = getattr(settings, "LOG_PATH", None)
        if raw:
            return Path(str(raw))
    except Exception:
        pass
    env = os.environ.get("LOG_PATH")
    if env:
        return Path(env)
    return None


def path_for(subscribe_id: Any) -> Optional[Path]:
    """返回该订阅日志文件路径（不保证存在）。"""
    sid = _as_id(subscribe_id)
    root = _log_root()
    if not sid or root is None:
        return None
    return root / "subscriptions" / f"{sid}.log"


def tail(subscribe_id: Any, lines: int = 300) -> dict:
    """回读订阅日志尾部。

    :param subscribe_id: 订阅 ID
    :param lines: 期望行数，内部限制在 ``1..MAX_TAIL_LINES``
    :return: ``{"exists": bool, "path": str, "text": str, "lines": int}``；
             文件不存在时 ``exists`` 为 False 且 ``text`` 为空串
    """
    sid = _as_id(subscribe_id)
    wanted = max(1, min(int(lines or 300), MAX_TAIL_LINES))
    path = path_for(sid)
    result = {"exists": False, "path": str(path) if path else "", "text": "", "lines": 0}
    if not sid or path is None or not path.exists():
        return result

    truncated = False
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > MAX_TAIL_BYTES:
                handle.seek(-MAX_TAIL_BYTES, os.SEEK_END)
                truncated = True
            raw = handle.read().decode("utf-8", errors="ignore")
    except OSError:
        return result

    rows = raw.splitlines()
    if truncated and rows:
        rows = rows[1:]  # 丢掉被截断的首行
    rows = rows[-wanted:]
    result.update({
        "exists": True,
        "text": "\n".join(rows),
        "lines": len(rows),
    })
    return result


__all__ = ["LOG_SOURCE", "log_scope", "path_for", "tail"]
