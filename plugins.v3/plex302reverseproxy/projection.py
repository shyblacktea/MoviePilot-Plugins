"""纯响应式媒体流信息投影：只补 Plex 缺失字段，不写 Plex 数据库。

设计照搬 InfinityPacer/plex-gateway 的响应投影思路（零副作用路线）：
- 只补缺失，绝不覆盖 Plex 已有值；
- 绝不伪造 Plex Stream ID / default / selected（客户端依赖这些选择音轨）；
- Plex 已物化（Stream 均带正数 id）时视为无需补全，直接透传；
- 只对单一 Media 单一 Part 的 STRM 条目生效；
- 任何异常一律 fail-open，返回原始响应。
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from collections import OrderedDict
from time import monotonic
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.sdk.logging import logger

# ---------- 投影白名单（照抄 plex-gateway 的常量表） ----------

# Media 层：internal 字段名 -> Plex 响应字段名
MEDIA_FIELDS: Dict[str, str] = {
    "container": "container",
    "duration": "duration",
    "bitrate": "bitrate",
    "width": "width",
    "height": "height",
    "aspect_ratio": "aspectRatio",
    "audio_channels": "audioChannels",
    "audio_codec": "audioCodec",
    "video_codec": "videoCodec",
    "video_resolution": "videoResolution",
    "video_frame_rate": "videoFrameRate",
    "video_profile": "videoProfile",
    "audio_profile": "audioProfile",
}

# Part 层白名单
PART_FIELDS: Dict[str, str] = {
    "duration": "duration",
    "size": "size",
    "container": "container",
    "video_profile": "videoProfile",
    "audio_profile": "audioProfile",
}

# Stream 公共字段
STREAM_COMMON: Dict[str, str] = {
    "codec": "codec",
    "profile": "profile",
    "level": "level",
    "bitrate": "bitrate",
    "language": "languageCode",
    "title": "title",
}

# 视频流追加字段
STREAM_VIDEO: Dict[str, str] = {
    "width": "width",
    "height": "height",
    "frame_rate": "frameRate",
    "ref_frames": "refFrames",
    "pixel_format": "pixelFormat",
    "bit_depth": "bitDepth",
    "color_space": "colorSpace",
    "color_range": "colorRange",
    "color_primaries": "colorPrimaries",
    "color_trc": "colorTrc",
    "chroma_location": "chromaLocation",
    "sample_aspect_ratio": "sampleAspectRatio",
    "display_aspect_ratio": "displayAspectRatio",
    "display_title": "displayTitle",
}

# 音频流追加字段
STREAM_AUDIO: Dict[str, str] = {
    "sampling_rate": "samplingRate",
    "channels": "channels",
    "audio_channel_layout": "audioChannelLayout",
    "display_title": "displayTitle",
}

# Dolby Vision 字段（HDR/DV 片源的技术标识）
STREAM_DOVI: Dict[str, str] = {
    "dovi_bl_compat_id": "DOVIBLCompatID",
    "dovi_bl_present": "DOVIBLPresent",
    "dovi_el_present": "DOVIELPresent",
    "dovi_level": "DOVILevel",
    "dovi_present": "DOVIPresent",
    "dovi_profile": "DOVIProfile",
    "dovi_rpu_present": "DOVIRPUPresent",
    "dovi_version": "DOVIVersion",
}

# STRM 控制文件大小阈值：Part.size <= 1MiB 且是 .strm 时，视为"控制文件占位大小"，需要纠正
STRM_CONTROL_SIZE_THRESHOLD = 1 << 20

# 响应体上限（超过则放弃解析，直接透传）
MAX_BODY_BYTES = 8 * 1024 * 1024


def streams_are_plex_materialized(streams: List[Dict[str, Any]]) -> bool:
    """
    判断 Plex 的 Stream 是否已由 Plex 数据模型物化。

    判据（照搬 plex-gateway）：每个 Stream 都有 streamType + index，且 id 为正整数。
    满足即认为无需补全——language/title 等可选描述字段缺失不触发二次探测。

    :param streams: Plex 响应中的 Stream 列表
    :return: True 表示已物化，应字节级透传
    """
    if not streams:
        return False
    for s in streams:
        if not isinstance(s, dict):
            return False
        if not s.get("streamType") or s.get("index") is None:
            return False
        try:
            if int(s.get("id") or 0) <= 0:
                return False
        except (TypeError, ValueError):
            return False
    return True


def strm_part_size_needs_correction(part: Dict[str, Any]) -> bool:
    """
    判断 .strm Part 的 size 是否是"控制文件大小"需要纠正。

    :param part: Plex Part 对象
    :return: True 表示 size 需要被真实大小替换
    """
    f = part.get("file") or ""
    if not isinstance(f, str) or not f.lower().endswith(".strm"):
        return False
    size = part.get("size")
    if size is None:
        return False
    try:
        value = int(size)
    except (TypeError, ValueError):
        return False
    return 0 <= value <= STRM_CONTROL_SIZE_THRESHOLD


def _missing_stream_field(
    streams: List[Dict[str, Any]], keys: Tuple[str, ...]
) -> bool:
    """
    判断给定 Stream 集合是否缺少任一白名单字段（任一缺失即视为需要补全）。

    :param streams: Plex Stream 列表
    :param keys: 需要检查的 Plex 字段名
    :return: True 表示存在缺失
    """
    for s in streams:
        if not isinstance(s, dict):
            continue
        for key in keys:
            if key not in s:
                return True
    return False


def needs_enrichment(media: Dict[str, Any], part: Dict[str, Any]) -> bool:
    """
    判断该 Media/Part 是否需要投影补全。

    顺序（照搬 plex-gateway 的 needs_enrichment）：
    1) Media/Part 白名单字段有缺失 -> 需要；
    2) .strm 的 Part.size 是控制文件大小 -> 需要；
    3) Stream 为空 -> 需要；
    4) Stream 已被 Plex 物化（都有正数 id）-> 不需要（关键短路，省掉无效 ffprobe）；
    5) Stream 公共/类型字段有缺失 -> 需要。

    :param media: Plex Media 对象
    :param part: Plex Part 对象
    :return: True 表示需要补全
    """
    streams = part.get("Stream") or []
    if isinstance(streams, list) and streams_are_plex_materialized(streams):
        # 关键短路：Plex 已持有完整流身份（含正数 Stream ID）。
        # 此时 Media/Part 描述字段即便缺失也不值得再打一次 CDN ffprobe，
        # 因为缺的只是展示性字段，不会影响播放与音轨选择。
        return False

    for key in MEDIA_FIELDS.values():
        if key not in media:
            return True
    for key in PART_FIELDS.values():
        if key not in part:
            return True
    if strm_part_size_needs_correction(part):
        return True

    if not isinstance(streams, list) or len(streams) == 0:
        return True

    for s in streams:
        if not isinstance(s, dict):
            continue
        stype = str(s.get("streamType") or "")
        keys = list(STREAM_COMMON.values())
        if stype == "1":
            keys += list(STREAM_VIDEO.values()) + list(STREAM_DOVI.values())
        elif stype == "2":
            keys += list(STREAM_AUDIO.values())
        if _missing_stream_field([s], tuple(keys)):
            return True
    return False


def select_single_strm_target(
    body: Any,
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    从 Plex JSON 响应中选出唯一的 (Media, Part) 目标。

    仅当响应恰好含一个 Metadata 项、该项恰好一个 Media、该 Media 恰好一个 Part，
    且该 Part 指向 .strm 文件时才返回。

    :param body: 已解析的 JSON 响应体
    :return: (media, part) 元组，不适用返回 None
    """
    if not isinstance(body, dict):
        return None
    items = (body.get("MediaContainer") or {}).get("Metadata") or []
    if not isinstance(items, list) or len(items) != 1:
        return None
    media_list = items[0].get("Media") or []
    if not isinstance(media_list, list) or len(media_list) != 1:
        return None
    media = media_list[0]
    part_list = media.get("Part") or []
    if not isinstance(part_list, list) or len(part_list) != 1:
        return None
    part = part_list[0]
    file_path = part.get("file")
    if not isinstance(file_path, str) or not file_path.lower().endswith(".strm"):
        return None
    return media, part


