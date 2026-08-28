"""手动订阅候选记录存储。

来源运行只负责抓取和保存候选，不直接创建 MoviePilot 订阅；用户在前端确认后，
再通过插件 API 按候选的媒体身份创建订阅。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

CANDIDATES_KEY = "candidates"


class CandidateStore:
    """封装候选条目的插件 KV 存储、筛选、分页和删除。"""

    def __init__(self, get_data, save_data, del_data):
        """加载候选记录并保存插件 KV 读写函数。"""
        self._records = list(get_data(CANDIDATES_KEY) or [])
        self._save = save_data
        self._delete_key = del_data

    def replace_provider(self, provider: str, records: list[dict]) -> None:
        """替换某个来源本次抓取结果，保留其它来源的候选。"""
        current = [r for r in self._records if r.get("provider") != provider]
        self._records = current + list(records or [])
        self.flush()

    def all(self) -> list[dict]:
        """返回全部候选记录的副本。"""
        return [dict(item) for item in self._records]

    def get(self, candidate_id: str) -> Optional[dict]:
        """按候选 ID 查找一条记录。"""
        return next((r for r in self._records if r.get("candidate_id") == candidate_id), None)

    def mark_subscribed(self, candidate_id: str, subscribe_id: int | None = None) -> bool:
        """把候选标记为已手动订阅并记录订阅 ID。"""
        item = self.get(candidate_id)
        if item is None:
            return False
        item["status"] = "subscribed"
        item["subscribe_id"] = subscribe_id
        item["subscribed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.flush()
        return True

    def delete_many(self, candidate_ids: list[str]) -> int:
        """删除指定候选并返回实际删除数量。"""
        targets = {str(value) for value in candidate_ids or [] if value}
        before = len(self._records)
        self._records = [r for r in self._records if str(r.get("candidate_id")) not in targets]
        removed = before - len(self._records)
        if removed:
            self.flush()
        return removed

    def query(self, provider: Optional[str] = None, status: Optional[str] = None,
              mtype: Optional[str] = None, keyword: Optional[str] = None,
              year_min=None, year_max=None, page: int = 1, count: int = 50) -> Tuple[list[dict], int]:
        """按来源、状态、类型、标题和年份筛选候选并分页。"""
        def values(raw):
            if raw is None:
                return None
            result = {str(v).strip() for v in (raw if isinstance(raw, (list, tuple, set)) else str(raw).split(","))}
            return result or None

        providers, statuses, types = values(provider), values(status), values(mtype)
        keyword = str(keyword or "").strip().lower()
        try:
            ymin = int(year_min) if year_min not in (None, "") else None
        except (TypeError, ValueError):
            ymin = None
        try:
            ymax = int(year_max) if year_max not in (None, "") else None
        except (TypeError, ValueError):
            ymax = None

        def year_ok(value):
            if ymin is None and ymax is None:
                return True
            try:
                year = int(str(value)[:4])
            except (TypeError, ValueError):
                return False
            return (ymin is None or year >= ymin) and (ymax is None or year <= ymax)

        result = [item for item in self._records
                  if (providers is None or item.get("provider") in providers)
                  and (statuses is None or item.get("status") in statuses)
                  and (types is None or item.get("type") in types)
                  and (not keyword or keyword in str(item.get("title") or "").lower())
                  and year_ok(item.get("year"))]
        result.sort(key=lambda item: item.get("time") or "", reverse=True)
        total = len(result)
        page = max(int(page or 1), 1)
        count = max(int(count or 1), 1)
        start = (page - 1) * count
        return result[start:start + count], total

    def stats(self) -> dict:
        """统计候选总量、来源和状态。"""
        by_provider = {}
        by_status = {}
        for item in self._records:
            provider = item.get("provider") or "unknown"
            status = item.get("status") or "candidate"
            by_provider[provider] = by_provider.get(provider, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        return {"total": len(self._records), "by_provider": by_provider, "by_status": by_status}

    def flush(self) -> None:
        """把候选整体保存到插件 KV。"""
        self._save(CANDIDATES_KEY, self._records)


__all__ = ["CandidateStore", "CANDIDATES_KEY"]
