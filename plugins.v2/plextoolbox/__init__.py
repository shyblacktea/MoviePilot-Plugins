"""PLEX 工具箱插件：Plex 302 反向代理 + STRM 媒体流信息补全。"""

from threading import Thread
from typing import Any, Dict, List, Optional, Tuple

from uvicorn import Config, Server

from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType

try:
    from apscheduler.triggers.cron import CronTrigger
except Exception:
    CronTrigger = None

from .proxy_app import create_app
from .emby_client import EmbyClient
from .helper_client import HelperClient
from .mediainfo import MediaInfoCompleter
from .plex_client import PlexClient


PIN_RULES_SEP = " => "


def _parse_pin_rules(raw: str) -> List[Tuple[str, str]]:
    """
    解析顶置路径规则字符串为 (路径前缀, 目标URL) 列表。

    :param raw: 多行文本，每行「路径前缀 => 目标URL」
    :return: 合法规则列表；非法行忽略并打日志
    """
    result: List[Tuple[str, str]] = []
    for line in (raw or "").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if PIN_RULES_SEP not in line:
            logger.warning('顶置规则格式错误，已忽略: %s', line)
            continue
        parts = line.split(PIN_RULES_SEP, 1)
        path_prefix = parts[0].strip()
        target_url = parts[1].strip()
        if not path_prefix or not target_url:
            logger.warning("顶置规则路径或目标为空，已忽略: %s", line)
            continue
        if not target_url.startswith(("http://", "https://")):
            logger.warning("顶置规则目标需以 http/https 开头，已忽略: %s", line)
            continue
        result.append((path_prefix, target_url))
    return result


