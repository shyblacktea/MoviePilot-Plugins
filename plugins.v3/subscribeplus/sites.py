from __future__ import annotations

from typing import Any, Callable, Dict, List

from .models import PluginConfig


class SiteResolver:
    def __init__(self, load_mp_sites: Callable[[], List[Dict[str, Any]]]):
        self.load_mp_sites = load_mp_sites

    def available_sites(self) -> List[Dict[str, str]]:
        sites = []
        for raw in self.load_mp_sites() or []:
            site_id = raw.get("id", raw.get("value"))
            if site_id in (None, ""):
                continue
            sites.append(
                {
                    "id": str(site_id),
                    "name": str(raw.get("name") or raw.get("title") or site_id),
                }
            )
        return sites

    def resolve_for_category(self, config: PluginConfig, category: str) -> List[str]:
        available = [site["id"] for site in self.available_sites()]
        selected = [str(site_id) for site_id in (config.search_sites or [])]
        if not selected:
            return available
        selected_set = set(selected)
        return [site_id for site_id in available if site_id in selected_set]

    def name_map(self) -> Dict[str, str]:
        """返回 站点ID -> 站点名称 的映射。"""
        return {site["id"]: site["name"] for site in self.available_sites()}

    def names_for(self, site_ids: List[Any]) -> List[str]:
        """把站点ID列表转换为站点名称列表，找不到名称时回退为原ID。"""
        mapping = self.name_map()
        names = []
        for site_id in site_ids or []:
            key = str(site_id)
            names.append(mapping.get(key, key))
        return names
