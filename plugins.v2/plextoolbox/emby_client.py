"""Emby API 轻封装：按文件名/路径查询条目的 MediaStreams 媒体流信息。"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from httpx import Client

from app.log import logger


class EmbyClient:
    """封装 Emby 只读查询，用于按文件名匹配媒体并取其媒体流信息作为数据源。"""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        """
        初始化 Emby 客户端。

        :param base_url: Emby 根地址，如 http://192.168.0.121:8096
        :param api_key: Emby API Key
        :param timeout: 请求超时秒数
        """
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._timeout = timeout
        self._user_id: Optional[str] = None

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Optional[dict]:
        """
        发起 GET 请求并解析 JSON。

        :param path: 相对路径
        :param params: 查询参数
        :return: JSON 或 None
        """
        query = {"api_key": self._key}
        if params:
            query.update(params)
        qs = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in query.items())
        url = f"{self._base}{path}?{qs}"
        try:
            with Client(timeout=self._timeout) as client:
                resp = client.get(url, headers={"Accept": "application/json"})
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("Emby API %s 返回 %s", path, resp.status_code)
        except Exception as e:
            logger.warning("Emby API 请求失败 %s: %s", path, e)
        return None

    def find_streams_by_name(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        按文件名（不含扩展名）搜索 Emby 条目并返回其归一化媒体流信息。

        :param file_name: STRM 文件名或媒体文件名
        :return: 归一化后的媒体信息 dict，未找到返回 None
        """
        stem = os.path.splitext(os.path.basename(file_name))[0]
        if not stem:
            return None
        data = self._get(
            "/Items",
            {
                "Recursive": "true",
                "SearchTerm": stem,
                "Fields": "MediaSources,Path",
                "Limit": "5",
            },
        )
        if not data:
            return None
        for item in data.get("Items", []) or []:
            info = self._extract_from_item(item, stem)
            if info:
                return info
        return None

    @staticmethod
    def _basename_stem(path: str) -> str:
        """取路径的无扩展名文件名。"""
        return os.path.splitext(os.path.basename(path or ""))[0]

    def _extract_from_item(
        self, item: Dict[str, Any], want_stem: str
    ) -> Optional[Dict[str, Any]]:
        """
        从 Emby 条目中匹配文件名并抽取归一化媒体流信息。

        :param item: Emby 条目
        :param want_stem: 目标无扩展名文件名
        :return: 归一化媒体信息，不匹配返回 None
        """
        sources = item.get("MediaSources") or []
        for src in sources:
            src_stem = self._basename_stem(src.get("Path") or src.get("Name") or "")
            if src_stem and src_stem != want_stem:
                continue
            info = self._normalize_source(src)
            if info:
                return info
        return None

    def _normalize_source(self, src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将 Emby MediaSource 归一化为 helper 需要的 payload 结构。

        :param src: Emby MediaSource
        :return: 归一化后的媒体信息
        """
        streams_in = src.get("MediaStreams") or []
        if not streams_in:
            return None
        # Emby 时长单位 100 纳秒(ticks)，转毫秒
        ticks = src.get("RunTimeTicks")
        duration_ms = int(ticks / 10000) if ticks else None
        info: Dict[str, Any] = {
            "container": (src.get("Container") or "").split(",")[0] or None,
            "size": src.get("Size"),
            "bitrate": int(src["Bitrate"] / 1000) if src.get("Bitrate") else None,
            "duration": duration_ms,
            "streams": [],
            "source": "emby",
        }
        # Emby MediaStream.Type: Video/Audio/Subtitle -> Plex stream_type 1/2/3
        type_map = {"Video": 1, "Audio": 2, "Subtitle": 3}
        video_seen = False
        audio_seen = False
        for s in streams_in:
            stype = type_map.get(s.get("Type"))
            if not stype:
                continue
            stream = {
                "stream_type": stype,
                "codec": (s.get("Codec") or "").lower() or None,
                "index": s.get("Index"),
                "language": s.get("Language"),
            }
            if stype == 1:
                stream.update(
                    {
                        "width": s.get("Width"),
                        "height": s.get("Height"),
                        "bitrate": int(s["BitRate"] / 1000) if s.get("BitRate") else None,
                        "frame_rate": s.get("RealFrameRate") or s.get("AverageFrameRate"),
                        "bit_depth": s.get("BitDepth"),
                    }
                )
                if not video_seen:
                    info["width"] = s.get("Width")
                    info["height"] = s.get("Height")
                    info["video_codec"] = (s.get("Codec") or "").lower() or None
                    info["frame_rate"] = s.get("RealFrameRate") or s.get("AverageFrameRate")
                    video_seen = True
            elif stype == 2:
                stream.update(
                    {
                        "bitrate": int(s["BitRate"] / 1000) if s.get("BitRate") else None,
                        "channels": s.get("Channels"),
                        "sampling_rate": s.get("SampleRate"),
                    }
                )
                if not audio_seen:
                    info["audio_codec"] = (s.get("Codec") or "").lower() or None
                    info["audio_channels"] = s.get("Channels")
                    audio_seen = True
            info["streams"].append(stream)
        return info if info["streams"] else None
