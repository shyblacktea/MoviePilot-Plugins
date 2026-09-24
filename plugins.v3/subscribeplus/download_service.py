"""候选下载提交编排服务。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class DownloadService:
    """处理候选上下文、缓存回建和 MoviePilot 下载提交。"""

    get_context: Callable[[str], Any]
    load_cached_context: Callable[[str], Any]
    start_native_search: Callable[[Dict[str, Any]], Dict[str, Any]]
    submit_context: Callable[[Any], None]
    post_message: Callable[..., None]
    log_info: Callable[[str], None]
    log_warning: Callable[[str], None]
    format_context: Callable[[Dict[str, Any], Dict[str, Any]], str]

    def download_candidate(
        self,
        diagnosis: Dict[str, Any],
        index: int,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """提交指定候选，内存上下文失效时回退缓存或原生搜索。"""
        event_data = event_data or {}
        candidates = diagnosis.get("candidates") or []
        if not (0 <= index < len(candidates)):
            self.post_message(event_data, title="订阅下载增强", text="候选资源不存在。", save_history=False)
            return
        candidate = candidates[index]
        candidate_id = candidate.get("download_payload") or candidate.get("candidate_id")
        context = self.get_context(str(candidate_id))
        from_cache = False
        if not context:
            try:
                context = self.load_cached_context(str(candidate_id))
                from_cache = bool(context)
            except Exception as exc:
                self.log_warning(f"订阅下载增强读取候选缓存失败: {exc}")
        if not context:
            result = self.start_native_search(diagnosis)
            text = result.get("message") or "已触发 MP 原生订阅搜索"
            text = f"候选下载上下文已失效，{text}"
            self.post_message(event_data, title="订阅下载增强", text=text, save_history=False)
            return
        try:
            self.submit_context(context)
            self.log_info(
                "订阅下载增强提交候选资源下载成功："
                + self.format_context(diagnosis, candidate)
                + f"，来源={'本地缓存重建' if from_cache else '内存上下文'}"
            )
            text = "已提交下载任务（缓存重建）。" if from_cache else "已提交下载任务。"
            self.post_message(event_data, title="订阅下载增强", text=text, save_history=False)
        except Exception as exc:
            self.log_warning(f"订阅下载增强提交候选资源下载失败: {exc}")
            self.post_message(event_data, title="订阅下载增强", text=f"提交下载失败：{exc}", save_history=False)
