"""Plex API 轻封装：枚举媒体库、列出条目、抽取 STRM part 信息。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from httpx import Client

from app.log import logger


class PlexClient:
    """封装 Plex 服务器只读查询，用于枚举需要补全媒体信息的 STRM 条目。"""

    def __init__(self, base_url: str, token: str, timeout: float = 30.0) -> None:
        """
        初始化 Plex 客户端。

        :param base_url: Plex 服务器根地址（可直连真实后端，如 http://192.168.0.122:32400）
        :param token: X-Plex-Token
        :param timeout: 请求超时秒数
        """
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def _get(self, path: str) -> Optional[dict]:
        """
        发起 GET 请求并解析 JSON。

        :param path: 相对路径（含查询串）
        :return: 解析后的 JSON，失败返回 None
        """
        sep = "&" if "?" in path else "?"
        url = f"{self._base}{path}{sep}X-Plex-Token={quote(self._token, safe='')}"
        try:
            with Client(timeout=self._timeout) as client:
                resp = client.get(url, headers={"Accept": "application/json"})
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("Plex API %s 返回 %s", path, resp.status_code)
        except Exception as e:
            logger.warning("Plex API 请求失败 %s: %s", path, e)
        return None

    def list_sections(self) -> List[Dict[str, Any]]:
        """
        列出所有媒体库分区。

        :return: [{key, title, type}]，type 为 movie/show 等
        """
        data = self._get("/library/sections")
        if not data:
            return []
        dirs = data.get("MediaContainer", {}).get("Directory", [])
        return [
            {"key": d.get("key"), "title": d.get("title"), "type": d.get("type")}
            for d in dirs
            if d.get("key")
        ]

    def _iter_section_items(self, section_key: str) -> List[Dict[str, Any]]:
        """
        列出某分区下全部条目的 ratingKey 与类型。

        :param section_key: 分区 key
        :return: [{rating_key, type, title}]
        """
        data = self._get(f"/library/sections/{section_key}/all")
        if not data:
            return []
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return [
            {
                "rating_key": m.get("ratingKey"),
                "type": m.get("type"),
                "title": m.get("title"),
            }
            for m in items
            if m.get("ratingKey")
        ]

    def _metadata(self, rating_key: str) -> List[Dict[str, Any]]:
        """
        获取条目元数据的 Metadata 数组。

        :param rating_key: 条目 ratingKey
        :return: Metadata 列表
        """
        data = self._get(f"/library/metadata/{rating_key}")
        if not data:
            return []
        return data.get("MediaContainer", {}).get("Metadata", [])

    def _children(self, rating_key: str) -> List[Dict[str, Any]]:
        """
        获取条目的子项（剧集的季、季的集）。

        :param rating_key: 父条目 ratingKey
        :return: 子项 Metadata 列表
        """
        data = self._get(f"/library/metadata/{rating_key}/children")
        if not data:
            return []
        return data.get("MediaContainer", {}).get("Metadata", [])

    @staticmethod
    def _extract_parts(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从单个条目元数据中抽取所有 Part 的关键字段。

        :param metadata: 条目 Metadata
        :return: [{part_id, file, container, title, duration_hint}]
        """
        result: List[Dict[str, Any]] = []
        title = metadata.get("title") or ""
        for media in metadata.get("Media", []) or []:
            for part in media.get("Part", []) or []:
                pid = part.get("id")
                pfile = part.get("file")
                if pid and pfile:
                    result.append(
                        {
                            "part_id": pid,
                            "file": pfile,
                            "container": part.get("container"),
                            "title": title,
                            "existing_duration": part.get("duration"),
                        }
                    )
        return result

    def collect_strm_parts(
        self, section_key: str, only_missing: bool = True
    ) -> List[Dict[str, Any]]:
        """
        枚举某分区下所有 STRM 文件对应的 Part 信息。

        对电影分区直接取条目 Part；对剧集分区逐层下钻到集再取 Part。
        only_missing 为 True 时仅返回缺失媒体流信息（无 Stream 或无时长）的 part。

        :param section_key: 分区 key
        :param only_missing: 是否仅返回缺失媒体信息的 part
        :return: STRM part 列表
        """
        parts: List[Dict[str, Any]] = []
        for item in self._iter_section_items(section_key):
            rating_key = item["rating_key"]
            itype = item.get("type")
            if itype in ("show",):
                # 剧集：show -> season -> episode
                for season in self._children(rating_key):
                    skey = season.get("ratingKey")
                    if not skey:
                        continue
                    for episode in self._children(skey):
                        parts.extend(self._collect_from_meta(episode, only_missing))
            else:
                for meta in self._metadata(rating_key):
                    parts.extend(self._collect_from_meta(meta, only_missing))
        return parts

    def _collect_from_meta(
        self, metadata: Dict[str, Any], only_missing: bool
    ) -> List[Dict[str, Any]]:
        """
        从条目元数据抽取 STRM part，按需过滤已有媒体信息的项。

        :param metadata: 条目 Metadata
        :param only_missing: 是否仅返回缺失媒体信息的 part
        :return: STRM part 列表
        """
        out: List[Dict[str, Any]] = []
        for p in self._extract_parts(metadata):
            fpath = (p.get("file") or "").lower()
            if not fpath.endswith(".strm"):
                continue
            if only_missing and p.get("existing_duration"):
                # 已有时长视为已补全，跳过
                continue
            out.append(p)
        return out