def _apply_missing(
    target: Dict[str, Any], info: Dict[str, Any], mapping: Dict[str, str]
) -> bool:
    """
    把 info 中的值按 mapping 写入 target 的缺失字段。

    :param target: 目标对象（Media 或 Part 或 Stream）
    :param info: 探测结果（内部字段名）
    :param mapping: 内部字段名 -> Plex 字段名
    :return: True 表示发生了写入
    """
    changed = False
    for source, plex_key in mapping.items():
        if plex_key in target:
            continue  # 绝不覆盖 Plex 已有值
        value = info.get(source)
        if value is None or value == "" or value == 0:
            continue
        target[plex_key] = value
        changed = True
    return changed


def project_response(
    body: Any, info: Dict[str, Any]
) -> Tuple[bool, Optional[Any]]:
    """
    对已解析的 Plex JSON 响应执行投影。

    规则：
    - Media/Part 只补缺失字段；
    - Stream 只按 (streamType, index) 匹配已有行补缺失字段；
    - 仅当 Part 完全没有 Stream 时，才构造描述性 Stream（只写 streamType/index + 白名单
      描述字段，绝不写 id/default/selected/decision）；
    - .strm 且 size <= 1MiB 时用真实 size 纠正。

    :param body: 已解析的 JSON 响应体
    :param info: ffprobe 探测结果
    :return: (是否发生改动, 改动后的响应体)
    """
    target = select_single_strm_target(body)
    if not target:
        return False, body
    media, part = target

    media_info = info.get("media") or {}
    part_info = info.get("part") or {}
    streams_info = info.get("streams") or []

    changed = False
    if _apply_missing(media, media_info, MEDIA_FIELDS):
        changed = True
    if _apply_missing(part, part_info, PART_FIELDS):
        changed = True

    # .strm 控制文件大小纠正：仅在当前 size 处于控制阈值内且真实 size 更大时替换
    if strm_part_size_needs_correction(part):
        real_size = part_info.get("size")
        try:
            real = int(real_size) if real_size is not None else 0
        except (TypeError, ValueError):
            real = 0
        if real > 0 and real > int(part.get("size") or 0):
            part["size"] = real
            changed = True

    existing = part.get("Stream")
    if not isinstance(existing, list) or len(existing) == 0:
        # Part 完全没有 Stream：构造描述性行，但不写任何 Plex 拥有的身份/选择状态
        generated: List[Dict[str, Any]] = []
        for s in streams_info:
            stype = s.get("stream_type")
            if stype not in (1, 2, 3):
                continue
            row: Dict[str, Any] = {"streamType": str(stype), "index": s.get("index")}
            mapping = dict(STREAM_COMMON)
            if stype == 1:
                mapping.update(STREAM_VIDEO)
                mapping.update(STREAM_DOVI)
            elif stype == 2:
                mapping.update(STREAM_AUDIO)
            for source, plex_key in mapping.items():
                value = s.get(source)
                if value is None or value == "" or value == 0:
                    continue
                if plex_key not in row:
                    row[plex_key] = value
            generated.append(row)
        if generated:
            part["Stream"] = generated
            changed = True
    else:
        # Plex 已有 Stream：只对 identity 匹配的行补缺失字段，不新增、不删除、不改 id
        by_identity: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for row in existing:
            if not isinstance(row, dict):
                continue
            key = (str(row.get("streamType") or ""), str(row.get("index")))
            by_identity.setdefault(key, row)
        for s in streams_info:
            stype = s.get("stream_type")
            if stype not in (1, 2, 3):
                continue
            key = (str(stype), str(s.get("index")))
            row = by_identity.get(key)
            if not row:
                continue
            mapping = dict(STREAM_COMMON)
            if stype == 1:
                mapping.update(STREAM_VIDEO)
                mapping.update(STREAM_DOVI)
            elif stype == 2:
                mapping.update(STREAM_AUDIO)
            if _apply_missing(row, s, mapping):
                changed = True

    return changed, body


