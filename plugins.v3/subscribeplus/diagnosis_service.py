"""订阅诊断流程的无宿主副作用编排。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from .models import DiagnosisInput, DiagnosisItem


@dataclass
class DiagnosisService:
    """编排 MP 原生搜索、订阅范围诊断和其他站点诊断。"""

    run_moviepilot_search: Callable[[DiagnosisInput], Dict[str, Any]]
    diagnose_moviepilot_scope: Callable[[DiagnosisInput, Dict[str, Any]], DiagnosisItem]
    diagnose_other_sites: Callable[
        [DiagnosisInput, Dict[str, Any], DiagnosisItem], Optional[DiagnosisItem]
    ]
    log_info: Callable[[str], None]
    format_item_context: Callable[[DiagnosisInput], str]

    def diagnose(self, item: DiagnosisInput) -> Optional[DiagnosisItem]:
        """执行一部订阅的诊断编排，不直接访问宿主或持久化数据。"""
        mp_search = self.run_moviepilot_search(item)
        mp_diagnosis = self.diagnose_moviepilot_scope(item, mp_search)
        if mp_diagnosis.candidates:
            if mp_diagnosis.reason == "downloadable":
                self.log_info(
                    "订阅下载增强触发 MP 订阅搜索后发现可匹配资源，已交给 MP 下载处理："
                    + self.format_item_context(item)
                )
                return None
            return mp_diagnosis

        other_site_diagnosis = self.diagnose_other_sites(item, mp_search, mp_diagnosis)
        if other_site_diagnosis and other_site_diagnosis.candidates:
            return other_site_diagnosis

        self.log_info(
            f"订阅下载增强：{item.title} 在 MP 订阅搜索范围内没有候选资源，"
            "不再执行插件 PT 范围兜底搜索"
        )
        return None
