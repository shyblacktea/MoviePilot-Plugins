import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import File
from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.sdk.cache import cached
from app.sdk.config import settings
from app.sdk.media import MediaInfo, MetaBase
from app.sdk.logging import logger
from app.plugins import _PluginBase
from app.sdk.network import RequestUtils
from app.sdk.utilities import SystemUtils

from .engine import MetaCorrectionUseCase
from .log_output import classify_service_line
from .patch import MonkeyPatchManager


class CureTMDbAnimeShyConfig(BaseModel):
    # 启用插件
    enabled: bool = Field(default=False)
    # Bangumi API 地址
    bangumi_api_url: str = Field(
        default="https://api.bgm.tv",
    )
    # Bangumi API 是否使用代理
    bangumi_use_proxy: bool = Field(default=True)
    # 启用元数据修正
    enable_correction: bool = Field(default=True)
    # 当标题默认解析为 S01 时，按发布时间匹配 TMDB 季播出窗口推断季号
    assume_season_by_window: bool = Field(default=False)
    # 最新季允许的越界宽限集数
    grace_episodes: int = Field(default=2, ge=0, le=5)
    # 改写所需的最小总分优势（避免噪声触发改写）
    rewrite_threshold: int = Field(default=16, ge=0, le=40)
    # 远程数据源地址
    source: Optional[str] = Field(
        default="https://raw.githubusercontent.com/wikrin/CureTMDb/main/tv.json",
    )
    # 设置了来源时，优先使用来源的分季定义（覆盖 TMDB/TVDB 推导结果）
    prefer_source_season: bool = Field(default=True)
    # 运行端口
    port: int = Field(default=8632, ge=1024, le=65535)