# ---------- ffprobe 探测 ----------


def read_strm_target(path: str) -> str:
    """
    读取本地 STRM 文件里的第一条 HTTP(S) 地址。

    :param path: STRM 文件路径
    :return: 直链，读取失败返回空串
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            first = (handle.read().strip().splitlines() or [""])[0].strip()
        return first if first.startswith(("http://", "https://")) else ""
    except (OSError, IndexError):
        return ""


def _probe_remote_size(url: str, user_agent: str = "") -> int:
    """
    用 `Range: bytes=0-0` 探测远程文件总大小（照搬 plex-gateway 的兜底）。

    约束：独立连接、2 秒超时、不跟随重定向、只接受 206、从 Content-Range 解析，
    绝不读取响应体。失败返回 0，不影响其他字段。

    :param url: 媒体直链
    :return: 总字节数，失败返回 0
    """
    import http.client
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return 0
    conn = None
    try:
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        if parts.scheme == "https":
            conn = http.client.HTTPSConnection(parts.netloc, timeout=2)
        else:
            conn = http.client.HTTPConnection(parts.netloc, timeout=2)
        headers = {"Range": "bytes=0-0", "Accept-Encoding": "identity"}
        if user_agent:
            headers["User-Agent"] = user_agent
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        if resp.status != 206:
            return 0
        content_range = resp.getheader("Content-Range") or ""
        # 形如 bytes 0-0/12345678
        if "/" in content_range:
            total = content_range.rsplit("/", 1)[-1].strip()
            if total.isdigit():
                return int(total)
        return 0
    except Exception:
        return 0
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _fps(value: Any) -> Optional[str]:
    """
    把 ffprobe 的帧率分数（"24000/1001"）转成 Plex 需要的字符串。

    :param value: ffprobe 原始帧率
    :return: 形如 "23.976" 的字符串，无法解析返回 None
    """
    if value in (None, ""):
        return None
    try:
        text = str(value)
        if "/" in text:
            num, den = text.split("/", 1)
            d = float(den)
            if d == 0:
                return None
            return f"{float(num) / d:.3f}".rstrip("0").rstrip(".")
        return f"{float(text):.3f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return None


def _dovi_to_fields(side_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    从 ffprobe 的 side_data_list 提取 Dolby Vision 字段。

    :param side_data: ffprobe 流的 side_data_list
    :return: DOVI* 字段字典
    """
    out: Dict[str, Any] = {}
    for item in side_data or []:
        if not isinstance(item, dict):
            continue
        if "DOVI" not in str(item.get("side_data_type") or ""):
            continue
        out["dovi_present"] = 1
        profile = item.get("dv_profile")
        if profile is not None:
            out["dovi_profile"] = profile
        level = item.get("dv_level")
        if level is not None:
            out["dovi_level"] = level
        bl = item.get("dv_bl_signal_compatibility_id")
        if bl is not None:
            out["dovi_bl_compat_id"] = bl
            out["dovi_bl_present"] = 1
        if item.get("rpu_present_flag") is not None:
            out["dovi_rpu_present"] = int(item["rpu_present_flag"])
        if item.get("el_present_flag") is not None:
            out["dovi_el_present"] = int(item["el_present_flag"])
        if item.get("dv_version") is not None:
            out["dovi_version"] = item["dv_version"]
        break
    return out


