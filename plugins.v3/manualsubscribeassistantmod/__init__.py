"""手动订阅助手魔改版插件。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from bs4 import BeautifulSoup

from app.chain.media import MediaChain
from app.chain.subscribe import SubscribeChain
from app.domain.metainfo import MetaInfo
from app.plugins import _PluginBase
from app.sdk.config import settings
from app.sdk.logging import logger
from app.sdk.network import RequestUtils
from app.schemas.types import MediaSource, MediaType


class ManualSubscribeAssistantMod(_PluginBase):
    """聚合 Mikan 季番候选并由用户手动创建 MoviePilot 订阅。"""

    plugin_name = "手动订阅助手魔改版"
    plugin_desc = (
        "基于 Aqr-K 自动订阅助手改造的 MoviePilot V3 手动订阅工具："
        "抓取 Mikan 季番、识别 Bangumi/TMDB，并由用户点击后创建订阅。感谢 Aqr-K 原作者。"
    )
    plugin_icon = "https://raw.githubusercontent.com/Aqr-K/MoviePilot-Plugins/main/icons/Auto_Subscribe_Assistant.png"
    plugin_version = "0.0.1"
    plugin_author = "shyblacktea（基于 Aqr-K）"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "manualsubscribeassistantmod_"
    plugin_order = 26
    auth_level = 1

    def __init__(self) -> None:
        """初始化插件运行状态。"""
        super().__init__()
        self._config: Dict[str, Any] = {}
        self._enabled = False

    def init_plugin(self, config: dict = None) -> None:
        """加载配置；本插件不注册自动任务。"""
        self._config = dict(config or {})
        self._enabled = bool(self._config.get("enabled", False))

    def get_state(self) -> bool:
        """返回插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, str]:
        """声明使用 Vue 联邦页面。"""
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回 Vue 页面使用的默认配置。"""
        return [], {
            "enabled": False,
            "year": 0,
            "season": "当前",
            "resolve_bangumi": True,
            "proxy": False,
        }

    def get_page(self) -> List[dict]:
        """返回空的 Vuetify 页面，由 Vue 联邦组件负责渲染。"""
        return []

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """本插件不注册远程命令，所有操作通过页面完成。"""
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        """返回空服务，明确禁止后台自动订阅。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """返回候选抓取、手动订阅和配置接口。"""
        return [
            {"path": "/config", "endpoint": self.api_config, "methods": ["GET"], "auth": "bear", "summary": "读取手动订阅配置"},
            {"path": "/config", "endpoint": self.api_save_config, "methods": ["POST"], "auth": "bear", "summary": "保存手动订阅配置"},
            {"path": "/candidates", "endpoint": self.api_candidates, "methods": ["POST"], "auth": "bear", "summary": "抓取并识别 Mikan 候选"},
            {"path": "/subscribe", "endpoint": self.api_subscribe, "methods": ["POST"], "auth": "bear", "summary": "手动创建单条订阅"},
        ]

    def api_config(self) -> Dict[str, Any]:
        """返回当前配置。"""
        return {"code": 0, "config": self._config}

    def api_save_config(self, request: dict = None) -> Dict[str, Any]:
        """保存配置并保持无自动服务状态。"""
        body = request if isinstance(request, dict) else {}
        config = {
            "enabled": bool(body.get("enabled", False)),
            "year": self._to_int(body.get("year"), 0),
            "season": str(body.get("season") or "当前"),
            "resolve_bangumi": bool(body.get("resolve_bangumi", True)),
            "proxy": bool(body.get("proxy", False)),
        }
        self._config = config
        self._enabled = config["enabled"]
        self.update_config(config)
        return {"code": 0, "message": "保存成功；本插件不会自动创建订阅", "config": config}

    def api_candidates(self, request: dict = None) -> Dict[str, Any]:
        """抓取当前季度 Mikan 候选并尝试用 Bangumi ID 识别 TMDB。"""
        if not self._enabled:
            return {"code": 1, "message": "请先启用插件"}
        body = request if isinstance(request, dict) else {}
        year = self._to_int(body.get("year", self._config.get("year", 0)), 0)
        season = str(body.get("season") or self._config.get("season") or "当前")
        resolve_bangumi = bool(body.get("resolve_bangumi", self._config.get("resolve_bangumi", True)))
        proxy = bool(body.get("proxy", self._config.get("proxy", False)))
        actual_year = year or self._current_year()
        season_name = self._resolve_season(season)
        try:
            rows = self._fetch_mikan(actual_year, season_name, proxy)
        except Exception as exc:
            logger.warning(f"手动订阅助手抓取 Mikan 失败：{exc}")
            return {"code": 1, "message": f"抓取失败：{exc}"}
        candidates = []
        for row in rows:
            candidate = self._recognize_candidate(row, actual_year, resolve_bangumi)
            if candidate:
                candidates.append(candidate)
        self.save_data("candidates", candidates)
        return {"code": 0, "year": actual_year, "season": season_name, "list": candidates, "total": len(candidates)}

    def api_subscribe(self, request: dict = None) -> Dict[str, Any]:
        """根据用户点击的单条候选创建一个 MoviePilot 订阅。"""
        if not self._enabled:
            return {"code": 1, "message": "请先启用插件"}
        body = request if isinstance(request, dict) else {}
        candidate = body.get("candidate") if isinstance(body.get("candidate"), dict) else body
        title = str(candidate.get("title") or "").strip()
        if not title:
            return {"code": 1, "message": "缺少候选标题"}
        source = candidate.get("media_source")
        media_id = candidate.get("media_id")
        if not source or not media_id:
            return {"code": 1, "message": "候选没有可用的媒体身份，请先重新抓取识别"}
        try:
            mtype = MediaType.TV if candidate.get("type") != MediaType.MOVIE.value else MediaType.MOVIE
            season = self._to_int(body.get("season", candidate.get("season", 1)), 1) if mtype == MediaType.TV else None
            sid, message = SubscribeChain().add(
                title=title,
                year=str(candidate.get("year") or "") or None,
                mtype=mtype,
                season=season,
                media_source=MediaSource(source),
                media_id=str(media_id),
                exist_ok=True,
                username="手动订阅助手魔改版",
                message=False,
            )
        except Exception as exc:
            logger.error(f"手动创建订阅失败：{exc}")
            return {"code": 1, "message": f"创建订阅失败：{exc}"}
        if not sid:
            return {"code": 1, "message": message or "MoviePilot 未创建订阅"}
        return {"code": 0, "message": "手动订阅已创建", "subscribe_id": sid}

    def _fetch_mikan(self, year: int, season: str, use_proxy: bool) -> List[dict]:
        """抓取 Mikan 季度页面并解析番剧条目。"""
        bases = ("https://mikanani.me", "https://mikanime.tv")
        path = f"/Home/BangumiCoverFlowByDayOfWeek?year={year}&seasonStr={quote(season)}"
        last_error: Optional[Exception] = None
        for base in bases:
            try:
                response = RequestUtils(proxies=settings.PROXY if use_proxy else None, timeout=30).get_res(base + path)
                html = getattr(response, "text", "") if response is not None else ""
                if html:
                    return self._parse_mikan(html, base)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(last_error or "Mikan 没有返回内容")

    @staticmethod
    def _parse_mikan(html: str, base: str) -> List[dict]:
        """解析 Mikan 季番 HTML。"""
        soup = BeautifulSoup(html, "lxml")
        result: List[dict] = []
        seen = set()
        for group in soup.select("div.sk-bangumi"):
            week_node = group.select_one("div.row")
            week = week_node.get_text(strip=True) if week_node else ""
            for li in group.select("li"):
                marker = li.select_one("span[data-bangumiid]")
                anchor = li.select_one("a.an-text")
                if marker is None or anchor is None:
                    continue
                mikan_id = str(marker.get("data-bangumiid") or "").strip()
                title = str(anchor.get("title") or anchor.get_text(strip=True) or "").strip()
                if not mikan_id or not title or mikan_id in seen:
                    continue
                seen.add(mikan_id)
                cover = str(marker.get("data-src") or "").strip()
                if cover.startswith("/"):
                    cover = base + cover
                result.append({"title": title, "mikan_id": mikan_id, "cover": cover, "week": week})
        return result

    def _recognize_candidate(self, row: dict, year: int, resolve_bangumi: bool) -> Optional[dict]:
        """将 Mikan 条目转换成含 Bangumi/TMDB 链接的候选。"""
        title = str(row.get("title") or "").strip()
        mikan_id = self._to_int(row.get("mikan_id"), 0)
        if not title:
            return None
        result: Dict[str, Any] = {
            "title": title,
            "year": str(year),
            "type": MediaType.TV.value,
            "season": 1,
            "mikan_id": mikan_id or None,
            "bangumi_id": None,
            "tmdb_id": None,
            "media_source": None,
            "media_id": None,
            "cover": row.get("cover"),
            "week": row.get("week"),
            "bangumi_url": f"https://bgm.tv/subject/{mikan_id}" if mikan_id else "",
            "tmdb_url": "",
        }
        if not resolve_bangumi or not mikan_id:
            return result
        detail = self._fetch_mikan_detail(mikan_id)
        bangumi_id = self._to_int(detail.get("bangumi_id"), 0)
        result["bangumi_id"] = bangumi_id or None
        if bangumi_id:
            result["bangumi_url"] = f"https://bgm.tv/subject/{bangumi_id}"
            try:
                meta = MetaInfo(title)
                meta.year = str(detail.get("year") or year)
                info = MediaChain().recognize_media(
                    meta=meta,
                    mtype=MediaType.TV,
                    media_source=MediaSource.Bangumi,
                    media_id=str(bangumi_id),
                )
                if info:
                    result["title"] = info.title or title
                    result["year"] = info.year or result["year"]
                    result["tmdb_id"] = info.tmdb_id
                    result["media_source"] = MediaSource.TMDB.value if info.tmdb_id else MediaSource.Bangumi.value
                    result["media_id"] = str(info.tmdb_id) if info.tmdb_id else str(bangumi_id)
                    if info.tmdb_id:
                        result["tmdb_url"] = f"https://www.themoviedb.org/tv/{info.tmdb_id}?language=zh-CN"
            except Exception as exc:
                logger.warning(f"Bangumi 识别 TMDB 失败：{title}：{exc}")
        return result

    def _fetch_mikan_detail(self, mikan_id: int) -> dict:
        """抓取 Mikan 详情并解析 Bangumi subject ID。"""
        bases = ("https://mikanani.me", "https://mikanime.tv")
        pattern = re.compile(r"b(?:gm|angumi)\.tv/subject/(\d+)")
        for base in bases:
            try:
                response = RequestUtils(proxies=settings.PROXY if self._config.get("proxy") else None, timeout=30).get_res(f"{base}/Home/Bangumi/{mikan_id}")
                html = getattr(response, "text", "") if response is not None else ""
                soup = BeautifulSoup(html, "lxml")
                nodes = soup.select("p.bangumi-info") or soup.select(".bangumi-info")
                search_text = "\n".join(node.get_text(" ", strip=True) for node in nodes) if nodes else html
                match = pattern.search(search_text)
                if match:
                    info = {}
                    for node in nodes:
                        text = node.get_text(" ", strip=True)
                        if "：" in text:
                            key, _, value = text.partition("：")
                            if key.strip() and value.strip():
                                info[key.strip()] = value.strip()
                    year_match = re.search(r"(19|20)\d{2}", info.get("放送开始", ""))
                    if not year_match:
                        year_match = re.search(r"(19|20)\d{2}", html)
                    return {"bangumi_id": int(match.group(1)), "year": year_match.group(0) if year_match else None}
            except Exception:
                continue
        return {}

    @staticmethod
    def _resolve_season(value: str) -> str:
        """把当前季度转换为 Mikan 使用的中文季度。"""
        if value in ("春", "夏", "秋", "冬"):
            return value
        month = __import__("datetime").datetime.now().month
        return "冬" if month in (1, 2, 12) else "春" if month in (3, 4, 5) else "夏" if month in (6, 7, 8) else "秋"

    @staticmethod
    def _current_year() -> int:
        """返回当前年份。"""
        from datetime import datetime
        return datetime.now().year

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        """安全转换整数。"""
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def stop_service(self) -> None:
        """停止插件服务；本插件没有后台线程。"""
        return None


ManualSubscribeAssistantMod.__module__ = "app.plugins.manualsubscribeassistantmod"

__all__ = ["ManualSubscribeAssistantMod"]
