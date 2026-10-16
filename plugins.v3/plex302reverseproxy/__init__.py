from threading import Thread
from typing import Any, Dict, List, Tuple

from uvicorn import Config, Server

from app.sdk.logging import logger
from app.plugins import _PluginBase

from .proxy_app import create_app


PIN_RULES_SEP = " => "


def _parse_pin_rules(raw: str) -> List[Tuple[str, str]]:
    """
    解析顶置路径规则字符串为 (路径前缀, 目标URL) 列表

    :param raw: 多行文本，每行「路径前缀 => 目标URL」（用 " => " 分隔，两侧可含空格）
    :return: 合法规则列表；非法行忽略并打日志
    """
    result: List[Tuple[str, str]] = []
    for line in (raw or "").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if PIN_RULES_SEP not in line:
            logger.warning(
                '顶置规则格式错误，已忽略（需用 " => " 分隔路径前缀与目标URL）: %s',
                line,
            )
            continue
        parts = line.split(PIN_RULES_SEP, 1)
        path_prefix = parts[0].strip()
        target_url = parts[1].strip()
        if not path_prefix or not target_url:
            logger.warning("顶置规则路径或目标为空，已忽略: %s", line)
            continue
        if not target_url.startswith(("http://", "https://")):
            logger.warning(
                "顶置规则目标需以 http:// 或 https:// 开头，已忽略: %s => %s",
                path_prefix,
                target_url,
            )
            continue
        result.append((path_prefix, target_url))
    return result