def ffprobe_media(url: str, timeout: int = 20) -> Optional[Dict[str, Any]]:
    """
    对媒体直链执行受限 ffprobe，返回投影所需的归一化结构。

    :param url: 媒体直链
    :param timeout: 超时秒数
    :return: {"media": {...}, "part": {...}, "streams": [...]}，失败返回 None
    """
    if not url or urlparse(url).scheme not in ("http", "https"):
        return None
    command = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams",
        "-probesize", "8388608", "-analyzeduration", "5000000", url,
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
        if result.returncode != 0:
            return None
        raw = json.loads(result.stdout or "{}")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        logger.debug("Plex302ReverseProxy ffprobe 失败: %s", exc)
        return None

    fmt = raw.get("format") or {}
    container = (fmt.get("format_name") or "").split(",")[0]
    container = {"matroska": "mkv", "mov": "mp4"}.get(container, container)

    duration_ms = None
    if fmt.get("duration"):
        try:
            duration_ms = int(float(fmt["duration"]) * 1000)
        except (TypeError, ValueError):
            pass
    bitrate = None
    if fmt.get("bit_rate"):
        try:
            bitrate = int(int(fmt["bit_rate"]) / 1000)
        except (TypeError, ValueError):
            pass
    size = None
    if fmt.get("size"):
        try:
            size = int(fmt["size"])
        except (TypeError, ValueError):
            pass
    if not size:
        # 兜底：ffprobe 拿不到总大小时用 Range 探测（这正是 Part.size 的来源）
        size = _probe_remote_size(url) or None

    streams_out: List[Dict[str, Any]] = []
    first_video: Optional[Dict[str, Any]] = None
    first_audio: Optional[Dict[str, Any]] = None
    for item in raw.get("streams") or []:
        ctype = item.get("codec_type")
        stype = {"video": 1, "audio": 2, "subtitle": 3}.get(ctype)
        if not stype:
            continue
        tags = item.get("tags") or {}
        row: Dict[str, Any] = {
            "stream_type": stype,
            "index": item.get("index"),
            "codec": item.get("codec_name"),
            "profile": item.get("profile"),
            "level": item.get("level"),
            "language": tags.get("language"),
            "title": tags.get("title"),
        }
        if item.get("bit_rate"):
            try:
                row["bitrate"] = int(int(item["bit_rate"]) / 1000)
            except (TypeError, ValueError):
                pass
        if stype == 1:
            row.update(
                {
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "frame_rate": _fps(item.get("r_frame_rate")),
                    "ref_frames": item.get("refs"),
                    "pixel_format": item.get("pix_fmt"),
                    "bit_depth": item.get("bits_per_raw_sample")
                    or item.get("bits_per_sample"),
                    "color_space": item.get("color_space"),
                    "color_range": item.get("color_range"),
                    "color_primaries": item.get("color_primaries"),
                    "color_trc": item.get("color_transfer"),
                    "chroma_location": item.get("chroma_location"),
                    "sample_aspect_ratio": item.get("sample_aspect_ratio"),
                    "display_aspect_ratio": item.get("display_aspect_ratio"),
                }
            )
            row.update(_dovi_to_fields(item.get("side_data_list") or []))
            first_video = first_video or item
        elif stype == 2:
            row.update(
                {
                    "channels": item.get("channels"),
                    "sampling_rate": item.get("sample_rate"),
                    "audio_channel_layout": item.get("channel_layout"),
                }
            )
            first_audio = first_audio or item
        streams_out.append(row)

    if not streams_out:
        return None

    media_info: Dict[str, Any] = {
        "container": container or None,
        "duration": duration_ms,
        "bitrate": bitrate,
        "video_codec": (first_video or {}).get("codec_name"),
        "audio_codec": (first_audio or {}).get("codec_name"),
        "audio_channels": (first_audio or {}).get("channels"),
    }
    if first_video:
        media_info.update(
            {
                "width": first_video.get("width"),
                "height": first_video.get("height"),
                "video_profile": first_video.get("profile"),
            }
        )
        fps = _fps(first_video.get("r_frame_rate"))
        if fps:
            media_info["video_frame_rate"] = fps
        height = first_video.get("height")
        width = first_video.get("width")
        if height:
            if height >= 1800:
                media_info["video_resolution"] = "4k"
            elif height >= 1000:
                media_info["video_resolution"] = "1080"
            elif height >= 700:
                media_info["video_resolution"] = "720"
            elif height >= 400:
                media_info["video_resolution"] = "480"
        if width and height:
            try:
                media_info["aspect_ratio"] = round(float(width) / float(height), 3)
            except (TypeError, ValueError, ZeroDivisionError):
                pass
    if first_audio:
        media_info["audio_profile"] = first_audio.get("profile")

    part_info: Dict[str, Any] = {
        "duration": duration_ms,
        "size": size,
        "container": container or None,
        "video_profile": (first_video or {}).get("profile"),
        "audio_profile": (first_audio or {}).get("profile"),
    }

    return {"media": media_info, "part": part_info, "streams": streams_out}