class PlexToolbox(_PluginBase):
    """PLEX 工具箱：302 反向代理与 STRM 媒体流信息补全。"""

    plugin_name = "PLEX 工具箱"
    plugin_desc = "Plex 302 反向代理 + STRM 媒体流信息补全（Emby/ffprobe 数据源写入 Plex 库）。"
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/refs/heads/main/icons/Plex_A.png"
    plugin_version = "0.3.0"
    plugin_author = "shyblacktea"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "plextoolbox_"
    plugin_order = 20
    auth_level = 1

    # ---- 反代配置 ----
    _enabled = False
    _proxy_enabled = False
    _plex_host = ""
    _plex_token = ""
    _host = "0.0.0.0"
    _port = 32401
    _pin_rules: List[Tuple[str, str]] = []
    _pin_rules_raw = ""
    _force_direct_play = True
    _server = None
    _thread = None

    # ---- 媒体信息补全配置 ----
    _mediainfo_enabled = False
    _plex_direct_host = ""
    _helper_url = ""
    _helper_token = ""
    _emby_url = ""
    _emby_apikey = ""
    _use_emby = True
    _use_ffprobe = True
    _overwrite_streams = True
    _only_missing = True
    _concurrency = 3
    _sections = ""
    _cron = ""
    _running = False

    def init_plugin(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化插件：解析配置，按需启动 302 代理。

        :param config: 插件配置字典
        """
        if config:
            self._enabled = config.get("enabled", False)
            # 反代
            self._proxy_enabled = config.get("proxy_enabled", False)
            self._plex_host = (config.get("plex_host") or "").strip()
            self._plex_token = (config.get("plex_token") or "").strip()
            self._host = (config.get("host") or "0.0.0.0").strip() or "0.0.0.0"
            try:
                self._port = int(config.get("port") or 32401)
            except (TypeError, ValueError):
                self._port = 32401
            self._pin_rules_raw = (config.get("pin_rules") or "").strip()
            self._pin_rules = _parse_pin_rules(self._pin_rules_raw)
            self._force_direct_play = config.get("force_direct_play", True)
            # 媒体信息补全
            self._mediainfo_enabled = config.get("mediainfo_enabled", False)
            self._plex_direct_host = (config.get("plex_direct_host") or "").strip()
            self._helper_url = (config.get("helper_url") or "").strip()
            self._helper_token = (config.get("helper_token") or "").strip()
            self._emby_url = (config.get("emby_url") or "").strip()
            self._emby_apikey = (config.get("emby_apikey") or "").strip()
            self._use_emby = config.get("use_emby", True)
            self._use_ffprobe = config.get("use_ffprobe", True)
            self._overwrite_streams = config.get("overwrite_streams", True)
            self._only_missing = config.get("only_missing", True)
            try:
                self._concurrency = int(config.get("concurrency") or 3)
            except (TypeError, ValueError):
                self._concurrency = 3
            self._sections = (config.get("sections") or "").strip()
            self._cron = (config.get("cron") or "").strip()
            self._update_config()

        self.stop_service()
        self._start_proxy()

    def _start_proxy(self) -> None:
        """按配置启动 302 反向代理服务。"""
        if not (self._enabled and self._proxy_enabled and self._plex_host):
            if self._enabled and self._proxy_enabled and not self._plex_host:
                logger.warning("PlexToolbox 反代已启用但未配置 Plex 地址")
            return
        if not self._plex_host.startswith(("http://", "https://")):
            self._plex_host = "http://" + self._plex_host
        app = create_app(
            self._plex_host,
            plex_token=self._plex_token,
            pin_rules=self._pin_rules,
            force_direct_play=self._force_direct_play,
        )
        try:
            uv_config = Config(app=app, host=self._host, port=self._port, log_config=None)
            self._server = Server(uv_config)
            self._thread = Thread(target=self._server.run, daemon=True)
            self._thread.start()
            logger.info(
                "PlexToolbox 302 代理已启动: %s:%s -> %s",
                self._host, self._port, self._plex_host,
            )
        except Exception as e:
            logger.error("PlexToolbox 代理启动失败: %s", e, exc_info=True)
            self._server = None
            self._thread = None

    def _update_config(self) -> None:
        """将当前配置写回插件配置存储。"""
        self.update_config(
            {
                "enabled": self._enabled,
                "proxy_enabled": self._proxy_enabled,
                "plex_host": self._plex_host,
                "plex_token": self._plex_token,
                "host": self._host,
                "port": self._port,
                "pin_rules": self._pin_rules_raw,
                "force_direct_play": self._force_direct_play,
                "mediainfo_enabled": self._mediainfo_enabled,
                "plex_direct_host": self._plex_direct_host,
                "helper_url": self._helper_url,
                "helper_token": self._helper_token,
                "emby_url": self._emby_url,
                "emby_apikey": self._emby_apikey,
                "use_emby": self._use_emby,
                "use_ffprobe": self._use_ffprobe,
                "overwrite_streams": self._overwrite_streams,
                "only_missing": self._only_missing,
                "concurrency": self._concurrency,
                "sections": self._sections,
                "cron": self._cron,
            }
        )

    def _build_completer(self, force_write: bool = False) -> Optional[MediaInfoCompleter]:
        """
        根据配置构建媒体信息补全器。

        :param force_write: 是否忽略 Plex 繁忙强制写入
        :return: 补全器实例，配置不全返回 None
        """
        plex_host = self._plex_direct_host or self._plex_host
        if not plex_host or not self._plex_token:
            logger.warning("PlexToolbox 补全缺少 Plex 直连地址或 token")
            return None
        if not self._helper_url:
            logger.warning("PlexToolbox 补全缺少 helper 地址")
            return None
        if not plex_host.startswith(("http://", "https://")):
            plex_host = "http://" + plex_host
        plex = PlexClient(plex_host, self._plex_token)
        helper = HelperClient(self._helper_url, self._helper_token)
        emby = None
        if self._use_emby and self._emby_url and self._emby_apikey:
            emby = EmbyClient(self._emby_url, self._emby_apikey)
        return MediaInfoCompleter(
            plex=plex,
            helper=helper,
            emby=emby,
            use_emby=self._use_emby,
            use_ffprobe=self._use_ffprobe,
            overwrite_streams=self._overwrite_streams,
            concurrency=self._concurrency,
            force_write=force_write,
        )

    def run_completion(
        self, source: str = "manual", force_write: bool = False,
        section_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        执行媒体信息补全流程并持久化最近结果。

        :param source: 触发来源（manual/schedule/api）
        :param force_write: 是否忽略 Plex 繁忙强制写入
        :param section_keys: 指定分区 key；缺省用配置中的 sections
        :return: 汇总结果
        """
        if self._running:
            return {"success": False, "error": "已有补全任务在运行"}
        completer = self._build_completer(force_write=force_write)
        if not completer:
            return {"success": False, "error": "补全配置不完整"}
        keys = section_keys or [
            s.strip() for s in self._sections.split(",") if s.strip()
        ]
        if not keys:
            return {"success": False, "error": "未指定要处理的 Plex 媒体库"}
        self._running = True
        try:
            summary = completer.run(keys, only_missing=self._only_missing)
            summary["success"] = True
            summary["source"] = source
            self.save_data("last_result", summary)
            logger.info("PlexToolbox 补全完成: %s", summary)
            return summary
        except Exception as e:
            logger.error("PlexToolbox 补全异常: %s", e, exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            self._running = False

    def get_state(self) -> bool:
        """返回插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """声明使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。"""
        return [
            {
                "cmd": "/ptbox",
                "event": EventType.PluginAction,
                "desc": "PLEX 工具箱媒体信息补全",
                "category": "PLEX 工具箱",
                "data": {"action": "plextoolbox_complete"},
            }
        ]

    def get_service(self) -> List[Dict[str, Any]]:
        """返回定时补全服务。"""
        if not (self._enabled and self._mediainfo_enabled and self._cron):
            return []
        trigger = self._cron
        if CronTrigger:
            try:
                trigger = CronTrigger.from_crontab(self._cron)
            except Exception as exc:
                logger.warning("PlexToolbox Cron 无效，跳过定时: %s", exc)
                return []
        return [
            {
                "id": "plextoolbox_complete",
                "name": "PLEX 工具箱媒体信息补全",
                "trigger": trigger,
                "func": self.run_completion,
                "kwargs": {"source": "schedule"},
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件前端调用的 API 列表。"""
        return [
            {"path": "/status", "endpoint": self.status_api, "methods": ["GET"], "auth": "bear", "summary": "工具箱状态"},
            {"path": "/sections", "endpoint": self.sections_api, "methods": ["GET"], "auth": "bear", "summary": "获取 Plex 媒体库"},
            {"path": "/helper_check", "endpoint": self.helper_check_api, "methods": ["GET"], "auth": "bear", "summary": "检查 helper 连通与数据库"},
            {"path": "/complete", "endpoint": self.complete_api, "methods": ["POST"], "auth": "bear", "summary": "手动触发媒体信息补全"},
            {"path": "/result", "endpoint": self.result_api, "methods": ["GET"], "auth": "bear", "summary": "获取最近补全结果"},
        ]

    def status_api(self) -> Dict[str, Any]:
        """返回工具箱运行状态与配置概要。"""
        return {
            "success": True,
            "enabled": self._enabled,
            "proxy_enabled": self._proxy_enabled,
            "proxy_running": self._server is not None,
            "mediainfo_enabled": self._mediainfo_enabled,
            "running": self._running,
            "use_emby": self._use_emby,
            "use_ffprobe": self._use_ffprobe,
        }

    def sections_api(self) -> Dict[str, Any]:
        """获取 Plex 媒体库分区列表，供前端勾选。"""
        plex_host = self._plex_direct_host or self._plex_host
        if not plex_host or not self._plex_token:
            return {"success": False, "error": "未配置 Plex 直连地址或 token", "sections": []}
        if not plex_host.startswith(("http://", "https://")):
            plex_host = "http://" + plex_host
        try:
            sections = PlexClient(plex_host, self._plex_token).list_sections()
            return {"success": True, "sections": sections}
        except Exception as e:
            return {"success": False, "error": str(e), "sections": []}

    def helper_check_api(self) -> Dict[str, Any]:
        """检查 helper 连通性与数据库探测结果。"""
        if not self._helper_url:
            return {"success": False, "error": "未配置 helper 地址"}
        client = HelperClient(self._helper_url, self._helper_token)
        if not client.health():
            return {"success": False, "error": "helper 不可达"}
        info = client.dbinfo()
        return {"success": True, "health": True, "dbinfo": info}

    def complete_api(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """手动触发媒体信息补全。"""
        payload = payload or {}
        keys = payload.get("sections")
        force = bool(payload.get("force"))
        return self.run_completion(source="api", force_write=force, section_keys=keys)

    def result_api(self) -> Dict[str, Any]:
        """获取最近一次补全结果。"""
        return {"success": True, "result": self.get_data("last_result") or {}}

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """Vue 模式下返回默认配置模型。"""
        return None, {
            "enabled": self._enabled,
            "proxy_enabled": self._proxy_enabled,
            "plex_host": self._plex_host,
            "plex_token": self._plex_token,
            "host": self._host,
            "port": self._port,
            "pin_rules": self._pin_rules_raw,
            "force_direct_play": self._force_direct_play,
            "mediainfo_enabled": self._mediainfo_enabled,
            "plex_direct_host": self._plex_direct_host,
            "helper_url": self._helper_url,
            "helper_token": self._helper_token,
            "emby_url": self._emby_url,
            "emby_apikey": self._emby_apikey,
            "use_emby": self._use_emby,
            "use_ffprobe": self._use_ffprobe,
            "overwrite_streams": self._overwrite_streams,
            "only_missing": self._only_missing,
            "concurrency": self._concurrency,
            "sections": self._sections,
            "cron": self._cron,
        }

    def get_page(self) -> Optional[List[dict]]:
        """Vue 模式下详情页由远程组件渲染。"""
        return None

    def stop_service(self) -> None:
        """停止代理服务并释放资源。"""
        if self._server is not None:
            try:
                self._server.should_exit = True
                if self._thread is not None and self._thread.is_alive():
                    self._thread.join(timeout=5.0)
                logger.info("PlexToolbox 302 代理已停止")
            except Exception as e:
                logger.error("PlexToolbox 停止异常: %s", e, exc_info=True)
            finally:
                self._server = None
                self._thread = None