class CureTMDbAnimeShy(_PluginBase):
    # 插件名称
    plugin_name = "CTMDbA魔改版"
    # 插件描述
    plugin_desc = "对 TMDb 上被合并为一季的番剧进行季信息分离，优先使用 TVDB 拆分依据。（小k自用版）"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/shyblacktea/MoviePilot-Plugins/main/icons/curetmdbanimeshy.png"
    # 插件版本
    plugin_version = "0.0.5"
    # 插件作者
    plugin_author = "Attente,shyblacktea"
    # 作者主页
    author_url = "https://github.com/shyblacktea"
    # 插件配置项ID前缀
    plugin_config_prefix = "curetmdbanimeshy_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1
    # 二进制文件
    binary_name = "curetmdbanime"
    # 二进制文件版本
    binary_version = "1.4.0"
    # 二进制下载仓库（二进制仍由原作者 wikrin 编译分发）
    binary_repo = "https://github.com/wikrin"

    def __init__(self):
        super().__init__()
        self.config = CureTMDbAnimeShyConfig()
        self.patch_manager = MonkeyPatchManager()
        self._thread: Optional[threading.Thread] = None
        self._event: threading.Event = threading.Event()
        self._process: Optional[Any] = None
        self._process_lock = threading.Lock()
        # 来源分季定义缓存：{tmdb_id: [{"season_number": int, "name": str, "episode_count": int}, ...]}
        self._source_seasons: Dict[str, List[Dict[str, Any]]] = {}
        self._source_seasons_url: Optional[str] = None

    def init_plugin(self, config: dict = None):
        # 停止现有任务
        if not self.stop_service():
            logger.error("CureTMDbAnimeShy 旧服务未能停止，取消重复启动。")
            return
        # 加载插件配置
        self.load_config(config)

        # 重置来源分季定义缓存，确保按最新配置重新加载
        self._source_seasons = {}
        self._source_seasons_url = None

        if not self.config.enabled:
            return

        # 初始化
        self.meta_correction_use_case = MetaCorrectionUseCase(
            grace_episodes=self.config.grace_episodes,
            rewrite_threshold=self.config.rewrite_threshold,
            assume_season_by_window=self.config.assume_season_by_window,
        )

        # 在单独线程中运行 CureTMDbAnimeShy 服务
        self._thread = threading.Thread(target=self._run_binary_in_thread, daemon=True)
        self._thread.start()

    def load_config(self, config: dict):
        """加载配置"""
        if config:
            self.config = CureTMDbAnimeShyConfig(**config)

    def stop_service(self):
        """退出插件"""
        # 先通知输出读取线程退出，再主动终止其子进程以唤醒管道。
        self._event.set()
        process_stopped = self._terminate_process()

        if self._thread:
            # 等待线程结束
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning("CureTMDbAnimeShy 服务线程未能及时停止。")
                self.patch_manager.unpatch_all()
                return False
            self._thread = None

        if not process_stopped:
            self.patch_manager.unpatch_all()
            return False

        # 仅在旧线程和进程都停止后重置事件，避免遗留线程恢复运行。
        self._event.clear()

        # 线程停止后再恢复补丁
        self.patch_manager.unpatch_all()
        return True

    def _terminate_process(self, process=None) -> bool:
        """终止并回收已跟踪的 CureTMDbAnimeShy 子进程。"""
        import psutil

        with self._process_lock:
            target = process or self._process
            if not target:
                return True

            stopped = False
            try:
                if target.is_running():
                    logger.info("正在停止 CureTMDbAnimeShy 子进程。")
                    target.terminate()

                try:
                    target.wait(timeout=3)
                    stopped = True
                except psutil.TimeoutExpired:
                    logger.warning("CureTMDbAnimeShy 子进程未及时退出，强制终止。")
                    if target.is_running():
                        target.kill()
                    target.wait(timeout=2)
                    stopped = True
                except psutil.NoSuchProcess:
                    stopped = True
            except psutil.NoSuchProcess:
                stopped = True
            except Exception as e:
                logger.warning(f"清理 CureTMDbAnimeShy 子进程失败：{e}")

            if stopped and self._process is target:
                self._process = None
            return stopped

    @staticmethod
    def _is_port_in_use(port: int) -> bool:
        """检查本机端口是否已有服务监听，避免重复启动。"""
        import socket

        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=0.25):
                return True
        except OSError:
            return False

    def get_api(self) -> List[Dict[str, Any]]:
        """
        注册插件 API。

        :return: 插件 API 声明列表
        """
        return [
            {
                "path": "/refresh_source",
                "endpoint": self.api_refresh_source,
                "methods": ["POST"],
                "summary": "清理缓存并重新下载来源文件",
                "description": "删除本地来源数据文件并重启服务，强制从来源地址重新下载最新的分季数据。",
            },
            {
                "path": "/upload_source",
                "endpoint": self.api_upload_source,
                "methods": ["POST"],
                "summary": "上传本地来源文件",
                "description": "直接上传一个分季来源 JSON 文件作为兜底，写入后重启服务使其生效。",
            },
            {
                "path": "/source_status",
                "endpoint": self.api_source_status,
                "methods": ["GET"],
                "summary": "查询来源数据状态",
                "description": "返回本地来源文件的路径、条目数、是否包含当前来源地址等信息。",
            },
        ]

    def api_source_status(self) -> Dict[str, Any]:
        """
        查询本地来源数据的加载状态。

        :return: 状态字典
        """
        local_file = self._source_seasons_file()
        entries: List[str] = []
        if local_file.exists():
            try:
                import json

                data = json.loads(local_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    entries = list(data.keys())
            except Exception as e:
                logger.warning(f"读取本地来源数据失败：{e}")

        return {
            "success": True,
            "source_url": self.config.source,
            "prefer_source_season": self.config.prefer_source_season,
            "file": local_file.as_posix(),
            "file_exists": local_file.exists(),
            "file_size": local_file.stat().st_size if local_file.exists() else 0,
            "entry_count": len(entries),
            "entries": entries,
        }

    def api_refresh_source(self) -> Dict[str, Any]:
        """
        清理本地来源缓存并重启服务，强制重新下载来源文件。

        :return: 执行结果
        """
        local_file = self._source_seasons_file()
        # 先停服务，避免文件句柄与写入竞争
        if not self.stop_service():
            return {"success": False, "message": "旧服务未能停止，已取消操作"}

        removed = False
        try:
            if local_file.exists():
                local_file.unlink()
                removed = True
        except Exception as e:
            logger.error(f"删除本地来源文件失败：{e}")
            return {"success": False, "message": f"删除本地来源文件失败：{e}"}

        # 重置内存缓存，确保下次读取重新从来源下载
        self._source_seasons = {}
        self._source_seasons_url = None

        self._restart_binary_thread()
        logger.info(f"已清理来源缓存（删除文件={removed}）并重启服务，将重新下载来源数据。")
        return {
            "success": True,
            "removed": removed,
            "source_url": self.config.source,
            "message": "已清理缓存并重启服务，正在重新下载来源文件。",
        }

    def api_upload_source(
        self, file: "UploadFile" = File(default=None)
    ) -> Dict[str, Any]:
        """
        接收上传的来源 JSON 文件并写入本地数据目录，随后重启服务。

        :param file: 上传的文件对象（FastAPI UploadFile）
        :return: 执行结果
        """
        import json

        if file is None:
            return {"success": False, "message": "未收到上传文件"}

        try:
            content = file.file.read()
        except Exception as e:
            return {"success": False, "message": f"读取上传文件失败：{e}"}

        if not content:
            return {"success": False, "message": "上传文件为空"}

        try:
            data = json.loads(content.decode("utf-8"))
        except Exception as e:
            return {"success": False, "message": f"上传文件不是合法 JSON：{e}"}

        if not isinstance(data, dict) or not data:
            return {"success": False, "message": "上传的 JSON 必须是非空对象"}

        # 校验结构：每个条目需包含 seasons 列表，且每季含 season_number/episode_count
        for tmdb_id, entry in data.items():
            if not isinstance(entry, dict) or not isinstance(entry.get("seasons"), list):
                return {
                    "success": False,
                    "message": f"条目 {tmdb_id} 缺少 seasons 列表",
                }
            for season in entry["seasons"]:
                if not isinstance(season, dict):
                    return {
                        "success": False,
                        "message": f"条目 {tmdb_id} 的 seasons 元素不是对象",
                    }
                if not isinstance(season.get("season_number"), int) or not isinstance(
                    season.get("episode_count"), int
                ):
                    return {
                        "success": False,
                        "message": f"条目 {tmdb_id} 的 season_number/episode_count 必须为整数",
                    }

        local_file = self._source_seasons_file()
        # 先停服务，确保文件可被替换
        if not self.stop_service():
            return {"success": False, "message": "旧服务未能停止，已取消操作"}

        try:
            local_file.parent.mkdir(parents=True, exist_ok=True)
            local_file.write_bytes(content)
        except Exception as e:
            return {"success": False, "message": f"写入来源文件失败：{e}"}

        self._source_seasons = {}
        self._source_seasons_url = None
        self._restart_binary_thread()
        logger.info(
            f"已上传来源文件（{len(content)} 字节，{len(data)} 个条目）并重启服务。"
        )
        return {
            "success": True,
            "file": local_file.as_posix(),
            "size": len(content),
            "entry_count": len(data),
            "message": "来源文件已写入并重启服务，分季数据已更新。",
        }

    def _restart_binary_thread(self) -> None:
        """
        以当前配置重新启动二进制服务线程。

        在停止旧服务之后调用，用于让新写入的来源文件立即生效。
        """
        if not self.config.enabled:
            return
        self._event.clear()
        self._thread = threading.Thread(
            target=self._run_binary_in_thread, daemon=True
        )
        self._thread.start()

    def get_form(self):
        """
        返回插件唯一的配置页面。

        该页面同时承载运行配置与来源数据维护入口：
        基本信息、修正策略、来源设置、来源数据维护、来源状态。
        插件不再提供独立详情页，点击卡片直接进入本页面。

        :return: `(页面结构, 默认配置)` 二元组
        """
        status = self.api_source_status()
        entries_text = "、".join(status.get("entries") or []) or "暂无"
        file_state = "已存在" if status.get("file_exists") else "不存在"

        return [
            {
                "component": "VForm",
                "content": [
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
                                            "density": "comfortable",
                                            "class": "mb-2",
                                            "text": "本页同时管理运行配置与分季来源数据，无需切换其他页面。",
                                        },
                                    }
                                ],
                            }
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
                                        "component": "VCard",
                                        "props": {"variant": "outlined", "class": "mb-3"},
                                        "content": [
                                            {
                                                "component": "VCardTitle",
                                                "props": {"class": "text-subtitle-1"},
                                                "text": "基础设置",
                                            },
                                            {
                                                "component": "VCardText",
                                                "content": [
                                                    {
                                                        "component": "VRow",
                                                        "content": [
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VSwitch",
                                                                        "props": {
                                                                            "model": "enabled",
                                                                            "label": "启用插件",
                                                                            "hint": "开启后将使用 CureTMDbAnimeShy 代理 TheMovieDb API请求",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VTextField",
                                                                        "props": {
                                                                            "model": "port",
                                                                            "label": "端口",
                                                                            "type": "number",
                                                                            "min": 1024,
                                                                            "max": 65535,
                                                                            "step": 1,
                                                                            "hint": "插件服务的监听端口，范围 1024-65535",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VSwitch",
                                                                        "props": {
                                                                            "model": "bangumi_use_proxy",
                                                                            "label": "Bangumi 使用代理",
                                                                            "hint": "请求 Bangumi API 时是否使用代理",
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
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 6,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VTextField",
                                                                        "props": {
                                                                            "model": "bangumi_api_url",
                                                                            "label": "Bangumi API URL",
                                                                            "placeholder": "https://api.bgm.tv",
                                                                            "hint": "请求 Bangumi API 时使用的地址",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    }
                                ],
                            }
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
                                        "component": "VCard",
                                        "props": {"variant": "outlined", "class": "mb-3"},
                                        "content": [
                                            {
                                                "component": "VCardTitle",
                                                "props": {"class": "text-subtitle-1"},
                                                "text": "分季修正策略",
                                            },
                                            {
                                                "component": "VCardText",
                                                "content": [
                                                    {
                                                        "component": "VRow",
                                                        "content": [
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VSwitch",
                                                                        "props": {
                                                                            "model": "enable_correction",
                                                                            "label": "启用元数据修正",
                                                                            "hint": "开启后将对元数据季号、集号进行修正",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VSwitch",
                                                                        "props": {
                                                                            "model": "assume_season_by_window",
                                                                            "label": "按播出窗口推断季号",
                                                                            "hint": "在标题缺少明确季号时，根据发布时间匹配 TMDB 季播出窗口尝试修正季号",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VTextField",
                                                                        "props": {
                                                                            "model": "grace_episodes",
                                                                            "label": "集数越界宽限",
                                                                            "type": "number",
                                                                            "min": 0,
                                                                            "max": 5,
                                                                            "step": 1,
                                                                            "hint": "最新季连载中允许超出 TMDB 已知集数的宽限集数，用于容忍连载滞后",
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
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 4,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VTextField",
                                                                        "props": {
                                                                            "model": "rewrite_threshold",
                                                                            "label": "改写阈值",
                                                                            "type": "number",
                                                                            "min": 0,
                                                                            "max": 40,
                                                                            "step": 2,
                                                                            "hint": "改写候选需比原样候选高出的最小分数差值，数值越大越严格",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    }
                                ],
                            }
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
                                        "component": "VCard",
                                        "props": {"variant": "outlined", "class": "mb-3"},
                                        "content": [
                                            {
                                                "component": "VCardTitle",
                                                "props": {"class": "text-subtitle-1"},
                                                "text": "分季来源",
                                            },
                                            {
                                                "component": "VCardText",
                                                "content": [
                                                    {
                                                        "component": "VRow",
                                                        "content": [
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 9,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VTextField",
                                                                        "props": {
                                                                            "model": "source",
                                                                            "label": "来源地址",
                                                                            "hint": "自定义分季数据源地址（JSON格式），适用于无法自动匹配或需自定义分季的场景",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 3,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VSwitch",
                                                                        "props": {
                                                                            "model": "prefer_source_season",
                                                                            "label": "优先使用来源分季",
                                                                            "hint": "开启后，设置了来源时优先按来源的 seasons 定义修正分季，覆盖 TMDB/TVDB 推导结果",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    }
                                ],
                            }
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
                                        "component": "VCard",
                                        "props": {"variant": "outlined", "class": "mb-3"},
                                        "content": [
                                            {
                                                "component": "VCardTitle",
                                                "props": {"class": "text-subtitle-1"},
                                                "text": "来源数据维护",
                                            },
                                            {
                                                "component": "VCardText",
                                                "content": [
                                                    {
                                                        "component": "VAlert",
                                                        "props": {
                                                            "type": "info"
                                                            if status.get("file_exists")
                                                            else "warning",
                                                            "variant": "tonal",
                                                            "density": "comfortable",
                                                            "class": "mb-3",
                                                            "text": (
                                                                f"来源地址：{status.get('source_url') or '未设置'}\n"
                                                                f"本地数据文件：{status.get('file')}\n"
                                                                f"文件状态：{file_state}"
                                                                f"（{status.get('file_size')} 字节，{status.get('entry_count')} 个条目）\n"
                                                                f"条目：{entries_text}"
                                                            ),
                                                        },
                                                    },
                                                    {
                                                        "component": "VRow",
                                                        "content": [
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 6,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VBtn",
                                                                        "props": {
                                                                            "color": "primary",
                                                                            "block": True,
                                                                            "prepend-icon": "mdi-cloud-download",
                                                                        },
                                                                        "text": "清理缓存并重新下载来源文件",
                                                                        "events": {
                                                                            "click": {
                                                                                "api": "plugin/CureTMDbAnimeShy/refresh_source",
                                                                                "method": "post",
                                                                            }
                                                                        },
                                                                    }
                                                                ],
                                                            },
                                                            {
                                                                "component": "VCol",
                                                                "props": {
                                                                    "cols": 12,
                                                                    "md": 6,
                                                                },
                                                                "content": [
                                                                    {
                                                                        "component": "VFileInput",
                                                                        "props": {
                                                                            "model": "upload_file",
                                                                            "label": "上传来源文件（JSON）",
                                                                            "accept": ".json",
                                                                            "prepend-icon": "mdi-upload",
                                                                            "hint": "作为兜底：直接上传分季来源 JSON，写入后自动重启服务",
                                                                            "persistent-hint": True,
                                                                        },
                                                                    },
                                                                    {
                                                                        "component": "VBtn",
                                                                        "props": {
                                                                            "color": "secondary",
                                                                            "block": True,
                                                                            "prepend-icon": "mdi-content-save",
                                                                        },
                                                                        "text": "上传并应用来源文件",
                                                                        "events": {
                                                                            "click": {
                                                                                "api": "plugin/CureTMDbAnimeShy/upload_source",
                                                                                "method": "post",
                                                                            }
                                                                        },
                                                                    },
                                                                ],
                                                            },
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], CureTMDbAnimeShyConfig().model_dump()

    def get_page(self) -> Optional[List[dict]]:
        """不提供详情页，函数体保持占位使框架判定 has_page=False，点击插件卡片直接进入配置页。"""
        pass


    def get_state(self):
        return self.patch_manager.is_patched()

    def _run_binary_in_thread(self):
        """
        在独立线程中运行二进制文件并捕获其输出。
        """
        # 工作目录
        working_dir = settings.PLUGIN_DATA_PATH / self.__class__.__name__.lower()
        # 可执行文件路径
        executable_path = working_dir / self.binary_name

        if not executable_path.exists() or not self._check_version(executable_path):
            logger.info("尝试下载二级制文件...")
            self.__download(executable_path)
            if not executable_path.exists():
                logger.error("二级制文件不存在，无法启动 CureTMDbAnimeShy 服务。")
                return

        # 确保文件有可执行权限
        if not os.access(executable_path, os.X_OK) and not self.__fix_exec_permission(
            executable_path
        ):
            return

        # 构建命令行参数列表
        cmd_args = [
            executable_path.as_posix(),
            "--port",
            str(self.config.port),
            "--data-dir",
            working_dir.as_posix(),
        ]

        if self.config.bangumi_api_url:
            cmd_args.extend(["--bangumi-api-url", self.config.bangumi_api_url])

        if self.config.bangumi_use_proxy:
            cmd_args.append("--bangumi-use-proxy")

        if self.config.source:
            cmd_args.extend(["--cure-source", self.config.source])

        if settings.PROXY_HOST:
            cmd_args.extend(["--proxy", settings.PROXY_HOST])

        if settings.TMDB_API_DOMAIN:
            cmd_args.extend(["--tmdb-api-url", f"https://{settings.TMDB_API_DOMAIN}"])

        if self._is_port_in_use(self.config.port):
            logger.error(
                f"端口 {self.config.port} 已被占用，取消重复启动 CureTMDbAnimeShy。"
            )
            return

        process = None
        try:
            from subprocess import PIPE

            import psutil

            process = psutil.Popen(
                cmd_args, stdout=PIPE, stderr=PIPE, text=True, bufsize=1
            )
            with self._process_lock:
                self._process = process
            if process.is_running():
                self.patch_manager.patch_build_url(self.config.port)
                if self.config.enable_correction:
                    self.patch_manager.patch_meta_enhancement(self.correct_meta)
                # 输出服务日志
                self._read_process_output(process)

        finally:
            if process:
                self._terminate_process(process)
            logger.info("CureTMDbAnimeShy 服务线程已退出。")

    def _read_process_output(self, process):
        import selectors

        def log_output_line(line: str):
            """转发经分级及脱敏处理的服务输出。"""
            result = classify_service_line(line)
            if result:
                level, message = result
                getattr(logger, level)(f"🔗  {message}")

        streams = [stream for stream in (process.stdout, process.stderr) if stream]
        with selectors.DefaultSelector() as sel:
            for stream in streams:
                sel.register(stream, selectors.EVENT_READ)

            while not self._event.is_set() and sel.get_map():
                events = sel.select(timeout=1)
                for key, _ in events:
                    try:
                        line = key.fileobj.readline()
                    except (OSError, ValueError):
                        line = ""
                    if line:
                        log_output_line(line)
                    else:
                        # EOF/HUP 会持续被 selector 报告；注销后才能避免忙循环。
                        try:
                            sel.unregister(key.fileobj)
                        except KeyError:
                            pass

        for stream in streams:
            try:
                stream.close()
            except (OSError, ValueError):
                pass

    def _check_version(self, executable: Path) -> bool:
        """检查版本"""
        from app.sdk.string import StringUtils

        version = SystemUtils.execute(f"{executable.as_posix()} -v")
        if version == "dev":
            return True

        result, msg = StringUtils.compare_version(
            version, ">=", self.binary_version, True
        )
        if result is None:
            logger.error(f"比较版本出错：{msg}")
            return False

        logger.info(msg)
        return result

    @staticmethod
    def __fix_exec_permission(file_path: Path) -> bool:
        """修复文件可执行权限"""
        try:
            import stat

            current_uid = os.getuid()
            file_stat = file_path.stat()

            # 文件所有者或 root 可直接修改
            if current_uid == file_stat.st_uid or current_uid == 0:
                file_path.chmod(file_stat.st_mode | stat.S_IXUSR)
                success = os.access(file_path, os.X_OK)
                if success:
                    logger.info(
                        f"权限修复成功：{oct(file_path.stat().st_mode & 0o777)}"
                    )
                else:
                    logger.error("权限设置后仍无法执行")
                return success

            # Docker 环境通过容器修改
            logger.info("当前用户无权限，尝试通过 Docker 修改")
            return CureTMDbAnimeShy.__fix_permission_via_docker(file_path)

        except Exception as e:
            logger.error(f"修复可执行权限失败：{e}")
            return False

    @staticmethod
    def __fix_permission_via_docker(file_path: Path) -> bool:
        """
        通过 Docker 守护进程修改文件权限

        :return bool: 修复成功返回 True，否则返回 False
        """
        try:
            import docker
            from app.sdk.services import SystemHelper

            # 检查是否为 Docker 环境
            if not SystemUtils.is_docker():
                logger.error("非 Docker 环境，无法通过 Docker 守护进程修改权限")
                return False

            # 获取容器 ID
            container_id = SystemHelper._get_container_id()
            if not container_id:
                logger.error("无法获取容器 ID")
                return False

            # 创建 Docker 客户端
            client = docker.DockerClient(base_url=settings.DOCKER_CLIENT_API)
            container = client.containers.get(container_id)

            logger.info("通过 Docker 容器执行权限修改")

            # 执行命令
            exit_code, output = container.exec_run(
                cmd=["chmod", "+x", file_path.as_posix()],
                stdout=False,
                detach=True,
            )

            if exit_code == 0:
                logger.info("通过 Docker 守护进程修改权限成功")
                return os.access(file_path, os.X_OK)
            else:
                logger.error(
                    f"通过 Docker 修改权限失败：{output.decode() if output else '无输出'}"
                )
                return False

        except Exception as e:
            logger.error(f"通过 Docker 修改权限失败：{e}")
            return False

    def __download_url(self):
        """
        获取下载链接
        """
        _url = "{binary_repo}/{name}/releases/download/v{version}/{name}-{os}-{arch}"

        if SystemUtils.is_aarch64():
            arch = "arm64"
        elif SystemUtils.is_x86_64():
            arch = "amd64"
        else:
            raise NotImplementedError("不支持的CPU架构")

        os_name = "darwin" if SystemUtils.is_macos() else "linux"

        return _url.format(
            binary_repo=self.binary_repo,
            name=self.binary_name,
            arch=arch,
            version=self.binary_version,
            os=os_name,
        )

    def __download(self, dest_path: Path):
        """
        下载二进制文件
        """
        import shutil
        import tempfile

        url = self.__download_url()
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / f"{self.binary_name}.tmp"

        try:
            # 创建目标目录
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"正在下载: {url}")
            with RequestUtils(proxies=settings.PROXY).get_stream(url) as r:
                r.raise_for_status()
                with open(temp_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # 设置可执行权限
            temp_file.chmod(0o755)

            # 复制到目标位置
            shutil.copy2(temp_file.as_posix(), dest_path.as_posix())

            logger.info(f"下载完成: {dest_path}")

        except Exception as e:
            logger.error(f"下载失败: {e}")
            raise
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")

    def _source_seasons_file(self) -> Path:
        """
        返回二进制服务使用的本地来源数据文件路径。

        :return: `curetmdb.json` 的完整路径
        """
        working_dir = settings.PLUGIN_DATA_PATH / self.__class__.__name__.lower()
        return working_dir / "curetmdb.json"

    def _load_source_seasons(self, force: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        加载自定义来源的分季定义表。

        优先读取本地 `curetmdb.json`（二进制下载/上传后的落地文件），
        本地不存在时再回退到远程 `source`。解析结果按 TMDB ID 缓存在内存中。

        :param force: 为 True 时忽略内存缓存重新读取
        :return: `{tmdb_id: [seasons...]}` 形式的映射表
        """
        cache_key = self.config.source
        if (
            not force
            and self._source_seasons
            and self._source_seasons_url == cache_key
        ):
            return self._source_seasons

        raw: Optional[Dict[str, Any]] = None

        # 1) 本地文件优先（清理缓存后重新下载或手动上传都会落到这里）
        local_file = self._source_seasons_file()
        if local_file.exists():
            try:
                import json

                raw = json.loads(local_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"读取本地来源数据失败：{e}")
                raw = None

        # 2) 回退到远程来源
        if not isinstance(raw, dict) and self.config.source:
            try:
                raw = RequestUtils(timeout=10).get_json(self.config.source)
            except Exception as e:
                logger.error(f"下载远程来源数据失败：{e}")
                raw = None

        parsed: Dict[str, List[Dict[str, Any]]] = {}
        if isinstance(raw, dict):
            for tmdb_id, entry in raw.items():
                if not isinstance(entry, dict):
                    continue
                seasons = entry.get("seasons")
                if not isinstance(seasons, list):
                    continue
                normalized: List[Dict[str, Any]] = []
                for season in seasons:
                    if not isinstance(season, dict):
                        continue
                    try:
                        season_number = int(season.get("season_number"))
                        episode_count = int(season.get("episode_count"))
                    except (TypeError, ValueError):
                        continue
                    if season_number < 1 or episode_count < 1:
                        continue
                    normalized.append(
                        {
                            "season_number": season_number,
                            "name": str(season.get("name") or f"第{season_number}季"),
                            "episode_count": episode_count,
                        }
                    )
                normalized.sort(key=lambda item: item["season_number"])
                if normalized:
                    parsed[str(tmdb_id)] = normalized

        self._source_seasons = parsed
        self._source_seasons_url = cache_key
        return parsed

    def _apply_source_season(self, meta: MetaBase, mediainfo: MediaInfo) -> bool:
        """
        按自定义来源的分季定义修正元数据的季号与集号。

        来源 JSON 的 `seasons` 描述的是"作品级"分季（如 S1=14/S2=12/S3=10/S4=12），
        而识别结果里的季号往往是 TMDB 的合并季号（如把后三季合并为 S2）。
        这里按来源各季集数的累计分布，把识别出的季集号重新定位到来源季号：

        - 识别季号已存在于来源定义且集号未越界时，保持原样；
        - 否则把识别结果视为"源季序 + 本季集号"的组合，换算为累计集号后
          依次扣减各来源季的集数，定位到正确的来源季与季内集号。

        :param meta: 原始元数据对象
        :param mediainfo: 媒体信息对象
        :return: 实际发生修正时返回 True，否则返回 False
        """
        seasons = self._load_source_seasons().get(str(mediainfo.tmdb_id))
        if not seasons:
            return False

        begin_season = int(meta.begin_season or 1)
        begin_episode = int(meta.begin_episode or 1)
        episode_list = [int(item) for item in (meta.episode_list or [begin_episode])]

        # 仅处理同季范围，跨季交给原有引擎
        if meta.end_season is not None and int(meta.end_season) != begin_season:
            return False

        season_count = {
            item["season_number"]: item["episode_count"] for item in seasons
        }

        # 识别季号已存在于来源定义且集号未越界：无需改写
        if begin_season in season_count:
            max_episode = max(episode_list) if episode_list else begin_episode
            if max_episode <= season_count[begin_season]:
                return False

        # 把识别结果换算为"作品级累计集号"
        #
        # TMDB 常把多季合并：例如 4 季作品在 TMDB 只有 S1(36)+S2(24)。
        # 识别结果中的季号对应 TMDB 季，集号是该 TMDB 季内的集号；
        # 平移到来源分季时，需要先按来源季数找到该 TMDB 季对应的来源季序号。
        #
        # 策略：以"识别季号 - 1"作为已消耗的来源季数，累计此前季的集数作为偏移。
        max_episode = max(episode_list) if episode_list else begin_episode
        if max_episode <= 0:
            return False

        consumed = 0
        for index, item in enumerate(seasons):
            if index == begin_season - 1:
                consumed = sum(
                    previous["episode_count"] for previous in seasons[:index]
                )
                break
        else:
            # 识别季号超出来源季数，按最后已知季定位
            consumed = sum(item["episode_count"] for item in seasons)

        cumulative = consumed + max_episode

        target_season: Optional[Dict[str, Any]] = None
        offset = 0
        for item in seasons:
            if cumulative <= offset + item["episode_count"]:
                target_season = item
                break
            offset += item["episode_count"]

        if target_season is None:
            # 超出来源定义覆盖范围，保持原样
            return False

        target_episode = cumulative - offset
        if (
            target_season["season_number"] == begin_season
            and target_episode == max_episode
        ):
            return False

        meta.set_season([target_season["season_number"]])
        meta.set_episode([target_episode])
        logger.info(
            "%s 按来源分季修正: S%02dE%02d => S%02dE%02d (%s)",
            meta.title,
            begin_season,
            max_episode,
            target_season["season_number"],
            target_episode,
            target_season["name"],
        )
        return True

    @cached(ttl=2 * 3600)
    def _get_logical_mapping(self, tmdb_id: int):
        """
        获取 TMDB 逻辑季集映射信息
        """
        mapping: Dict[tuple[int, int], tuple[int, int]] = {}

        result = RequestUtils(timeout=2).get_json(
            f"http://127.0.0.1:{self.config.port}/cache/mapping/{tmdb_id}"
        )
        if not isinstance(result, dict):
            return mapping

        for season_key, episodes in result.items():
            try:
                season_num = int(season_key)
            except (TypeError, ValueError):
                continue

            if not isinstance(episodes, dict):
                continue

            for episode_key, item in episodes.items():
                try:
                    episode_num = int(episode_key)
                except (TypeError, ValueError):
                    continue

                if not isinstance(item, dict):
                    continue

                logical_season = item.get("season")
                logical_episode = item.get("episode")
                try:
                    logical_season = int(logical_season)
                    logical_episode = int(logical_episode)
                except (TypeError, ValueError):
                    continue

                mapping[(season_num, episode_num)] = (logical_season, logical_episode)

        return mapping

    def correct_meta(self, meta: MetaBase, mediainfo: MediaInfo) -> MetaBase:
        """
        根据逻辑季信息调整元数据对象中的季号和集号。

        :param meta: 原始元数据对象
        :param mediainfo: 媒体信息对象
        """
        if not meta or not mediainfo or mediainfo.type.name != "TV":
            return meta

        if set(mediainfo.genre_ids).isdisjoint(settings.ANIME_GENREIDS):
            return meta

        # 检查识别词是否已偏移集数
        if meta.apply_words and (
            matched_word := next(
                (
                    word
                    for word in meta.apply_words
                    if " >> " in word and " <> " in word
                ),
                None,
            )
        ):
            logger.info(f"存在应用的集数偏移识别词 `{matched_word}`, 跳过调整元数据")
            return meta

        tmdb_mapping = self._get_logical_mapping(mediainfo.tmdb_id)

        # 设置了来源且开启优先来源分季时，先用来源定义修正；
        # 命中即视为最终结果，避免再被 TMDB/TVDB 推导覆盖。
        if (
            self.config.prefer_source_season
            and self.config.source
            and self._apply_source_season(meta, mediainfo)
        ):
            return meta

        pubdate = self.patch_manager.get_torrent_pubdate(
            title=meta.title,
            description=meta.subtitle,
        )
        try:
            decision = self.meta_correction_use_case.correct(
                meta=meta,
                tmdb_mapping=tmdb_mapping,
                mediainfo=mediainfo,
                publish_date=pubdate,
                source="torrent_pubdate" if pubdate else None,
            )
        except ValueError:
            return meta

        if not decision.changed:
            return meta

        meta.set_season(decision.final_range.season_list)
        meta.set_episode(decision.final_range.episode_list)

        logger.info(
            "%s 调整结论: %s => %s, %s",
            meta.title,
            decision.original_range.format(),
            decision.final_range.format(),
            "；".join(decision.reasons) if decision.reasons else "",
        )

        return meta
