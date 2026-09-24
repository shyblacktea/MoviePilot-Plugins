"""订阅搜索服务边界。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from .models import DiagnosisInput


@dataclass
class SubscriptionSearchService:
    """封装订阅搜索观察入口，隔离诊断编排与宿主搜索实现。"""

    execute_observer: Callable[[DiagnosisInput], Dict[str, Any]]

    def search(self, item: DiagnosisInput) -> Dict[str, Any]:
        """执行一次订阅搜索观察并返回标准化捕获结果。"""
        return self.execute_observer(item)
