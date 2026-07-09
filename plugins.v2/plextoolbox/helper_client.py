"""helper 写库服务的 HTTP 客户端封装。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from httpx import Client

from app.log import logger


class HelperClient:
    """封装对 122 上 plex-mediainfo-helper 写库服务的调用。"""

    def __init__(self, base_url: str, token: str = "", timeout: float = 60.0) -> None:
        """
        初始化 helper 客户端。

        :param base_url: helper 地址，如 http://192.168.0.122:9001
        :param token: 访问 token（对应 helper 的 PTH_TOKEN）
        :param timeout: 请求超时秒数
        """
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def _headers(self) -> Dict[str, str]:
        """构建带 token 的请求头。"""
        h = {"Content-Type": "application/json"}
        if self._token:
            h["X-PTH-Token"] = self._token
        return h

    def health(self) -> bool:
        """
        健康检查。

        :return: 服务可用返回 True
        """
        try:
            with Client(timeout=10.0) as client:
                resp = client.get(f"{self._base}/health")
                return resp.status_code == 200
        except Exception:
            return False

    def dbinfo(self) -> Optional[Dict[str, Any]]:
        """
        查询 helper 的数据库信息。

        :return: dbinfo 响应，失败返回 None
        """
        try:
            with Client(timeout=15.0) as client:
                resp = client.get(f"{self._base}/dbinfo", headers=self._headers())
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("helper /dbinfo 返回 %s", resp.status_code)
        except Exception as e:
            logger.warning("helper /dbinfo 失败: %s", e)
        return None

    def write_batch(
        self, items: List[Dict[str, Any]], force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        批量写入媒体信息。

        :param items: 每项为 helper payload（含 part_id 等）
        :param force: 是否忽略 Plex 繁忙检测强制写入
        :return: 写入结果，失败返回 None
        """
        if not items:
            return {"success": True, "total": 0, "ok": 0, "results": []}
        try:
            with Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base}/write_batch",
                    headers=self._headers(),
                    json={"items": items, "force": force},
                )
                if resp.status_code in (200, 409):
                    return resp.json()
                logger.warning("helper /write_batch 返回 %s", resp.status_code)
        except Exception as e:
            logger.warning("helper /write_batch 失败: %s", e)
        return None