class Plex302ReverseProxy(_PluginBase):
    """
    PLEX 302 反向代理
    """

    plugin_name = "PLEX 302 反向代理"
    plugin_desc = (
        "Plex 302 反向代理 + 纯响应式媒体流信息投影（不写 Plex 数据库）。（小k自用版）"
    )
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/refs/heads/main/icons/Plex_A.png"
    plugin_version = "1.0.0"
    plugin_version_history = {
        "1.0.0": """本人已转 MoviePilot 核心贡献者 @InfinityPacer 倾力打造的项目：Cirvel 🎬

STRM 播放永久免费

故此插件不再更新！

官网 https://cirvel.tidewren.com
频道 @cirvel_news""",
    }

    plugin_author = "shyblacktea"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "plex302reverseproxy_"
    plugin_order = 20
    auth_level = 1

    _enabled = False
    _plex_host = ""
    _plex_token = ""
    _host = "0.0.0.0"
    _port = 32401
    _pin_rules: List[Tuple[str, str]] = []
    _pin_rules_raw = ""
    _force_direct_play = True
    # ---- 响应投影（不写库）配置 ----
    _projection_enabled = False
    _projection_timeout = 20
    _projection_cold_wait = 5.0
    _projection_ttl_ok = 30 * 24 * 3600
    _projection_ttl_fail = 60
    _projection_cache_size = 1000
    _finalize_redirect = True
    _server = None
    _thread = None

    def init_plugin(self, config: Dict[str, Any] | None = None) -> None:
        """
        初始化插件：解析配置，启用时在独立线程启动 uvicorn，否则停止服务

        :param config (Dict): 插件配置字典
        """
        if config:
            self._enabled = config.get("enabled", False)
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
            # 响应投影配置
            self._projection_enabled = config.get("projection_enabled", False)
            try:
                self._projection_timeout = int(config.get("projection_timeout") or 20)
            except (TypeError, ValueError):
                self._projection_timeout = 20
            try:
                self._projection_cold_wait = float(
                    config.get("projection_cold_wait") or 5.0
                )
            except (TypeError, ValueError):
                self._projection_cold_wait = 5.0
            try:
                self._projection_cache_size = int(
                    config.get("projection_cache_size") or 1000
                )
            except (TypeError, ValueError):
                self._projection_cache_size = 1000
            self._finalize_redirect = bool(
                config.get("finalize_redirect", True)
            )
            self._update_config()

        self.stop_service()

        if self._enabled and self._plex_host:
            if not self._plex_host.startswith(("http://", "https://")):
                self._plex_host = "http://" + self._plex_host
            app = create_app(
                self._plex_host,
                plex_token=self._plex_token,
                pin_rules=self._pin_rules,
                force_direct_play=self._force_direct_play,
                projection_enabled=self._projection_enabled,
                projection_timeout=self._projection_timeout,
                projection_cold_wait=self._projection_cold_wait,
                projection_cache_size=self._projection_cache_size,
                finalize_redirect=self._finalize_redirect,
            )
            try:
                uv_config = Config(
                    app=app,
                    host=self._host,
                    port=self._port,
                    log_config=None,
                )
                self._server = Server(uv_config)
                self._thread = Thread(target=self._server.run, daemon=True)
                self._thread.start()
                logger.info(
                    "Plex302ReverseProxy 代理已启动: %s:%s -> %s",
                    self._host,
                    self._port,
                    self._plex_host,
                )
            except Exception as e:
                logger.error("Plex302ReverseProxy 启动失败: %s", e, exc_info=True)
                self._server = None
                self._thread = None
        elif self._enabled and not self._plex_host:
            logger.warning("Plex302ReverseProxy 已启用但未配置 Plex 地址，代理未启动")

    def _update_config(self) -> None:
        """
        将当前配置写回插件配置存储
        """
        self.update_config(
            {
                "enabled": self._enabled,
                "plex_host": self._plex_host,
                "plex_token": self._plex_token,
                "host": self._host,
                "port": self._port,
                "pin_rules": self._pin_rules_raw,
                "force_direct_play": self._force_direct_play,
                "projection_enabled": self._projection_enabled,
                "projection_timeout": self._projection_timeout,
                "projection_cold_wait": self._projection_cold_wait,
                "projection_cache_size": self._projection_cache_size,
                "finalize_redirect": self._finalize_redirect,
            }
        )

    def stop_service(self) -> None:
        """
        停止代理服务：设置 server.should_exit 并等待线程结束
        """
        if self._server is not None:
            try:
                self._server.should_exit = True
                if self._thread is not None and self._thread.is_alive():
                    self._thread.join(timeout=5.0)
                logger.info("Plex302ReverseProxy 代理已停止")
            except Exception as e:
                logger.error("Plex302ReverseProxy 停止异常: %s", e, exc_info=True)
            finally:
                self._server = None
                self._thread = None

    def get_state(self) -> bool:
        """
        返回插件启用状态

        :return bool: True 表示插件已启用
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        返回插件远程命令列表，本插件无远程命令

        :return List: 插件远程命令列表
        """
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        """
        返回插件 API 端点列表，本插件无自定义 API

        :return List: 空列表
        """
        return []

    def get_page(self) -> List[dict]:
        """
        返回插件数据页面配置，本插件无数据页面

        :return List: 插件数据页面配置
        """
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面

        :return Tuple: (页面配置列表, 表单默认值字典)
        """
        return [
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VSwitch",
                                "props": {
                                    "model": "enabled",
                                    "label": "启用插件",
                                    "hint": "开启后将在独立端口运行 Plex 反向代理",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VSwitch",
                                "props": {
                                    "model": "force_direct_play",
                                    "label": "强制直接播放",
                                    "hint": "改写转码决策为 DirectPlay，保证 302 直链生效",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VSwitch",
                                "props": {
                                    "model": "projection_enabled",
                                    "label": "响应投影补全（不写库）",
                                    "hint": "在 Plex 响应里补 Media/Part/Stream 字段，完全不写 Plex 数据库",
                                    "persistent-hint": True,
                                    "color": "warning",
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VSwitch",
                                "props": {
                                    "model": "finalize_redirect",
                                    "label": "展开内网中间地址",
                                    "hint": "服务端自行跟随后续跳转，直接 302 到公网直链；远程客户端（公网接入/账号登录的第三方 App）必需，否则会拿到内网地址而无法解析",
                                    "persistent-hint": True,
                                    "color": "success",
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "info",
                                    "variant": "tonal",
                                    "density": "compact",
                                    "text": "响应投影：只补 Plex 缺失的字段，绝不覆盖已有值、绝不伪造 Stream ID（客户端依赖 Stream ID 选择音轨）。Plex 已物化（Stream 均带正数 id）时直接透传，不做任何探测。",
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "projection_cold_wait",
                                    "label": "播前冷等待(秒)",
                                    "type": "number",
                                    "hint": "仅 decision 类请求同步等待探测，上限 5 秒；浏览页冷未命中立即返回",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "projection_timeout",
                                    "label": "ffprobe 超时(秒)",
                                    "type": "number",
                                    "hint": "单个直链的 ffprobe 探测超时",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 4},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "projection_cache_size",
                                    "label": "投影缓存条目数",
                                    "type": "number",
                                    "hint": "内存缓存上限（成功 30 天 / 失败 60 秒）",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "plex_host",
                                    "label": "Plex 服务器地址",
                                    "placeholder": "http://192.168.1.100:32400",
                                    "hint": "Plex 服务器根地址，必填",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 3},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "host",
                                    "label": "监听地址",
                                    "placeholder": "0.0.0.0",
                                    "hint": "代理监听地址",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 3},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "port",
                                    "label": "监听端口",
                                    "placeholder": "32401",
                                    "hint": "代理监听端口",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VTextField",
                                "props": {
                                    "model": "plex_token",
                                    "label": "X-Plex-Token（可选）",
                                    "placeholder": "留空则使用请求自带的 Token",
                                    "hint": "备用 Token：正常情况下客户端请求自带 Token，无需填写",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                ],
            },
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
                        "content": [
                            {
                                "component": "VTextarea",
                                "props": {
                                    "model": "pin_rules",
                                    "label": "顶置路径规则",
                                    "rows": 4,
                                    "placeholder": "每行一条：路径前缀 => 目标URL",
                                    "hint": "高级配置：不理解规则含义请勿配置（建议留空）。每行一条，格式：路径前缀 => 目标 URL；文件路径匹配到前缀后将替换为目标 URL 并返回 302。示例：/strm/cd2 => http://192.168.31.99:4567/d",
                                    "persistent-hint": True,
                                },
                            }
                        ],
                    },
                ],
            },
        ], {
            "enabled": False,
            "plex_host": "",
            "plex_token": "",
            "host": "0.0.0.0",
            "port": 32401,
            "pin_rules": "",
            "force_direct_play": True,
            "projection_enabled": False,
            "projection_timeout": 20,
            "projection_cold_wait": 5.0,
            "projection_cache_size": 1000,
            "finalize_redirect": True,
        }
