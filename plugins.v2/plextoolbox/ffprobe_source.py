"""ffprobe 数据源：读取 STRM 内容得到远程直链并探测媒体流信息。"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from httpx import Client

from app.log import logger


def read_strm_url(strm_path: str) -> str:
    """
    读取 STRM 文件内容，返回其中的远程地址。

    :param strm_path: STRM 文件路径（对 MP 容器可达时才有效）
    :return: STRM 内的 URL，读不到返回空串
    """
    try:
        if os.path.isfile(strm_path):
            with open(strm_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            first = content.splitlines()[0].strip() if content else ""
            if first.startswith(("http://", "https://")):
                return first
    except OSError as e:
        logger.debug("读取 STRM 失败 %s: %s", strm_path, e)
    return ""


def resolve_final_url(url: str, timeout: float = 15.0) -> str:
    """
    跟随 302 得到最终可探测的直链（STRM 内地址可能是中间跳转地址）。

    :param url: STRM 内的 URL
    :param timeout: 超时秒数
    :return: 最终直链，失败返回原 url
    """
    if not url:
        return ""
    try:
        with Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.head(url)
            if 300 < resp.status_code < 400:
                loc = resp.headers.get("location", "")
                if loc:
                    return loc
    except Exception as e:
        logger.debug("解析最终直链失败 %s: %s", url, e)
    return url


def ffprobe_url(url: str, timeout: int = 40) -> Optional[Dict[str, Any]]:
    """
    对远程直链执行 ffprobe，仅读文件头，返回归一化媒体流信息。

    :param url: 可探测的远程直链
    :param timeout: ffprobe 超时秒数
    :return: 归一化媒体信息，失败返回 None
    """
    if not url:
        return None
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-analyzeduration", "10000000",
        "-probesize", "10000000",
        url,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if proc.returncode != 0:
            logger.debug("ffprobe 返回码 %s: %s", proc.returncode, proc.stderr[:200])
            return None
        data = json.loads(proc.stdout or "{}")
    except (subprocess.TimeoutExpired, ValueError, OSError) as e:
        logger.debug("ffprobe 执行失败: %s", e)
        return None
    return _normalize_ffprobe(data)


def _normalize_ffprobe(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    将 ffprobe JSON 输出归一化为 helper 需要的 payload 结构。

    :param data: ffprobe -print_format json 的输出
    :return: 归一化媒体信息，无有效流返回 None
    """
    fmt = data.get("format", {}) or {}
    streams_in = data.get("streams", []) or []
    if not streams_in:
        return None
    duration_s = fmt.get("duration")
    duration_ms = int(float(duration_s) * 1000) if duration_s else None
    bitrate = fmt.get("bit_rate")
    info: Dict[str, Any] = {
        "container": _norm_container(fmt.get("format_name")),
        "size": int(fmt["size"]) if fmt.get("size") else None,
        "bitrate": int(int(bitrate) / 1000) if bitrate else None,
        "duration": duration_ms,
        "streams": [],
        "source": "ffprobe",
    }
    type_map = {"video": 1, "audio": 2, "subtitle": 3}
    video_seen = False
    audio_seen = False
    for s in streams_in:
        stype = type_map.get(s.get("codec_type"))
        if not stype:
            continue
        codec = (s.get("codec_name") or "").lower() or None
        sbr = s.get("bit_rate")
        stream: Dict[str, Any] = {
            "stream_type": stype,
            "codec": codec,
            "index": s.get("index"),
            "language": (s.get("tags", {}) or {}).get("language"),
        }
        if stype == 1:
            stream.update(
                {
                    "width": s.get("width"),
                    "height": s.get("height"),
                    "bitrate": int(int(sbr) / 1000) if sbr else None,
                    "frame_rate": _parse_fps(s.get("r_frame_rate")),
                    "bit_depth": _bit_depth(s),
                }
            )
            if not video_seen:
                info["width"] = s.get("width")
                info["height"] = s.get("height")
                info["video_codec"] = codec
                info["frame_rate"] = _parse_fps(s.get("r_frame_rate"))
                video_seen = True
        elif stype == 2:
            stream.update(
                {
                    "bitrate": int(int(sbr) / 1000) if sbr else None,
                    "channels": s.get("channels"),
                    "sampling_rate": int(s["sample_rate"]) if s.get("sample_rate") else None,
                }
            )
            if not audio_seen:
                info["audio_codec"] = codec
                info["audio_channels"] = s.get("channels")
                audio_seen = True
        info["streams"].append(stream)
    return info if info["streams"] else None


def _norm_container(format_name: Optional[str]) -> Optional[str]:
    """
    归一化容器名（ffprobe 的 format_name 常是逗号分隔的候选）。

    :param format_name: ffprobe format_name
    :return: 单一容器名
    """
    if not format_name:
        return None
    first = format_name.split(",")[0].strip()
    mapping = {"matroska": "mkv", "mov": "mp4", "mpegts": "ts"}
    return mapping.get(first, first) or None


def _parse_fps(r_frame_rate: Optional[str]) -> Optional[float]:
    """
    解析 ffprobe 的 r_frame_rate（形如 '24000/1001'）为浮点帧率。

    :param r_frame_rate: 帧率字符串
    :return: 帧率浮点值
    """
    if not r_frame_rate or "/" not in r_frame_rate:
        return None
    try:
        num, den = r_frame_rate.split("/")
        den_f = float(den)
        return round(float(num) / den_f, 3) if den_f else None
    except (ValueError, ZeroDivisionError):
        return None


def _bit_depth(stream: Dict[str, Any]) -> Optional[int]:
    """
    推断视频流位深。

    :param stream: ffprobe 视频流
    :return: 位深，无法判断返回 None
    """
    bps = stream.get("bits_per_raw_sample")
    if bps:
        try:
            return int(bps)
        except ValueError:
            pass
    pix_fmt = stream.get("pix_fmt") or ""
    if "10" in pix_fmt:
        return 10
    if "12" in pix_fmt:
        return 12
    if pix_fmt:
        return 8
    return None