# ---------- 缓存与调度 ----------


class ProjectionCache:
    """有界内存缓存：成功记录长 TTL，失败短 TTL 退避，附单飞合并。"""

    def __init__(self, max_size: int = 1000, ttl_ok: int = 30 * 24 * 3600,
                 ttl_fail: int = 60) -> None:
        """
        初始化缓存。

        :param max_size: 最大条目数
        :param ttl_ok: 成功记录存活秒数
        :param ttl_fail: 失败记录退避秒数
        """
        self._cache: "OrderedDict[str, Tuple[float, Optional[Dict[str, Any]]]]" = (
            OrderedDict()
        )
        self._max = max(10, max_size)
        self._ttl_ok = ttl_ok
        self._ttl_fail = ttl_fail
        self._tasks: Dict[str, asyncio.Task] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        读取缓存（只返回仍在有效期内的记录）。

        :param key: 缓存键
        :return: 命中返回 info，未命中返回 None
        """
        entry = self._cache.get(key)
        if not entry:
            return None
        expiry, info = entry
        if monotonic() >= expiry:
            self._cache.pop(key, None)
            return None
        self._cache.move_to_end(key)
        return info

    def put(self, key: str, info: Optional[Dict[str, Any]]) -> None:
        """
        写入缓存并按 TTL 决定存活时长。

        :param key: 缓存键
        :param info: 探测结果，None 表示失败（短 TTL 退避）
        """
        ttl = self._ttl_ok if info else self._ttl_fail
        self._cache[key] = (monotonic() + ttl, info)
        self._cache.move_to_end(key)
        while len(self._cache) > self._max:
            self._cache.popitem(last=False)

    def negative(self, key: str) -> bool:
        """
        判断该键是否处于失败退避期。

        :param key: 缓存键
        :return: True 表示正在退避
        """
        entry = self._cache.get(key)
        if not entry:
            return False
        expiry, info = entry
        if info is not None:
            return False
        if monotonic() >= expiry:
            self._cache.pop(key, None)
            return False
        return True

    def inflight(self) -> Dict[str, asyncio.Task]:
        """
        返回进行中的探测任务表。

        :return: key -> Task
        """
        return self._tasks
