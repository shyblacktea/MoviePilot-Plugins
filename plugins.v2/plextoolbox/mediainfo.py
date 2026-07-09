"""媒体信息补全编排：枚举 Plex STRM 条目，取数据源，写入 helper。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from app.log import logger

from .emby_client import EmbyClient
from .ffprobe_source import ffprobe_url, read_strm_url, resolve_final_url
from .helper_client import HelperClient
from .plex_client import PlexClient


class MediaInfoCompleter:
    """编排 Plex STRM 媒体流信息补全的完整流程。"""

    def __init__(
        self,
        plex: PlexClient,
        helper: HelperClient,
        emby: Optional[EmbyClient] = None,
        use_emby: bool = True,
        use_ffprobe: bool = True,
        overwrite_streams: bool = True,
        concurrency: int = 3,
        force_write: bool = False,
    ) -> None:
        """
        初始化补全器。

        :param plex: Plex 客户端
        :param helper: helper 写库客户端
        :param emby: Emby 客户端（数据源①）
        :param use_emby: 是否启用 Emby 数据源
        :param use_ffprobe: 是否启用 ffprobe 数据源
        :param overwrite_streams: 写入前是否清空该 part 旧流
        :param concurrency: 数据源探测并发数
        :param force_write: 是否忽略 Plex 繁忙强制写入
        """
        self._plex = plex
        self._helper = helper
        self._emby = emby
        self._use_emby = use_emby and emby is not None
        self._use_ffprobe = use_ffprobe
        self._overwrite = overwrite_streams
        self._concurrency = max(1, concurrency)
        self._force = force_write

    def _resolve_one(self, part: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        为单个 STRM part 解析媒体信息，按 Emby -> ffprobe 优先级。

        :param part: {part_id, file, title, ...}
        :return: helper payload（含 part_id 与流信息），失败返回 None
        """
        file_path = part.get("file") or ""
        info: Optional[Dict[str, Any]] = None

        if self._use_emby and self._emby:
            try:
                info = self._emby.find_streams_by_name(file_path)
            except Exception as e:
                logger.debug("Emby 数据源失败 %s: %s", file_path, e)

        if not info and self._use_ffprobe:
            url = read_strm_url(file_path)
            if url:
                final = resolve_final_url(url)
                try:
                    info = ffprobe_url(final)
                except Exception as e:
                    logger.debug("ffprobe 数据源失败 %s: %s", file_path, e)

        if not info:
            return None
        info["part_id"] = part["part_id"]
        info["overwrite_streams"] = self._overwrite
        return info

    def run(
        self,
        section_keys: List[str],
        only_missing: bool = True,
        progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        执行补全：枚举分区 STRM part，解析数据源并写入 helper。

        :param section_keys: 要处理的 Plex 分区 key 列表
        :param only_missing: 是否仅处理缺失媒体信息的 part
        :param progress_cb: 进度回调（收到阶段性统计）
        :return: 汇总结果
        """
        summary: Dict[str, Any] = {
            "sections": len(section_keys),
            "strm_parts": 0,
            "resolved": 0,
            "emby_hits": 0,
            "ffprobe_hits": 0,
            "unresolved": 0,
            "written_ok": 0,
            "write_failed": 0,
            "helper_busy": False,
            "details": [],
        }

        # 1. 枚举 STRM part
        all_parts: List[Dict[str, Any]] = []
        for skey in section_keys:
            all_parts.extend(self._plex.collect_strm_parts(skey, only_missing))
        summary["strm_parts"] = len(all_parts)
        if not all_parts:
            return summary
        if progress_cb:
            progress_cb({"phase": "enumerated", "count": len(all_parts)})

        # 2. 并发解析数据源
        payloads: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=self._concurrency) as pool:
            futures = {pool.submit(self._resolve_one, p): p for p in all_parts}
            done = 0
            for fut in as_completed(futures):
                done += 1
                info = fut.result()
                if info:
                    payloads.append(info)
                    summary["resolved"] += 1
                    if info.get("source") == "emby":
                        summary["emby_hits"] += 1
                    elif info.get("source") == "ffprobe":
                        summary["ffprobe_hits"] += 1
                else:
                    summary["unresolved"] += 1
                if progress_cb and done % 10 == 0:
                    progress_cb(
                        {"phase": "resolving", "done": done, "total": len(all_parts)}
                    )

        # 3. 写入 helper（去掉 source 字段再发）
        for p in payloads:
            p.pop("source", None)
        if payloads:
            res = self._helper.write_batch(payloads, force=self._force)
            if res is None:
                summary["write_failed"] = len(payloads)
            elif res.get("busy"):
                summary["helper_busy"] = True
                summary["write_failed"] = len(payloads)
            else:
                summary["written_ok"] = res.get("ok", 0)
                summary["write_failed"] = len(payloads) - res.get("ok", 0)
        if progress_cb:
            progress_cb({"phase": "done", **summary})
        return summary
