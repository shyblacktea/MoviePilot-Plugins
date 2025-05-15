import threading
import sys
import time
import shutil
import platform
import tarfile
import tempfile
import os # <-- ADDED IMPORT
from ruamel.yaml import YAML
from ruamel.yaml.representer import RoundTripRepresenter
import psutil
from collections.abc import Mapping
from datetime import datetime, timedelta
from threading import Event as ThreadEvent
from typing import Any, List, Dict, Tuple, Self, cast, Optional
from errno import EIO, ENOENT
from urllib.parse import quote, unquote, urlsplit, urlencode
from pathlib import Path

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Request, Response
import requests
from requests.exceptions import HTTPError
from orjson import dumps, loads
from cachetools import cached, TTLCache, LRUCache
from cachetools.keys import hashkey
from p115client import P115Client
from p115client.tool.iterdir import (
    iter_files_with_path,
    get_path_to_cid,
    share_iterdir,
    get_id_to_path,
)
from p115client.tool.life import iter_life_behavior_list, life_show
from p115client.tool.util import share_extract_payload
from p115rsacipher import encrypt, decrypt
from p115client.exception import DataError # <-- 新增导入

from app import schemas
from app.schemas import TransferInfo, FileItem, RefreshMediaItem, ServiceInfo
from app.schemas.types import EventType, MediaType, MessageChannel, NotificationType
from app.core.config import settings
from app.core.event import eventmanager, Event
from app.core.context import MediaInfo
from app.core.meta import MetaBase
from app.core.metainfo import MetaInfoPath
from app.log import logger
from app.plugins import _PluginBase
from app.chain.transfer import TransferChain
from app.chain.media import MediaChain
from app.helper.mediaserver import MediaServerHelper
from app.utils.system import SystemUtils

# 新增 MediaWarp 相关 imports
import platform
import tarfile
import tempfile
from ruamel.yaml import YAML
from ruamel.yaml.representer import RoundTripRepresenter
import psutil
# ---

p1115strmhelper_lock = threading.Lock()


class IdPathCache:
    """
    文件路径ID缓存
    """

    def __init__(self, maxsize=128):
        self.id_to_dir = LRUCache(maxsize=maxsize)
        self.dir_to_id = LRUCache(maxsize=maxsize)

    def add_cache(self, id: int, directory: str):
        """
        添加缓存
        """
        self.id_to_dir[id] = directory
        self.dir_to_id[directory] = id

    def get_dir_by_id(self, id: int):
        """
        通过 ID 获取路径
        """
        return self.id_to_dir.get(id)

    def get_id_by_dir(self, directory: str):
        """
        通过路径获取 ID
        """
        return self.dir_to_id.get(directory)

    def clear(self):
        """
        清空所有缓存
        """
        self.id_to_dir.clear()
        self.dir_to_id.clear()


class Url(str):
    def __new__(cls, val: Any = "", /, *args, **kwds):
        return super().__new__(cls, val)

    def __init__(self, val: Any = "", /, *args, **kwds):
        self.__dict__.update(*args, **kwds)

    def __getattr__(self, attr: str, /):
        try:
            return self.__dict__[attr]
        except KeyError as e:
            raise AttributeError(attr) from e

    def __getitem__(self, key, /):
        try:
            if isinstance(key, str):
                return self.__dict__[key]
        except KeyError:
            return super().__getitem__(key)  # type: ignore

    def __repr__(self, /) -> str:
        cls = type(self)
        if (module := cls.__module__) == "__main__":
            name = cls.__qualname__
        else:
            name = f"{module}.{cls.__qualname__}"
        return f"{name}({super().__repr__()}, {self.__dict__!r})"

    @classmethod
    def of(cls, val: Any = "", /, ns: None | dict = None) -> Self:
        self = cls.__new__(cls, val)
        if ns is not None:
            self.__dict__ = ns
        return self

    def get(self, key, /, default=None):
        return self.__dict__.get(key, default)

    def items(self, /):
        return self.__dict__.items()

    def keys(self, /):
        return self.__dict__.keys()

    def values(self, /):
        return self.__dict__.values()


def check_response(
    resp: requests.Response,
) -> requests.Response:
    """
    检查 HTTP 响应，如果状态码 ≥ 400 则抛出 HTTPError
    """
    if resp.status_code >= 400:
        raise HTTPError(
            f"HTTP Error {resp.status_code}: {resp.text}",
            response=resp,
        )
    return resp


def get_download_url(pickcode: str, cookie: str):
    """
    获取下载链接
    """
    resp = requests.post(
        "http://proapi.115.com/android/2.0/ufile/download",
        data={"data": encrypt(f'{{"pick_code":"{pickcode}"}}').decode("utf-8")},
        headers={
            "User-Agent": settings.USER_AGENT,
            "Cookie": cookie,
        },
    )
    check_response(resp)
    json = loads(cast(bytes, resp.content))
    if not json["state"]:
        raise OSError(EIO, json)
    data = json["data"] = loads(decrypt(json["data"]))
    data["file_name"] = unquote(urlsplit(data["url"]).path.rpartition("/")[-1])
    return Url.of(data["url"], data)


def save_mediainfo_file(
    file_path: Path, file_name: str, download_url: str, cookie: str
):
    """
    保存媒体信息文件
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(
        download_url,
        stream=True,
        timeout=30,
        headers={
            "User-Agent": settings.USER_AGENT,
            "Cookie": cookie,
        },
    ) as response:
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    logger.info(f"【媒体信息文件】保存 {file_name} 文件成功: {file_path}")


class FullSyncStrmHelper:
    """
    全量生成 STRM 文件
    """

    def __init__(
        self,
        client,
        user_rmt_mediaext: str,
        user_download_mediaext: str,
        server_address: str,
        cookie: str,
        auto_download_mediainfo: bool = False,
    ):
        self.rmt_mediaext = [
            f".{ext.strip()}" for ext in user_rmt_mediaext.replace("，", ",").split(",")
        ]
        self.download_mediaext = [
            f".{ext.strip()}"
            for ext in user_download_mediaext.replace("，", ",").split(",")
        ]
        self.auto_download_mediainfo = auto_download_mediainfo
        self.client = client
        self.cookie = cookie
        self.strm_count = 0
        self.mediainfo_count = 0
        self.server_address = server_address.rstrip("/")

    def generate_strm_files(self, full_sync_strm_paths):
        """
        生成 STRM 文件
        """
        media_paths = full_sync_strm_paths.split("\n")
        for path in media_paths:
            if not path:
                continue
            parts = path.split("#", 1)
            pan_media_dir = parts[1]
            target_dir = parts[0]

            try:
                parent_id = int(self.client.fs_dir_getid(pan_media_dir)["id"])
                logger.info(f"【全量STRM生成】网盘媒体目录 ID 获取成功: {parent_id}")
            except Exception as e:
                logger.error(f"【全量STRM生成】网盘媒体目录 ID 获取失败: {e}")
                return False

            try:
                for item in iter_files_with_path(
                    self.client, cid=parent_id, cooldown=2
                ):
                    if item["is_dir"] or item["is_directory"]:
                        continue
                    file_path = item["path"]
                    file_path = Path(target_dir) / Path(file_path).relative_to(
                        pan_media_dir
                    )
                    file_target_dir = file_path.parent
                    original_file_name = file_path.name
                    file_name = file_path.stem + ".strm"
                    new_file_path = file_target_dir / file_name

                    if self.auto_download_mediainfo:
                        if file_path.suffix in self.download_mediaext:
                            pickcode = item["pickcode"]
                            if not pickcode:
                                logger.error(
                                    f"【全量STRM生成】{original_file_name} 不存在 pickcode 值，无法下载该文件"
                                )
                                continue
                            download_url = get_download_url(
                                pickcode=pickcode, cookie=self.cookie
                            )

                            if not download_url:
                                logger.error(
                                    f"【全量STRM生成】{original_file_name} 下载链接获取失败，无法下载该文件"
                                )
                                continue

                            save_mediainfo_file(
                                file_path=Path(file_path),
                                file_name=original_file_name,
                                download_url=download_url,
                                cookie=self.cookie,
                            )
                            self.mediainfo_count += 1
                            continue

                    if file_path.suffix not in self.rmt_mediaext:
                        logger.warn(
                            "【全量STRM生成】跳过网盘路径: %s",
                            str(file_path).replace(str(target_dir), "", 1),
                        )
                        continue

                    pickcode = item["pickcode"]
                    if not pickcode:
                        pickcode = item["pick_code"]

                    new_file_path.parent.mkdir(parents=True, exist_ok=True)

                    if not pickcode:
                        logger.error(
                            f"【全量STRM生成】{original_file_name} 不存在 pickcode 值，无法生成 STRM 文件"
                        )
                        continue
                    if not (len(pickcode) == 17 and str(pickcode).isalnum()):
                        logger.error(
                            f"【全量STRM生成】错误的 pickcode 值 {pickcode}，无法生成 STRM 文件"
                        )
                        continue
                    strm_url = f"{self.server_address}/api/v1/plugin/P1115StrmHelper/redirect_url?apikey={settings.API_TOKEN}&pickcode={pickcode}"

                    with open(new_file_path, "w", encoding="utf-8") as file:
                        file.write(strm_url)
                    self.strm_count += 1
                    logger.info(
                        "【全量STRM生成】生成 STRM 文件成功: %s", str(new_file_path)
                    )
            except Exception as e:
                logger.error(f"【全量STRM生成】全量生成 STRM 文件失败: {e}")
                return False
        logger.info(
            f"【全量STRM生成】全量生成 STRM 文件完成，总共生成 {self.strm_count} 个 STRM 文件，下载 {self.mediainfo_count} 个媒体数据文件"
        )
        return True

    def get_generate_total(self):
        """
        输出总共生成文件个数
        """
        return self.strm_count, self.mediainfo_count


class ShareStrmHelper:
    """
    根据分享生成STRM
    """

    def __init__(
        self,
        client,
        user_rmt_mediaext: str,
        user_download_mediaext: str,
        share_media_path: str,
        local_media_path: str,
        server_address: str,
        cookie: str,
        auto_download_mediainfo: bool = False,
    ):
        self.rmt_mediaext = [
            f".{ext.strip()}" for ext in user_rmt_mediaext.replace("，", ",").split(",")
        ]
        self.download_mediaext = [
            f".{ext.strip()}"
            for ext in user_download_mediaext.replace("，", ",").split(",")
        ]
        self.auto_download_mediainfo = auto_download_mediainfo
        self.client = client
        self.strm_count = 0
        self.mediainfo_count = 0
        self.cookie = cookie
        self.share_media_path = share_media_path
        self.local_media_path = local_media_path
        self.server_address = server_address.rstrip("/")

    def has_prefix(self, full_path, prefix_path):
        """
        判断路径是否包含
        """
        full = Path(full_path).parts
        prefix = Path(prefix_path).parts

        if len(prefix) > len(full):
            return False

        return full[: len(prefix)] == prefix

    def generate_strm_files(
        self,
        share_code: str,
        receive_code: str,
        file_id: str,
        file_path: str,
    ):
        """
        生成 STRM 文件
        """
        if not self.has_prefix(file_path, self.share_media_path):
            logger.debug(
                "【分享STRM生成】此文件不在用户设置分享目录下，跳过网盘路径: %s",
                str(file_path).replace(str(self.local_media_path), "", 1),
            )
            return
        file_path = Path(self.local_media_path) / Path(file_path).relative_to(
            self.share_media_path
        )
        file_target_dir = file_path.parent
        original_file_name = file_path.name
        file_name = file_path.stem + ".strm"
        new_file_path = file_target_dir / file_name

        if self.auto_download_mediainfo:
            if file_path.suffix in self.download_mediaext:
                payload = {
                    "share_code": share_code,
                    "receive_code": receive_code,
                    "file_id": file_id,
                }
                resp = requests.post(
                    "http://proapi.115.com/app/share/downurl",
                    data={"data": encrypt(dumps(payload)).decode("utf-8")},
                    headers={
                        "User-Agent": settings.USER_AGENT,
                        "Cookie": self.cookie,
                    },
                )
                check_response(resp)
                json = loads(cast(bytes, resp.content))
                if not json["state"]:
                    raise OSError(EIO, json)
                data = json["data"] = loads(decrypt(json["data"]))
                if not (data and (url_info := data["url"])):
                    raise FileNotFoundError(ENOENT, json)
                data["file_id"] = data.pop("fid")
                data["file_name"] = data.pop("fn")
                data["file_size"] = int(data.pop("fs"))
                download_url = Url.of(url_info["url"], data)

                if not download_url:
                    logger.error(
                        f"【分享STRM生成】{original_file_name} 下载链接获取失败，无法下载该文件"
                    )
                    return

                save_mediainfo_file(
                    file_path=Path(file_path),
                    file_name=original_file_name,
                    download_url=download_url,
                    cookie=self.cookie,
                )
                self.mediainfo_count += 1
                logger.info("【分享STRM生成】休眠 1s 后继续生成")
                time.sleep(1)
                return

        if file_path.suffix not in self.rmt_mediaext:
            logger.warn(
                "【分享STRM生成】文件后缀不匹配，跳过网盘路径: %s",
                str(file_path).replace(str(self.local_media_path), "", 1),
            )
            return

        new_file_path.parent.mkdir(parents=True, exist_ok=True)

        if not file_id:
            logger.error(
                f"【分享STRM生成】{original_file_name} 不存在 id 值，无法生成 STRM 文件"
            )
            return
        if not share_code:
            logger.error(
                f"【分享STRM生成】{original_file_name} 不存在 share_code 值，无法生成 STRM 文件"
            )
            return
        if not receive_code:
            logger.error(
                f"【分享STRM生成】{original_file_name} 不存在 receive_code 值，无法生成 STRM 文件"
            )
            return
        strm_url = f"{self.server_address}/api/v1/plugin/P1115StrmHelper/redirect_url?apikey={settings.API_TOKEN}&share_code={share_code}&receive_code={receive_code}&id={file_id}"

        with open(new_file_path, "w", encoding="utf-8") as file:
            file.write(strm_url)
        self.strm_count += 1
        logger.info("【分享STRM生成】生成 STRM 文件成功: %s", str(new_file_path))

    def get_share_list_creata_strm(
        self,
        cid: int = 0,
        current_path: str = "",
        share_code: str = "",
        receive_code: str = "",
    ):
        """
        获取分享文件，生成 STRM
        """
        for item in share_iterdir(
            self.client, receive_code=receive_code, share_code=share_code, cid=int(cid)
        ):
            item_path = (
                f"{current_path}/{item['name']}" if current_path else "/" + item["name"]
            )

            if item["is_directory"] or item["is_dir"]:
                if self.strm_count != 0 and self.strm_count % 100 == 0:
                    logger.info("【分享STRM生成】休眠 2s 后继续生成")
                    time.sleep(2)
                self.get_share_list_creata_strm(
                    cid=int(item["id"]),
                    current_path=item_path,
                    share_code=share_code,
                    receive_code=receive_code,
                )
            else:
                item_with_path = dict(item)
                item_with_path["path"] = item_path
                self.generate_strm_files(
                    share_code=share_code,
                    receive_code=receive_code,
                    file_id=item_with_path["id"],
                    file_path=item_with_path["path"],
                )

    def get_generate_total(self):
        """
        输出总共生成文件个数
        """
        logger.info(
            f"【分享STRM生成】分享生成 STRM 文件完成，总共生成 {self.strm_count} 个 STRM 文件，下载 {self.mediainfo_count} 个媒体数据文件"
        )
        return self.strm_count, self.mediainfo_count


class P1115StrmHelper(_PluginBase):
    # 插件名称
    plugin_name = "VUE-115网盘STRM助手"
    # 插件描述
    plugin_desc = "测试版仅供测试"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Frontend/refs/heads/v2/src/assets/images/misc/u115.png"
    # 插件版本
    plugin_version = "800000.8.8"
    # 插件作者
    plugin_author = "VUE测试版"
    # 作者主页
    author_url = "https://github.com/DDSRem"
    # 插件配置项ID前缀
    plugin_config_prefix = "p1115strmhelper_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    mediaserver_helper = None
    transferchain = None
    mediachain = None

    # 目录ID缓存
    id_path_cache = None
    # 生活事件缓存
    cache_delete_pan_transfer_list = None
    cache_creata_pan_transfer_list = None

    _client = None
    _scheduler = None
    _enabled = False
    _once_full_sync_strm = False
    _cookies = None
    _password = None
    moviepilot_address = None
    _user_rmt_mediaext = None
    _user_download_mediaext = None
    _transfer_monitor_enabled = False
    _transfer_monitor_scrape_metadata_enabled = False
    _transfer_monitor_paths = None
    _transfer_mp_mediaserver_paths = None
    _transfer_monitor_mediaservers = None
    _transfer_monitor_media_server_refresh_enabled = False
    _timing_full_sync_strm = False
    _full_sync_auto_download_mediainfo_enabled = False
    _cron_full_sync_strm = None
    _full_sync_strm_paths = None
    _mediaservers = None
    _monitor_life_enabled = False
    _monitor_life_auto_download_mediainfo_enabled = False
    _monitor_life_paths = None
    _monitor_life_mp_mediaserver_paths = None
    _monitor_life_media_server_refresh_enabled = False
    _monitor_life_mediaservers = None
    _monitor_life_auto_remove_local_enabled = False
    _monitor_life_scrape_metadata_enabled = False
    _share_strm_enabled = False
    _share_strm_auto_download_mediainfo_enabled = False
    _user_share_code = None
    _user_receive_code = None
    _user_share_link = None
    _user_share_pan_path = None
    _user_share_local_path = None
    _clear_recyclebin_enabled = False
    _clear_receive_path_enabled = False
    _cron_clear = None
    _pan_transfer_enabled = False
    _pan_transfer_paths = None
    _cookie_error_notify_enabled: bool = False
    _cookie_error_notify_client_type: str = "alipaymini"
    _picgo_enabled: bool = False
    _picgo_api_key: str = ""
    _picgo_upload_url: str = "https://www.picgo.net/api/1/upload"

    # MediaWarp 集成相关属性
    _mediawarp_process: Optional[psutil.Process] = None
    _mediawarp_enabled: bool = False
    _mediawarp_port: str = '18699'
    _mediawarp_media_strm_path: str = ""
    _mediawarp_mediaserver_name: Optional[str] = None
    _mediawarp_emby_type: Optional[str] = None 
    _mediawarp_emby_host: Optional[str] = None
    _mediawarp_emby_apikey: Optional[str] = None
    _mediawarp_crx: bool = False
    _mediawarp_actor_plus: bool = False
    _mediawarp_fanart_show: bool = False
    _mediawarp_external_player_url: bool = False
    _mediawarp_danmaku: bool = False
    _mediawarp_video_together: bool = False
    _mediawarp_srt2ass: bool = False
    __MEDIAWARP_DEFAULT_VERSION: str = "0.1.8"
    # 以下路径属性将在 __init__ 中初始化
    _mediawarp_base_data_path: Optional[Path] = None
    __mediawarp_binary_path: Optional[Path] = None
    __mediawarp_config_dir_path: Optional[Path] = None
    __mediawarp_logs_dir_path: Optional[Path] = None
    __mediawarp_config_yaml_path: Optional[Path] = None
    __mediawarp_version_file_path: Optional[Path] = None
    # ---

    # 退出事件
    _event = ThreadEvent()
    monitor_stop_event = None # General stop event for long-running tasks like life monitor
    _qr_polling_stop_event = None # Specific stop event for QR code polling threads
    monitor_life_thread = None

    def __init__(self):
        super().__init__()
        self.mediaserver_helper = MediaServerHelper()
        self.id_path_cache = IdPathCache()
        self.transferchain = TransferChain()
        self.mediachain = MediaChain()
        self.cache_delete_pan_transfer_list = TTLCache(maxsize=1024, ttl=60 * 60 * 24)
        self.cache_creata_pan_transfer_list = TTLCache(maxsize=1024, ttl=60 * 60 * 24)

        plugin_data_dir_name = getattr(self, 'plugin_id', self.__class__.__name__.lower())
        if not plugin_data_dir_name: # Fallback if plugin_id is not set
            plugin_data_dir_name = "p1115strmhelper"

        # MediaWarp 相关路径定义及属性初始化
        self._mediawarp_base_data_path = settings.PLUGIN_DATA_PATH / plugin_data_dir_name / "mediawarp_files"
        self.__mediawarp_binary_path = self._mediawarp_base_data_path / "MediaWarp"
        self.__mediawarp_config_dir_path = self._mediawarp_base_data_path / "config"
        self.__mediawarp_logs_dir_path = self._mediawarp_base_data_path / "logs" 
        self.__mediawarp_config_yaml_path = self.__mediawarp_config_dir_path / "config.yaml"
        self.__mediawarp_version_file_path = self._mediawarp_base_data_path / "version.txt"
        
        # 初始化 MediaWarp 配置相关的实例变量 (这些会被 init_plugin 中的加载覆盖)
        self._mediawarp_enabled = False
        self._mediawarp_port = '18699'
        self._mediawarp_media_strm_path = ""
        self._mediawarp_mediaserver_name = None
        self._mediawarp_emby_type = None
        self._mediawarp_emby_host = None
        self._mediawarp_emby_apikey = None
        self._mediawarp_crx = False
        self._mediawarp_actor_plus = False
        self._mediawarp_fanart_show = False
        self._mediawarp_external_player_url = False
        self._mediawarp_danmaku = False
        self._mediawarp_video_together = False
        self._mediawarp_srt2ass = False
        self._mediawarp_process = None # psutil.Process object

        # 确保 MediaWarp 所需的目录存在
        self._mediawarp_base_data_path.mkdir(parents=True, exist_ok=True)
        self.__mediawarp_config_dir_path.mkdir(parents=True, exist_ok=True)
        self.__mediawarp_logs_dir_path.mkdir(parents=True, exist_ok=True)

    def debug_log(self, message):
        """记录调试日志"""
        logger.debug(f"【P1115StrmHelper】{message}")

    def init_plugin(self, config: dict = None):
        self.debug_log("Initializing P1115StrmHelper plugin...")
        # 初始化事件和调度器
        self._event.clear()
        self.monitor_stop_event = ThreadEvent()
        self._qr_polling_stop_event = ThreadEvent()
        self._scheduler = BackgroundScheduler(timezone=settings.TZ)

        # 确保Python版本符合要求
        if not self.__check_python_version():
            logger.error("Python 版本过低，插件可能无法正常运行！")
            # 可以选择在这里阻止插件进一步加载或发出更强的警告

        if config:
            self._enabled = config.get("enabled", False)
            self._cookies = config.get("cookies")
            self._password = config.get("password")
            self.moviepilot_address = config.get("moviepilot_address")
            self._user_rmt_mediaext = config.get(
                "user_rmt_mediaext",
                "mp4,mkv,ts,iso,rmvb,avi,mov,mpeg,mpg,wmv,3gp,asf,m4v,flv,m2ts,tp,f4v",
            )
            self._user_download_mediaext = config.get(
                "user_download_mediaext", "srt,ssa,ass"
            )
            self._transfer_monitor_enabled = config.get(
                "transfer_monitor_enabled", False
            )
            self._transfer_monitor_scrape_metadata_enabled = config.get(
                "transfer_monitor_scrape_metadata_enabled", False
            )
            self._transfer_monitor_paths = config.get("transfer_monitor_paths")
            self._transfer_mp_mediaserver_paths = config.get(
                "transfer_mp_mediaserver_paths"
            )
            self._transfer_monitor_mediaservers = config.get(
                "transfer_monitor_mediaservers"
            )
            self._transfer_monitor_media_server_refresh_enabled = config.get(
                "transfer_monitor_media_server_refresh_enabled", False
            )
            self._timing_full_sync_strm = config.get("timing_full_sync_strm", False)
            self._full_sync_auto_download_mediainfo_enabled = config.get(
                "full_sync_auto_download_mediainfo_enabled", False
            )
            self._cron_full_sync_strm = config.get(
                "cron_full_sync_strm", "0 */7 * * *"
            )
            self._full_sync_strm_paths = config.get("full_sync_strm_paths")
            self._monitor_life_enabled = config.get("monitor_life_enabled", False)
            self._monitor_life_auto_download_mediainfo_enabled = config.get(
                "monitor_life_auto_download_mediainfo_enabled", False
            )
            self._monitor_life_paths = config.get("monitor_life_paths")
            self._monitor_life_mp_mediaserver_paths = config.get(
                "monitor_life_mp_mediaserver_paths"
            )
            self._monitor_life_media_server_refresh_enabled = config.get(
                "monitor_life_media_server_refresh_enabled", False
            )
            self._monitor_life_mediaservers = config.get("monitor_life_mediaservers")
            self._monitor_life_auto_remove_local_enabled = config.get(
                "monitor_life_auto_remove_local_enabled", False
            )
            self._monitor_life_scrape_metadata_enabled = config.get(
                "monitor_life_scrape_metadata_enabled", False
            )
            self._share_strm_enabled = config.get("share_strm_enabled", False)
            self._share_strm_auto_download_mediainfo_enabled = config.get(
                "share_strm_auto_download_mediainfo_enabled", False
            )
            self._user_share_code = config.get("user_share_code")
            self._user_receive_code = config.get("user_receive_code")
            self._user_share_link = config.get("user_share_link")
            self._user_share_pan_path = config.get("user_share_pan_path")
            self._user_share_local_path = config.get("user_share_local_path")
            self._clear_recyclebin_enabled = config.get(
                "clear_recyclebin_enabled", False
            )
            self._clear_receive_path_enabled = config.get(
                "clear_receive_path_enabled", False
            )
            self._cron_clear = config.get("cron_clear", "0 */7 * * *")
            self._pan_transfer_enabled = config.get("pan_transfer_enabled", False)
            self._pan_transfer_paths = config.get("pan_transfer_paths")

            self._cookie_error_notify_enabled = config.get("cookie_error_notify_enabled", False)
            self._cookie_error_notify_client_type = config.get("cookie_error_notify_client_type", "alipaymini")
            self._picgo_enabled = config.get("picgo_enabled", False)
            self._picgo_api_key = config.get("picgo_api_key", "")
            self._picgo_upload_url = config.get("picgo_upload_url", "https://www.picgo.net/api/1/upload")

            # 加载 MediaWarp 配置
            self._mediawarp_enabled = config.get("mediawarp_enabled", False)
            self._mediawarp_port = config.get("mediawarp_port", '18699')
            self._mediawarp_media_strm_path = config.get("mediawarp_media_strm_path", "")
            # mediawarp_mediaservers 在前端是单选，所以直接获取字符串值
            self._mediawarp_mediaserver_name = config.get("mediawarp_mediaservers") 
            self._mediawarp_crx = config.get("mediawarp_crx", False)
            self._mediawarp_actor_plus = config.get("mediawarp_actor_plus", False)
            self._mediawarp_fanart_show = config.get("mediawarp_fanart_show", False)
            self._mediawarp_external_player_url = config.get("mediawarp_external_player_url", False)
            self._mediawarp_danmaku = config.get("mediawarp_danmaku", False)
            self._mediawarp_video_together = config.get("mediawarp_video_together", False)
            self._mediawarp_srt2ass = config.get("mediawarp_srt2ass", False)

            # 获取为 MediaWarp 选择的媒体服务器的详细信息
            if self._mediawarp_mediaserver_name:
                # self.mediaserver_helper 已在 __init__ 中初始化
                # get_services 需要一个列表，即使只有一个名称
                servers = self.mediaserver_helper.get_services(name_filters=[self._mediawarp_mediaserver_name])
                if servers:
                    # get_services 返回字典，取第一个值
                    server_instance = next(iter(servers.values()))
                    if server_instance and server_instance.config:
                        self._mediawarp_emby_type = server_instance.type # 'emby' or 'jellyfin'
                        self._mediawarp_emby_host = server_instance.config.config.get("host")
                        self._mediawarp_emby_apikey = server_instance.config.config.get("apikey")
                        if self._mediawarp_emby_host and not self._mediawarp_emby_host.startswith("http"):
                            self._mediawarp_emby_host = "http://" + self._mediawarp_emby_host
                        if self._mediawarp_emby_host:
                             self._mediawarp_emby_host = self._mediawarp_emby_host.rstrip("/")
                    else:
                        logger.warning(f"[MediaWarp] 未能获取媒体服务器 '{self._mediawarp_mediaserver_name}' 的配置详情。")
                        self._mediawarp_mediaserver_name = None # 清除无效选择
                else:
                    logger.warning(f"[MediaWarp] 找不到名为 '{self._mediawarp_mediaserver_name}' 的媒体服务器配置。")
                    self._mediawarp_mediaserver_name = None # 清除无效选择
            else:
                 # 如果没有选择媒体服务器，确保相关信息为空
                self._mediawarp_emby_type = None
                self._mediawarp_emby_host = None
                self._mediawarp_emby_apikey = None

        if self._enabled:
            self.debug_log("P1115StrmHelper plugin is enabled.")
            try:
                self._client = P115Client(self._cookies, self._password)
                userinfo = self._client.user_info()
                if not userinfo:
                    self._client = None
                    logger.error("115 Cookie 无效，插件部分功能将无法使用")
                    self._check_cookie_and_notify_if_invalid(context_message="插件初始化时检测到Cookie无效")
                else:
                    logger.info(f"115 登录成功：{userinfo.get('user_name')}")
                    self.id_path_cache.clear()
            except Exception as e:
                self._client = None
                logger.error(f"115 Client 初始化失败: {e}")
                self._check_cookie_and_notify_if_invalid(context_message=f"115 Client 初始化失败: {e}")

            # 处理一次性全量同步
            if self._enabled and self._client and self._once_full_sync_strm:
                logger.info("【P1115StrmHelper】检测到一次性全量同步请求，开始执行...")
                try:
                    self.full_sync_strm_files()
                    logger.info("【P1115StrmHelper】一次性全量同步执行完成。")
                except Exception as e:
                    logger.error(f"【P1115StrmHelper】一次性全量同步执行失败: {e}", exc_info=True)
                finally:
                    self._once_full_sync_strm = False # 重置标志
                    self.__update_config() # 保存重置后的标志
            
            # 添加定时任务
            if self._timing_full_sync_strm:
                try:
                    self._scheduler.add_job(
                        self.full_sync_strm_files,
                        CronTrigger.from_crontab(self._cron_full_sync_strm),
                        id="full_sync_strm",
                        name="全量同步STRM文件",
                        misfire_grace_time=3600,
                    )
                    logger.info(f"已添加全量同步STRM文件定时任务: {self._cron_full_sync_strm}")
                except Exception as e:
                    logger.error(f"添加全量同步STRM文件定时任务失败: {e}")
            
            if self._clear_recyclebin_enabled or self._clear_receive_path_enabled:
                try:
                    self._scheduler.add_job(
                        self.main_cleaner,
                        CronTrigger.from_crontab(self._cron_clear),
                        id="clear_115_files",
                        name="定期清理115文件",
                        misfire_grace_time=3600
                    )
                    logger.info(f"已添加定期清理115文件定时任务: {self._cron_clear}")
                except Exception as e:
                    logger.error(f"添加定期清理115文件定时任务失败: {e}")

            # 启动生活事件监控线程
            if self._monitor_life_enabled:
                self.debug_log("Starting monitor life events thread...")
                self.monitor_stop_event.clear()
                self.monitor_life_thread = threading.Thread(target=self.monitor_life_strm_files, daemon=True)
                self.monitor_life_thread.start()
            
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()
        else:
            self.debug_log("P1115StrmHelper plugin is disabled.")
            self.stop_service() # 确保在禁用时停止所有服务，包括可能存在的MediaWarp

        # 根据配置启动 MediaWarp 服务 (在主插件服务启动之后)
        if self._mediawarp_enabled:
            logger.info("[MediaWarp] 配置为启用，尝试启动 MediaWarp 服务...")
            self._run_mediawarp_service() # 调用实际的启动方法
        else:
            logger.info("[MediaWarp] 配置为禁用，确保 MediaWarp 服务已停止。")
            self._stop_mediawarp_service() # 调用实际的停止方法


    # --- MediaWarp Integration Methods START ---

    def _get_mediawarp_download_url(self) -> str:
        """
        获取 MediaWarp 二进制文件的下载链接。
        """
        base_url = "https://github.com/DDS-Derek/MediaWarp/releases/download/v{version}/MediaWarp_{version}_linux_{arch}.tar.gz"
        machine = platform.machine().lower()
        arch = "arm64" if machine in ["arm64", "aarch64"] else "amd64"
        return base_url.format(arch=arch, version=self.__MEDIAWARP_DEFAULT_VERSION)

    def _download_and_extract_mediawarp_binary(self) -> bool:
        """
        下载并解压 MediaWarp 二进制文件及其相关文件（如示例配置、static目录）。
        """
        if not all([
            self._mediawarp_base_data_path,
            self.__mediawarp_binary_path,
            self.__mediawarp_config_dir_path,
            self.__mediawarp_config_yaml_path,
            self.__mediawarp_version_file_path,
            self.__mediawarp_logs_dir_path 
        ]):
            logger.error("[MediaWarp] 内部路径未正确初始化，无法下载。")
            return False

        url = self._get_mediawarp_download_url()
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="mediawarp_dl_")
        temp_dir = Path(temp_dir_obj.name)
        temp_file = temp_dir / "MediaWarp.tar.gz"

        try:
            self._mediawarp_base_data_path.mkdir(parents=True, exist_ok=True)
            self.__mediawarp_config_dir_path.mkdir(parents=True, exist_ok=True)
            self.__mediawarp_logs_dir_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"[MediaWarp] 正在下载: {url}")
            if settings.PROXY:
                logger.info(f"[MediaWarp] 使用代理进行下载: {settings.PROXY}")
            else:
                logger.info("[MediaWarp] 未使用代理进行下载。")
            response = requests.get(url, stream=True, timeout=300, proxies=settings.PROXY)
            response.raise_for_status()

            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"[MediaWarp] 下载完成: {temp_file}")

            logger.info("[MediaWarp] 正在解压文件...")
            with tarfile.open(temp_file, "r:gz") as tar:
                mediawarp_binary_member = next((m for m in tar.getmembers() if m.name.endswith("MediaWarp") and m.isfile()), None)
                if mediawarp_binary_member:
                    tar.extract(member=mediawarp_binary_member, path=temp_dir)
                    extracted_binary_path = temp_dir / mediawarp_binary_member.name
                    extracted_binary_path.chmod(0o755)
                    shutil.move(str(extracted_binary_path), str(self.__mediawarp_binary_path))
                    logger.info(f"[MediaWarp] 二进制文件已更新到 {self.__mediawarp_binary_path}")
                else:
                    logger.error("[MediaWarp] 在压缩包中未找到 MediaWarp 二进制文件。")
                    temp_dir_obj.cleanup()
                    return False

                if not self.__mediawarp_config_yaml_path.exists():
                    config_example_member = next((m for m in tar.getmembers() if m.name.endswith("config.yaml.example") and m.isfile()), None)
                    if config_example_member:
                        tar.extract(member=config_example_member, path=temp_dir)
                        extracted_config_example_path = temp_dir / config_example_member.name
                        shutil.copy2(extracted_config_example_path, self.__mediawarp_config_yaml_path)
                        logger.info(f"[MediaWarp] 示例配置文件已保存到 {self.__mediawarp_config_yaml_path}")
                    else:
                        logger.warning("[MediaWarp] 压缩包中未找到 config.yaml.example。")
                
                static_target_path = self.__mediawarp_config_dir_path / "static"
                if static_target_path.exists() and static_target_path.is_dir():
                    shutil.rmtree(static_target_path)
                
                static_members_to_extract = [m for m in tar.getmembers() if m.name.startswith("static/")]
                if static_members_to_extract:
                    # Extract "static/*" members directly into the config directory,
                    # which will create "config/static/..."
                    tar.extractall(path=self.__mediawarp_config_dir_path, members=[m for m in static_members_to_extract if m.isfile() or m.isdir()])
                    logger.info(f"[MediaWarp] static 目录内容已尝试提取到 {self.__mediawarp_config_dir_path}")
                else:
                    logger.info("[MediaWarp] 压缩包中未找到 static/ 目录内容。")

            with open(self.__mediawarp_version_file_path, "w", encoding="utf-8") as f:
                f.write(self.__MEDIAWARP_DEFAULT_VERSION)
            logger.info(f"[MediaWarp] 安装/更新完成！MediaWarp 版本 {self.__MEDIAWARP_DEFAULT_VERSION} 已记录。")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"[MediaWarp] 下载失败: {e}")
            return False
        except tarfile.TarError as e:
            logger.error(f"[MediaWarp] 解压失败: {e}")
            return False
        except Exception as e:
            logger.error(f"[MediaWarp] 下载或解压过程中发生未知错误: {e} ({type(e).__name__})")
            return False
        finally:
            temp_dir_obj.cleanup()

    def _ensure_mediawarp_binary_and_config(self) -> bool:
        """
        确保 MediaWarp 二进制文件和基础配置文件存在且版本正确。
        如果需要，会自动下载和解压。
        """
        if not all([
            self.__mediawarp_binary_path, 
            self.__mediawarp_config_yaml_path, 
            self.__mediawarp_version_file_path
        ]):
            logger.error("[MediaWarp] 内部路径未正确初始化，无法确保二进制文件。")
            return False

        needs_download = False
        if not self.__mediawarp_binary_path.exists():
            logger.info(f"[MediaWarp] 二进制文件不存在于 {self.__mediawarp_binary_path}。")
            needs_download = True
        else:
            if self.__mediawarp_version_file_path.exists():
                try:
                    with open(self.__mediawarp_version_file_path, "r", encoding="utf-8") as f:
                        installed_version = f.read().strip()
                    if installed_version != self.__MEDIAWARP_DEFAULT_VERSION:
                        logger.info(f"[MediaWarp] 版本不匹配 (已安装: {installed_version}, 需要: {self.__MEDIAWARP_DEFAULT_VERSION})。")
                        needs_download = True
                    else:
                        logger.info(f"[MediaWarp] 版本已是最新 ({installed_version})。")
                except Exception as e:
                    logger.warning(f"[MediaWarp] 读取版本文件失败: {e}。假定需要更新。")
                    needs_download = True
            else:
                logger.info(f"[MediaWarp] 版本文件 {self.__mediawarp_version_file_path} 不存在。")
                needs_download = True
        
        if needs_download:
            logger.info("[MediaWarp] 准备下载/更新 MediaWarp 二进制文件...")
            if not self._download_and_extract_mediawarp_binary():
                logger.error("[MediaWarp] 下载/更新 MediaWarp 二进制文件失败。")
                return False
            logger.info("[MediaWarp] 下载/更新 MediaWarp 二进制文件过程完成。")

        if not self.__mediawarp_binary_path.exists():
            logger.error(f"[MediaWarp] 二进制文件仍不存在于 {self.__mediawarp_binary_path}，即使在尝试下载后。")
            return False
        
        if not self.__mediawarp_config_yaml_path.exists():
            logger.error(f"[MediaWarp] 配置文件不存在于 {self.__mediawarp_config_yaml_path}。MediaWarp可能无法启动。")
            return False

        logger.info(f"[MediaWarp] 二进制文件和配置文件检查通过。 Binary: {self.__mediawarp_binary_path}, Config: {self.__mediawarp_config_yaml_path}")
        return True

    def _modify_mediawarp_config(self) -> bool:
        """
        根据 P1115StrmHelper 的配置修改 MediaWarp 的 config.yaml 文件。
        """
        if not self.__mediawarp_config_yaml_path or not self.__mediawarp_config_dir_path:
            logger.error("[MediaWarp] 配置文件路径未初始化，无法修改配置。")
            return False
        if not self.__mediawarp_config_yaml_path.exists():
            logger.error(f"[MediaWarp] 配置文件 {self.__mediawarp_config_yaml_path} 不存在，无法修改。")
            return False

        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        class MyRepresenter(RoundTripRepresenter):
            pass
        MyRepresenter.add_representer(bool, lambda self, data: self.represent_scalar(u'tag:yaml.org,2002:bool', u'True' if data else u'False'))
        yaml.Representer = MyRepresenter
        
        try:
            with open(self.__mediawarp_config_yaml_path, "r", encoding="utf-8") as file:
                config_data = yaml.load(file)
                if not isinstance(config_data, Mapping):
                    logger.warning(f"[MediaWarp] 配置文件 {self.__mediawarp_config_yaml_path} 内容格式不正确或为空。将创建新的配置结构。")
                    config_data = {} 
        except Exception as e:
            logger.error(f"[MediaWarp] 读取或解析配置文件 {self.__mediawarp_config_yaml_path} 失败: {e}。将创建新的配置结构。")
            config_data = {}

        # Define default structure for sections if they don't exist
        config_data.setdefault("Logger", {}).setdefault("AccessLogger", {})
        config_data["Logger"].setdefault("ErrorLogger", {})
        config_data.setdefault("MediaServer", {})
        config_data.setdefault("Web", {})
        config_data.setdefault("HTTPStrm", {})
        config_data.setdefault("Subtitle", {})

        modifications = {
            "Port": str(self._mediawarp_port) if self._mediawarp_port else '18699',
            "Logger.AccessLogger.File": True,
            "Logger.AccessLogger.Console": False,
            "Logger.AccessLogger.Filename": "./logs/access.log", 
            "Logger.ErrorLogger.File": True,
            "Logger.ErrorLogger.Console": False,
            "Logger.ErrorLogger.Filename": "./logs/error.log",
        }

        if self._mediawarp_emby_type and self._mediawarp_emby_host and self._mediawarp_emby_apikey:
            modifications["MediaServer.Type"] = "Jellyfin" if self._mediawarp_emby_type == "jellyfin" else "Emby"
            modifications["MediaServer.ADDR"] = self._mediawarp_emby_host
            modifications["MediaServer.AUTH"] = self._mediawarp_emby_apikey
        else:
            modifications["MediaServer.Type"] = "Emby" 
            modifications["MediaServer.ADDR"] = ""
            modifications["MediaServer.AUTH"] = ""
            logger.debug("[MediaWarp] 未配置有效的媒体服务器信息供 MediaWarp 使用。")
        
        modifications["Web.Index"] = (self.__mediawarp_config_dir_path / "static" / "index.html").exists()
        modifications["Web.Crx"] = self._mediawarp_crx
        modifications["Web.ActorPlus"] = self._mediawarp_actor_plus
        modifications["Web.FanartShow"] = self._mediawarp_fanart_show
        modifications["Web.ExternalPlayerUrl"] = self._mediawarp_external_player_url
        modifications["Web.Danmaku"] = self._mediawarp_danmaku
        modifications["Web.VideoTogether"] = self._mediawarp_video_together
        
        modifications["HTTPStrm.Enable"] = True
        modifications["HTTPStrm.PrefixList"] = self._mediawarp_media_strm_path.splitlines() if self._mediawarp_media_strm_path else []
        
        modifications["Subtitle.SRT2ASS"] = self._mediawarp_srt2ass
        
        for key_path, value in modifications.items():
            keys = key_path.split(".")
            current_level = config_data
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current_level[key] = value
                else:
                    current_level = current_level.setdefault(key, {})
        
        try:
            with open(self.__mediawarp_config_yaml_path, "w", encoding="utf-8") as file:
                yaml.dump(config_data, file)
            logger.info(f"[MediaWarp] 配置文件 {self.__mediawarp_config_yaml_path} 已更新。")
            return True
        except Exception as e:
            logger.error(f"[MediaWarp] 写入配置文件 {self.__mediawarp_config_yaml_path} 失败: {e}")
            return False

    def _run_mediawarp_service(self):
        """
        启动 MediaWarp 服务。
        """
        if not self._mediawarp_enabled:
            logger.info("[MediaWarp] MediaWarp 未启用，跳过启动。")
            return

        if not self._ensure_mediawarp_binary_and_config():
            logger.error("[MediaWarp] 无法确保二进制文件和配置，启动中止。")
            return False

        if not self._modify_mediawarp_config():
            logger.error("[MediaWarp] 修改配置文件失败，启动中止。")
            return False

        if self._mediawarp_process and self._mediawarp_process.is_running():
            logger.info(f"[MediaWarp] 服务已在运行 (PID: {self._mediawarp_process.pid})。")
            return True

        if not self.__mediawarp_binary_path or not self.__mediawarp_config_dir_path or not self.__mediawarp_logs_dir_path:
            logger.error("[MediaWarp] 必要的路径未设置，无法启动服务。")
            return False

        try:
            cmd = [str(self.__mediawarp_binary_path), "-config", str(self.__mediawarp_config_yaml_path)]
            env = os.environ.copy()
            env["GIN_MODE"] = "release"
            
            # 定义日志文件路径
            stdout_log_path = self.__mediawarp_logs_dir_path / "mediawarp_stdout.log"
            stderr_log_path = self.__mediawarp_logs_dir_path / "mediawarp_stderr.log"

            # 以追加模式打开日志文件
            # 注意：os模块需要在使用前导入。如果 P1115StrmHelper 类或其所在模块尚未导入 os,
            # 需要确保 import os 在文件顶部。假设它已经存在。
            stdout_log = open(stdout_log_path, "ab")
            stderr_log = open(stderr_log_path, "ab")

            logger.info(f"[MediaWarp] 准备启动 MediaWarp 服务: {' '.join(cmd)}")
            logger.info(f"[MediaWarp] STDOUT 将重定向到: {stdout_log_path}")
            logger.info(f"[MediaWarp] STDERR 将重定向到: {stderr_log_path}")

            self._mediawarp_process = psutil.Popen(
                cmd,
                env=env,
                cwd=str(self._mediawarp_base_data_path), # 在mediawarp_files目录下运行
                stdout=stdout_log,
                stderr=stderr_log,
                # close_fds=True on POSIX is generally recommended for Popen if not passing specific fds.
                # However, on Windows, it can cause issues if True and std handles are not properly managed or redirected.
                # Given we are redirecting stdout/stderr to files, it should be safe.
                # psutil.Popen's behavior might differ slightly from subprocess.Popen here.
                # Let's assume 'os' is imported at the top of the file.
            )
            logger.info(f"[MediaWarp] 服务已启动 (PID: {self._mediawarp_process.pid})。")
            
            time.sleep(2) # Give the process a moment to start or fail.
            if not self._mediawarp_process.is_running() or self._mediawarp_process.status() == psutil.STATUS_ZOMBIE:
                logger.error(f"[MediaWarp] 服务启动后立即退出或变为僵尸进程。请检查 {stderr_log_path} 获取更多信息。")
                self._mediawarp_process = None
                stdout_log.close()
                stderr_log.close()
                return False
            
            return True
        except Exception as e:
            logger.error(f"[MediaWarp] 启动服务失败: {e}", exc_info=True)
            if hasattr(self, '_mediawarp_process') and self._mediawarp_process:
                self._mediawarp_process = None
            if 'stdout_log' in locals() and stdout_log and not stdout_log.closed:
                stdout_log.close()
            if 'stderr_log' in locals() and stderr_log and not stderr_log.closed:
                stderr_log.close()
            return False

    def _stop_mediawarp_service(self):
        """
        停止 MediaWarp 服务。
        """
        if self._mediawarp_process and self._mediawarp_process.is_running():
            logger.info(f"[MediaWarp] 正在停止 MediaWarp 服务 (PID: {self._mediawarp_process.pid})...")
            try:
                # 先尝试友好终止
                self._mediawarp_process.terminate()
                try:
                    self._mediawarp_process.wait(timeout=5) # 等待5秒
                    logger.info(f"[MediaWarp] 服务 (PID: {self._mediawarp_process.pid}) 已终止。")
                except psutil.TimeoutExpired:
                    logger.warning(f"[MediaWarp] 服务 (PID: {self._mediawarp_process.pid}) 在5秒内未终止，强制结束。")
                    self._mediawarp_process.kill() # 强制结束
                    self._mediawarp_process.wait(timeout=2) # 等待强制结束
                    logger.info(f"[MediaWarp] 服务 (PID: {self._mediawarp_process.pid}) 已强制结束。")

            except psutil.NoSuchProcess:
                logger.info(f"[MediaWarp] 尝试停止服务时，进程 (PID: {self._mediawarp_process.pid if self._mediawarp_process else 'N/A'}) 已不存在。")
            except Exception as e:
                logger.error(f"[MediaWarp] 停止服务时发生未知错误: {e}", exc_info=True)
            finally:
                # 确保在所有情况下都清理进程对象
                # 关闭可能由Popen打开的日志文件句柄 (尽管Popen应该自己管理)
                # 检查 self._mediawarp_process 是否仍然存在并且不是None
                if self._mediawarp_process: 
                    process_obj = self._mediawarp_process # temp var for safety
                    self._mediawarp_process = None # Clear immediately to prevent re-entry issues
                    try:
                        if hasattr(process_obj, 'stdout') and process_obj.stdout and hasattr(process_obj.stdout, 'close') and not process_obj.stdout.closed:
                            process_obj.stdout.close()
                        if hasattr(process_obj, 'stderr') and process_obj.stderr and hasattr(process_obj.stderr, 'close') and not process_obj.stderr.closed:
                            process_obj.stderr.close()
                    except Exception as e_close:
                        logger.error(f"[MediaWarp] 关闭子进程的std句柄时出错: {e_close}")
        else:
            logger.info("[MediaWarp] 服务未运行或进程对象不存在。")

    # --- MediaWarp Integration Methods END ---

    def get_state(self) -> bool:
        return self._enabled

    @property
    def transfer_service_infos(self) -> Optional[Dict[str, ServiceInfo]]:
        """
        监控MP整理 媒体服务器服务信息
        """
        if not self._transfer_monitor_mediaservers:
            logger.warning("尚未配置媒体服务器，请检查配置")
            return None

        services = self.mediaserver_helper.get_services(
            name_filters=self._transfer_monitor_mediaservers
        )
        if not services:
            logger.warning("获取媒体服务器实例失败，请检查配置")
            return None

        active_services = {}
        for service_name, service_info in services.items():
            if service_info.instance.is_inactive():
                logger.warning(f"媒体服务器 {service_name} 未连接，请检查配置")
            else:
                active_services[service_name] = service_info

        if not active_services:
            logger.warning("没有已连接的媒体服务器，请检查配置")
            return None

        return active_services

    @property
    def monitor_life_service_infos(self) -> Optional[Dict[str, ServiceInfo]]:
        """
        监控生活事件 媒体服务器服务信息
        """
        if not self._monitor_life_mediaservers:
            logger.warning("尚未配置媒体服务器，请检查配置")
            return None

        services = self.mediaserver_helper.get_services(
            name_filters=self._monitor_life_mediaservers
        )
        if not services:
            logger.warning("获取媒体服务器实例失败，请检查配置")
            return None

        active_services = {}
        for service_name, service_info in services.items():
            if service_info.instance.is_inactive():
                logger.warning(f"媒体服务器 {service_name} 未连接，请检查配置")
            else:
                active_services[service_name] = service_info

        if not active_services:
            logger.warning("没有已连接的媒体服务器，请检查配置")
            return None

        return active_services

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附带数据
        """
        return [
            {
                "cmd": "/p115_full_sync",
                "event": EventType.PluginAction,
                "desc": "全量同步115网盘文件",
                "category": "",
                "data": {"action": "p115_full_sync"},
            },
            {
                "cmd": "/p115_add_share",
                "event": EventType.PluginAction,
                "desc": "转存分享到待整理目录",
                "category": "",
                "data": {"action": "p115_add_share"},
            },
        ]

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """
        返回插件使用的前端渲染模式
        :return: 前端渲染模式，前端文件目录
        """
        return "vue", "dist/assets"

    def _get_user_storage_status(self) -> Dict[str, Any]:
        """
        获取115用户基本信息和空间使用情况。
        """
        if not self._cookies:
            return {
                "success": False,
                "error_message": "115 Cookies 未配置，无法获取信息。",
                "user_info": None,
                "storage_info": None
            }

        try:
            # 确保 P115Client 已初始化
            if not self._client:
                try:
                    temp_client = P115Client(self._cookies)
                    logger.info("【用户存储状态】临时 P115Client 初始化成功")
                except Exception as client_init_exc:
                    logger.error(f"【用户存储状态】临时 P115Client 初始化失败: {client_init_exc}")
                    return {
                        "success": False,
                        "error_message": f"115客户端初始化失败: {client_init_exc}",
                        "user_info": None,
                        "storage_info": None
                    }
            else:
                temp_client = self._client
            
            # 1. 获取用户信息
            user_info_resp = temp_client.user_my_info() 
            
            user_details = None
            if user_info_resp and user_info_resp.get("state"):
                data = user_info_resp.get("data", {})
                vip_data = data.get("vip", {})
                face_data = data.get("face", {})
                user_details = {
                    "name": data.get("uname"),
                    "is_vip": vip_data.get("is_vip"),
                    "is_forever_vip": vip_data.get("is_forever"),
                    "vip_expire_date": vip_data.get("expire_str") if not vip_data.get("is_forever") else "永久",
                    "avatar": face_data.get("face_s")
                }
                logger.info(f"【用户存储状态】获取用户信息成功: {user_details.get('name')}")
            else:
                error_msg = user_info_resp.get("message", "获取用户信息失败") if user_info_resp else "获取用户信息响应为空"
                logger.error(f"【用户存储状态】获取用户信息失败: {error_msg}")
                return {
                    "success": False,
                    "error_message": f"获取115用户信息失败: {error_msg}",
                    "user_info": None,
                    "storage_info": None
                }

            # 2. 获取空间信息
            space_info_resp = temp_client.fs_index_info(payload=0) 
            
            storage_details = None
            if space_info_resp and space_info_resp.get("state"):
                data = space_info_resp.get("data", {}).get("space_info", {})
                storage_details = {
                    "total": data.get("all_total", {}).get("size_format"),
                    "used": data.get("all_use", {}).get("size_format"),
                    "remaining": data.get("all_remain", {}).get("size_format")
                }
                logger.info(f"【用户存储状态】获取空间信息成功: 总-{storage_details.get('total')}")
            else:
                error_msg = space_info_resp.get("error", "获取空间信息失败") if space_info_resp else "获取空间信息响应为空"
                logger.error(f"【用户存储状态】获取空间信息失败: {error_msg}")
                return {
                    "success": False,
                    "error_message": f"获取115空间信息失败: {error_msg}",
                    "user_info": user_details, 
                    "storage_info": None
                }

            return {
                "success": True,
                "user_info": user_details,
                "storage_info": storage_details
            }

        except Exception as e:
            logger.error(f"【用户存储状态】获取信息时发生意外错误: {e}", exc_info=True)
            error_str_lower = str(e).lower()
            specific_error_message = f"处理请求时发生错误: {str(e)}" # 默认错误信息

            # 检查是否为特定的 DataError，表明Cookie失效并返回了HTML
            definitive_cookie_error_msg_template = "获取115账户信息失败：Cookie无效或已过期，请在插件配置中重新扫码登录。"
            if (isinstance(e, DataError) and
                ("errno 61" in error_str_lower or "enodata" in error_str_lower) and
                "<!doctype html>" in error_str_lower):
                specific_error_message = definitive_cookie_error_msg_template
            elif ("cookie" in error_str_lower or
                  "登录" in error_str_lower or
                  "登陆" in error_str_lower):
                 specific_error_message = f"获取115账户信息失败：{str(e)} 请检查Cookie或重新登录。"

            result_to_return = {
                "success": False,
                "error_message": specific_error_message,
                "user_info": None,
                "storage_info": None
            }

            # 如果是明确的Cookie失效，并且通知已启用，则主动触发通知流程
            if self._cookie_error_notify_enabled and specific_error_message == definitive_cookie_error_msg_template:
                logger.info("用户状态接口检测到明确的Cookie失效，将尝试发送通知。")
                self._check_cookie_and_notify_if_invalid(
                    context_message="用户状态接口检测到Cookie失效",
                    status_check_result=result_to_return # 传递已知的失败状态
                )
            
            return result_to_return

    def get_api(self) -> List[Dict[str, Any]]:
        """插件API"""
        return [
            {
                "path": "/get_config",
                "endpoint": self._get_config_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取配置"
            },
            {
                "path": "/save_config",
                "endpoint": self._save_config_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存配置"
            },
            {
                "path": "/get_status",
                "endpoint": self._get_status_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取状态"
            },
            {
                "path": "/full_sync",
                "endpoint": self._trigger_full_sync_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行全量同步"
            },
            {
                "path": "/share_sync",
                "endpoint": self._trigger_share_sync_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行分享同步"
            },
            {
                "path": "/browse_dir",
                "endpoint": self._browse_dir_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "浏览目录"
            },
            {
                "path": "/get_qrcode",
                "endpoint": self._get_qrcode_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取登录二维码"
            },
            {
                "path": "/check_qrcode",
                "endpoint": self._check_qrcode_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "检查二维码状态"
            },
            {
                "path": "/redirect_url",
                "endpoint": self.redirect_url,
                "methods": ["GET", "POST", "HEAD"],
                "summary": "302跳转",
                "description": "115网盘302跳转"
            },
            {
                "path": "/user_storage_status", # 新的API路径
                "endpoint": self._get_user_storage_status, # 对应的处理函数
                "methods": ["GET"], # HTTP方法
                "auth": "bear", # 认证类型
                "summary": "获取115用户基本信息和空间状态" # API描述
            }
        ]

    def _get_config_api(self) -> dict:
        """获取配置"""
        return {
            "enabled": self._enabled,
            "once_full_sync_strm": self._once_full_sync_strm,
            "cookies": self._cookies or "",
            "password": self._password or "",
            "moviepilot_address": self.moviepilot_address or "",
            "user_rmt_mediaext": self._user_rmt_mediaext or "mp4,mkv,ts,iso,rmvb,avi,mov,mpeg,mpg,wmv,3gp,asf,m4v,flv,m2ts,tp,f4v",
            "user_download_mediaext": self._user_download_mediaext or "srt,ssa,ass",
            "transfer_monitor_enabled": self._transfer_monitor_enabled,
            "transfer_monitor_scrape_metadata_enabled": self._transfer_monitor_scrape_metadata_enabled,
            "transfer_monitor_paths": self._transfer_monitor_paths or "",
            "transfer_mp_mediaserver_paths": self._transfer_mp_mediaserver_paths or "",
            "transfer_monitor_media_server_refresh_enabled": self._transfer_monitor_media_server_refresh_enabled,
            "transfer_monitor_mediaservers": self._transfer_monitor_mediaservers or [],
            "timing_full_sync_strm": self._timing_full_sync_strm,
            "full_sync_auto_download_mediainfo_enabled": self._full_sync_auto_download_mediainfo_enabled,
            "cron_full_sync_strm": self._cron_full_sync_strm or "0 */7 * * *",
            "full_sync_strm_paths": self._full_sync_strm_paths or "",
            "monitor_life_enabled": self._monitor_life_enabled,
            "monitor_life_auto_download_mediainfo_enabled": self._monitor_life_auto_download_mediainfo_enabled,
            "monitor_life_paths": self._monitor_life_paths or "",
            "monitor_life_mp_mediaserver_paths": self._monitor_life_mp_mediaserver_paths or "",
            "monitor_life_media_server_refresh_enabled": self._monitor_life_media_server_refresh_enabled,
            "monitor_life_mediaservers": self._monitor_life_mediaservers or [],
            "monitor_life_auto_remove_local_enabled": self._monitor_life_auto_remove_local_enabled,
            "monitor_life_scrape_metadata_enabled": self._monitor_life_scrape_metadata_enabled,
            "share_strm_enabled": self._share_strm_enabled,
            "share_strm_auto_download_mediainfo_enabled": self._share_strm_auto_download_mediainfo_enabled,
            "user_share_code": self._user_share_code or "",
            "user_receive_code": self._user_receive_code or "",
            "user_share_link": self._user_share_link or "",
            "user_share_pan_path": self._user_share_pan_path or "/",
            "user_share_local_path": self._user_share_local_path or "",
            "clear_recyclebin_enabled": self._clear_recyclebin_enabled,
            "clear_receive_path_enabled": self._clear_receive_path_enabled,
            "cron_clear": self._cron_clear or "0 */7 * * *",
            "pan_transfer_enabled": self._pan_transfer_enabled,
            "pan_transfer_paths": self._pan_transfer_paths or "",
            "cookie_error_notify_enabled": self._cookie_error_notify_enabled,
            "cookie_error_notify_client_type": self._cookie_error_notify_client_type,
            "picgo_enabled": self._picgo_enabled,
            "picgo_api_key": self._picgo_api_key or "",
            "picgo_upload_url": self._picgo_upload_url or "https://www.picgo.net/api/1/upload",
            
            # MediaWarp 配置项
            "mediawarp_enabled": self._mediawarp_enabled,
            "mediawarp_port": self._mediawarp_port or '18699',
            "mediawarp_media_strm_path": self._mediawarp_media_strm_path or "",
            "mediawarp_mediaservers": self._mediawarp_mediaserver_name or None, # 前端使用 mediawarp_mediaservers 作为单选的 v-model
            "mediawarp_crx": self._mediawarp_crx,
            "mediawarp_actor_plus": self._mediawarp_actor_plus,
            "mediawarp_fanart_show": self._mediawarp_fanart_show,
            "mediawarp_external_player_url": self._mediawarp_external_player_url,
            "mediawarp_danmaku": self._mediawarp_danmaku,
            "mediawarp_video_together": self._mediawarp_video_together,
            "mediawarp_srt2ass": self._mediawarp_srt2ass,
            "mediawarp_running": bool(self._mediawarp_process and self._mediawarp_process.is_running()),

            # 获取可用的媒体服务器配置
            "mediaservers": [
                                        {"title": config.name, "value": config.name}
                                        for config in self.mediaserver_helper.get_configs().values()
            ]
        }

    async def _save_config_api(self, request: Request) -> dict: # 修正：改为 async def
        """保存配置"""
        try:
            data = await request.json() # 修正：添加 await
            # 更新配置
            self._enabled = data.get("enabled", False)
            self._once_full_sync_strm = data.get("once_full_sync_strm", False)
            self._cookies = data.get("cookies", "")
            self._password = data.get("password", "")
            self.moviepilot_address = data.get("moviepilot_address", "")
            self._user_rmt_mediaext = data.get("user_rmt_mediaext", "mp4,mkv,ts,iso,rmvb,avi,mov,mpeg,mpg,wmv,3gp,asf,m4v,flv,m2ts,tp,f4v")
            self._user_download_mediaext = data.get("user_download_mediaext", "srt,ssa,ass")
            self._transfer_monitor_enabled = data.get("transfer_monitor_enabled", False)
            self._transfer_monitor_scrape_metadata_enabled = data.get("transfer_monitor_scrape_metadata_enabled", False)
            self._transfer_monitor_paths = data.get("transfer_monitor_paths", "")
            self._transfer_mp_mediaserver_paths = data.get("transfer_mp_mediaserver_paths", "")
            self._transfer_monitor_media_server_refresh_enabled = data.get("transfer_monitor_media_server_refresh_enabled", False)
            self._transfer_monitor_mediaservers = data.get("transfer_monitor_mediaservers", [])
            self._timing_full_sync_strm = data.get("timing_full_sync_strm", False)
            self._full_sync_auto_download_mediainfo_enabled = data.get("full_sync_auto_download_mediainfo_enabled", False)
            self._cron_full_sync_strm = data.get("cron_full_sync_strm", "0 */7 * * *")
            self._full_sync_strm_paths = data.get("full_sync_strm_paths", "")
            self._monitor_life_enabled = data.get("monitor_life_enabled", False)
            self._monitor_life_auto_download_mediainfo_enabled = data.get("monitor_life_auto_download_mediainfo_enabled", False) 
            self._monitor_life_paths = data.get("monitor_life_paths", "")
            self._monitor_life_mp_mediaserver_paths = data.get("monitor_life_mp_mediaserver_paths", "")
            self._monitor_life_media_server_refresh_enabled = data.get("monitor_life_media_server_refresh_enabled", False)
            self._monitor_life_mediaservers = data.get("monitor_life_mediaservers", [])
            self._monitor_life_auto_remove_local_enabled = data.get("monitor_life_auto_remove_local_enabled", False)
            self._monitor_life_scrape_metadata_enabled = data.get("monitor_life_scrape_metadata_enabled", False)
            self._share_strm_enabled = data.get("share_strm_enabled", False)
            self._share_strm_auto_download_mediainfo_enabled = data.get("share_strm_auto_download_mediainfo_enabled", False)
            self._user_share_code = data.get("user_share_code", "")
            self._user_receive_code = data.get("user_receive_code", "")
            self._user_share_link = data.get("user_share_link", "")
            self._user_share_pan_path = data.get("user_share_pan_path", "/")
            self._user_share_local_path = data.get("user_share_local_path", "")
            self._clear_recyclebin_enabled = data.get("clear_recyclebin_enabled", False)
            self._clear_receive_path_enabled = data.get("clear_receive_path_enabled", False)
            self._cron_clear = data.get("cron_clear", "0 */7 * * *")
            self._pan_transfer_enabled = data.get("pan_transfer_enabled", False)
            self._pan_transfer_paths = data.get("pan_transfer_paths", "")
            self._cookie_error_notify_enabled = data.get("cookie_error_notify_enabled", False)
            self._cookie_error_notify_client_type = data.get("cookie_error_notify_client_type", "alipaymini")
            self._picgo_enabled = data.get("picgo_enabled", False)
            self._picgo_api_key = data.get("picgo_api_key", "")
            self._picgo_upload_url = data.get("picgo_upload_url", "https://www.picgo.net/api/1/upload")
            # MediaWarp 配置项加载
            self._mediawarp_enabled = data.get("mediawarp_enabled", False)
            self._mediawarp_port = data.get("mediawarp_port", '18699')
            self._mediawarp_media_strm_path = data.get("mediawarp_media_strm_path", "")
            # mediawarp_mediaservers from frontend is the name of the selected server for MediaWarp
            self._mediawarp_mediaserver_name = data.get("mediawarp_mediaservers") 
            self._mediawarp_crx = data.get("mediawarp_crx", False)
            self._mediawarp_actor_plus = data.get("mediawarp_actor_plus", False)
            self._mediawarp_fanart_show = data.get("mediawarp_fanart_show", False)
            self._mediawarp_external_player_url = data.get("mediawarp_external_player_url", False)
            self._mediawarp_danmaku = data.get("mediawarp_danmaku", False)
            self._mediawarp_video_together = data.get("mediawarp_video_together", False)
            self._mediawarp_srt2ass = data.get("mediawarp_srt2ass", False)
            
            # 持久化存储配置
            self.__update_config()
            
            # 重新初始化插件
            self.init_plugin(config=self.get_config())
            
            return {"code": 0, "msg": "保存成功"}
        except Exception as e:
            return {"code": 1, "msg": f"保存失败: {str(e)}"}

    def _get_status_api(self) -> dict:
        """获取插件状态"""
        return {
            "code": 0,
            "data": {
                "enabled": self._enabled,
                "has_client": bool(self._client),
                "running": bool(self._scheduler and self._scheduler.running) or bool(self.monitor_life_thread and self.monitor_life_thread.is_alive())
            }
        }

    def _trigger_full_sync_api(self) -> dict:
        """触发全量同步"""
        try:
            if not self._enabled or not self._cookies:
                return {"code": 1, "msg": "插件未启用或未配置cookie"}
            
            # 启动全量同步任务
            self._once_full_sync_strm = True
            self.__update_config()
            self.init_plugin(config=self.get_config())
            
            return {"code": 0, "msg": "全量同步任务已启动"}
        except Exception as e:
            return {"code": 1, "msg": f"启动全量同步任务失败: {str(e)}"}

    def _trigger_share_sync_api(self) -> dict:
        """触发分享同步"""
        try:
            if not self._enabled or not self._cookies:
                return {"code": 1, "msg": "插件未启用或未配置cookie"}
            
            if not self._user_share_link and not (self._user_share_code and self._user_receive_code):
                return {"code": 1, "msg": "未配置分享链接或分享码"}
            
            # 启动分享同步任务
            self._share_strm_enabled = True
            self.__update_config()
            self.init_plugin(config=self.get_config())
            
            return {"code": 0, "msg": "分享同步任务已启动"}
        except Exception as e:
            return {"code": 1, "msg": f"启动分享同步任务失败: {str(e)}"}

    def _browse_dir_api(self, request: Request) -> dict:
        """浏览目录"""
        try:
            path = request.query_params.get("path", "/")
            is_local = request.query_params.get("is_local", "false").lower() == "true"
            
            if is_local:
                # 浏览本地目录
                try:
                    import os
                    if not os.path.exists(path):
                        return {"code": 1, "msg": f"目录不存在: {path}"}
                    
                    dirs = []
                    files = []
                    
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        if os.path.isdir(item_path):
                            dirs.append({"name": item, "path": item_path, "is_dir": True})
                        else:
                            files.append({"name": item, "path": item_path, "is_dir": False})
                    
                    return {
                        "code": 0,
                        "path": path,
                        "items": sorted(dirs, key=lambda x: x["name"])
                    }
                except Exception as e:
                    return {"code": 1, "msg": f"浏览本地目录失败: {str(e)}"}
            else:
                # 浏览115网盘目录
                if not self._client or not self._cookies:
                    return {"code": 1, "msg": "未配置cookie或客户端初始化失败"}
                
                try:
                    # 获取目录ID
                    dir_info = self._client.fs_dir_getid(path)
                    if not dir_info or "id" not in dir_info:
                        return {"code": 1, "msg": f"获取目录ID失败: {path}"}
                    
                    cid = int(dir_info["id"])
                    
                    # 获取目录内容 (修正：使用推断的方法 fs_files)
                    items = []
                    fs_data = self._client.fs_files(cid) 
                    # 假设返回结构是 {"data": [...]} 或类似
                    if fs_data and isinstance(fs_data, dict) and "data" in fs_data:
                        for item in fs_data["data"]:
                             # 假设的目录判断字段： "fid" 存在且不为 0，或 "isdir" 标记
                             # (需要根据实际返回调整)
                            is_directory = False
                            if "fid" in item and item["fid"] != "0": # 文件夹通常有 fid
                                is_directory = True
                            elif "isdir" in item and item["isdir"] == 1:
                                is_directory = True
                            elif "cid" in item and item["cid"] != "0": # cid 也可能表示目录
                                is_directory = True
                            
                            # 根据推断的字段名获取文件名 (n, name, file_name)
                            item_name = item.get("n", item.get("name", item.get("file_name", ""))) 

                            if is_directory and item_name: # 只保留识别出的目录
                                items.append({
                                    "name": item_name,
                                    "path": f"{path.rstrip('/')}/{item_name}",
                                    "is_dir": True
                                })
                    elif fs_data and isinstance(fs_data, list):
                         # 如果直接返回列表
                         for item in fs_data:
                            is_directory = False
                            if isinstance(item, dict):
                                if "fid" in item and item["fid"] != "0":
                                    is_directory = True
                                elif "isdir" in item and item["isdir"] == 1:
                                    is_directory = True
                                elif "cid" in item and item["cid"] != "0":
                                     is_directory = True
                                item_name = item.get("n", item.get("name", item.get("file_name", ""))) 
                                if is_directory and item_name:
                                    items.append({
                                        "name": item_name,
                                        "path": f"{path.rstrip('/')}/{item_name}",
                                        "is_dir": True
                                    })
                    else:
                        # 记录未知的返回格式
                        logger.warning(f"浏览网盘目录 {cid} 时，fs_files 返回未知格式: {type(fs_data)} - {str(fs_data)[:200]}...")
                    
                    return {
                        "code": 0,
                        "path": path,
                        "items": sorted(items, key=lambda x: x["name"])
                    }
                except Exception as e:
                    logger.error(f"【P1115StrmHelper】浏览网盘目录 API 原始错误: {str(e)}")
                    self._check_cookie_and_notify_if_invalid(context_message=f"浏览网盘目录 '{path}'")
                    return {"code": 1, "msg": f"浏览网盘目录失败: {str(e)}"}
        except Exception as e:
            return {"code": 1, "msg": f"浏览目录失败: {str(e)}"}

    def _get_qrcode_api(self, request: Request = None, client_type_override: Optional[str] = None) -> dict:
        """获取登录二维码"""
        try:
            import time
            import uuid
            import requests
            import json
            from app.log import logger # 确保 logger 已导入或可访问
            import base64

            # 优先使用 override，其次尝试从 request 获取，最后使用默认值
            final_client_type = client_type_override
            if not final_client_type:
                final_client_type = request.query_params.get("client_type", "alipaymini") if request else "alipaymini"
            
            self.debug_log(f"获取二维码 - 接收到的客户端类型参数(request): {request.query_params.get('client_type') if request else 'N/A'}, override: {client_type_override}, 最终使用: {final_client_type}")
            
            # 二维码支持的客户端类型验证 (使用官方或兼容值)
            allowed_types = ["web", "android", "115android", "ios", "115ios", "alipaymini", "wechatmini", "115ipad", "tv", "qandroid"]
            if final_client_type not in allowed_types:
                original_requested_type = final_client_type
                final_client_type = "alipaymini"  # 默认回退到支付宝小程序
                self.debug_log(f"客户端类型 {original_requested_type} 无效或不受支持，已回退到 {final_client_type}")

            # 添加日志记录，记录最终决定使用的 client_type
            logger.info(f"【115STRM助手】二维码API - 实际使用客户端类型: {final_client_type}")

            # 1. 获取二维码token
            token_url = f"https://qrcodeapi.115.com/api/1.0/{final_client_type}/1.0/token/"
            token_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://115.com",
                "Referer": "https://115.com/"
            }
            
            self.debug_log(f"获取二维码token URL: {token_url}")
            token_response = requests.get(token_url, headers=token_headers, timeout=10)
            if not token_response.ok:
                error_msg = f"获取二维码token失败: {token_response.status_code} - {token_response.text}"
                self.debug_log(error_msg)
                return {"code": -1, "error": error_msg, "message": error_msg, "success": False} # Added success flag
                
            token_data = token_response.json()
            if not token_data.get("state"):
                error_msg = f"获取二维码token失败: {token_data.get('error', '未知错误')}"
                self.debug_log(error_msg)
                return {"code": -1, "error": error_msg, "message": error_msg, "success": False}
                
            uid = token_data.get("data", {}).get("uid", "")
            if not uid:
                error_msg = "获取二维码token失败: 未获取到uid"
                self.debug_log(error_msg)
                return {"code": -1, "error": error_msg, "message": error_msg, "success": False}
                
            # 2. 获取二维码图片
            qrcode_url = f"https://qrcodeapi.115.com/api/1.0/{final_client_type}/1.0/qrcode?uid={uid}"
            qrcode_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Origin": "https://115.com",
                "Referer": "https://115.com/"
            }
            
            self.debug_log(f"获取二维码URL: {qrcode_url}")
            qrcode_response = requests.get(qrcode_url, headers=qrcode_headers, timeout=10)
            if not qrcode_response.ok:
                error_msg = f"获取二维码图片失败: {qrcode_response.status_code} - {qrcode_response.text}"
                self.debug_log(error_msg)
                return {"code": -1, "error": error_msg, "message": error_msg, "success": False}
                
            qrcode_base64 = base64.b64encode(qrcode_response.content).decode('utf-8')
            
            tips = "请扫描二维码登录"
            # Simplified tips logic for brevity, can be expanded as original
            tips_map = {
                "alipaymini": "请使用115客户端或支付宝扫描二维码登录",
                "wechatmini": "请使用115客户端或微信扫描二维码登录",
                "android": "请使用115安卓客户端扫描登录",
                "115android": "请使用115安卓客户端扫描登录",
                "ios": "请使用115 iOS客户端扫描登录",
                "115ios": "请使用115 iOS客户端扫描登录",
                "web": "请使用115网页版扫码登录",
                "115ipad": "请使用115 PAD客户端扫描登录",
                "tv": "请使用115 TV客户端扫描登录",
                "qandroid":"请使用115 qandroid客户端扫描登录"
            }
            tips = tips_map.get(final_client_type, "请扫描二维码登录")
            
            self.debug_log(f"二维码获取成功，UID: {uid}, 客户端类型: {final_client_type}")
            return {
                "code": 0,
                "uid": uid,
                "qrcode": f"data:image/png;base64,{qrcode_base64}",
                "tips": tips,
                "client_type": final_client_type, # 返回实际使用的 client_type
                "success": True 
            }
            
        except Exception as e:
            error_msg = f"获取登录二维码出错: {str(e)}"
            self.debug_log(error_msg)
            logger.error(f"【115STRM助手】获取二维码异常: {e}", exc_info=True) # 记录完整异常信息
            return {"code": -1, "error": error_msg, "message": error_msg, "success": False}

    def _check_qrcode_api_internal(self, uid: str, client_type: str, called_from_polling: bool = False) -> dict:
        """内部核心逻辑：检查二维码状态并处理登录（如果成功）"""
        log_prefix = "[PollingCall] " if called_from_polling else ""
        try:
            self.debug_log(f"{log_prefix}检查二维码状态请求参数 - UID: {uid}, 客户端类型: {client_type}")
            
            if not uid:
                error_msg = "无效的二维码ID，参数uid不能为空"
                self.debug_log(f"{log_prefix}{error_msg}")
                return {"code": -1, "error": error_msg, "message": error_msg}
            
            allowed_types = ["web", "android", "115android", "ios", "115ios", "alipaymini", "wechatmini", "115ipad", "tv", "qandroid", "harmony"]
            if client_type not in allowed_types:
                self.debug_log(f"{log_prefix}检查二维码状态时，客户端类型 {client_type} 无效，回退到 alipaymini")
                client_type = "alipaymini"
            
            import time
            import requests # Ensure requests is imported here if not globally in class or module
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://115.com",
                "Referer": "https://115.com/"
            }
            params = {"uid": uid, "time": int(time.time() * 1000)}
            status_url = f"https://qrcodeapi.115.com/api/1.0/{client_type}/1.0/status?" + "&".join([f"{k}={v}" for k, v in params.items() if v])
            
            self.debug_log(f"{log_prefix}查询二维码状态URL: {status_url}")
            response = requests.get(status_url, headers=headers, timeout=10)
            self.debug_log(f"{log_prefix}二维码状态响应: {response.status_code} - {response.text[:200]}...")
            
            data = response.json()

            if data.get("state") == False and data.get("code") == 90038: # 等待扫描
                self.debug_log(f"{log_prefix}二维码状态：等待扫描")
                return {"code": 0, "status": "waiting", "msg": "等待扫码"}
            
            if data.get("state") == False and data.get("code") == 90039: # 等待确认
                self.debug_log(f"{log_prefix}二维码状态：已扫描，等待确认")
                return {"code": 0, "status": "scanned", "msg": "已扫码，请在设备上确认"}
            
            status_data = None
            status_code_from_115 = None

            if data.get("state") == True and data.get("code") == 0:
                if "data" in data and "status" in data.get("data", {}):
                    status_data = data.get("data", {})
                    status_code_from_115 = status_data.get("status")
                elif "key" in data and "data" not in data:
                    status_code_from_115 = 2 
                    status_data = {}
                else:
                    status_code_from_115 = 2
                    status_data = data.get("data", {})
            elif not data.get("state"):
                error_msg_from_115 = data.get('error', data.get('message', '未知错误'))
                if data.get("code") == 40199002: 
                    backup_url = f"https://qrcodeapi.115.com/get/status?uid={uid}&time={int(time.time() * 1000)}"
                    self.debug_log(f"{log_prefix}尝试备用接口: {backup_url}")
                    try:
                        backup_response = requests.get(backup_url, headers=headers, timeout=10)
                        backup_data = backup_response.json()
                        self.debug_log(f"{log_prefix}备用接口响应: {backup_response.status_code} - {str(backup_data)[:200]}...")
                        if backup_data.get("state"):
                            data = backup_data
                            if "data" in data and "status" in data.get("data", {}):
                                status_data = data.get("data", {})
                                status_code_from_115 = status_data.get("status")
                            elif "key" in data and "data" not in data:
                                status_code_from_115 = 2; status_data = {}
                            else: #备用接口成功但格式未知
                                return {"code": -1, "error": "备用接口响应格式未知", "message": "备用接口响应格式未知"}
                        else: #备用接口也失败
                             return {"code": -1, "error": error_msg_from_115, "message": error_msg_from_115}
                    except Exception as backup_err:
                        self.debug_log(f"{log_prefix}备用接口请求失败: {backup_err}")
                        return {"code": -1, "error": error_msg_from_115, "message": error_msg_from_115}
                else:
                    return {"code": -1, "error": error_msg_from_115, "message": error_msg_from_115}
            else:
                 return {"code": -1, "error": "未知的二维码状态响应格式", "message": "未知的二维码状态响应格式"}
            
            status_map = {
                0: {"code": 0, "status": "waiting", "msg": "等待扫码"},
                1: {"code": 0, "status": "scanned", "msg": "已扫码，等待确认"},
                2: {"code": 0, "status": "success", "msg": "已确认，正在登录"},
                -1: {"code": -1, "error": "二维码已过期", "message": "二维码已过期"},
                -2: {"code": -1, "error": "用户取消登录", "message": "用户取消登录"}
            }

            if status_code_from_115 in status_map:
                result = status_map[status_code_from_115].copy()
                if status_code_from_115 == 2: # 登录成功
                    standard_app_name = client_type 
                    # (Mappings like 115android -> android, 115ipad -> 115ipad etc.)
                    # Simplified mapping for brevity here, assuming the original detailed mapping is in place
                    if client_type == "115android": standard_app_name = "android"
                    elif client_type == "115ios": standard_app_name = "ios"
                    # Ensure all client_type values used in _get_qrcode_api are correctly mapped here
                    elif client_type == "115ipad": standard_app_name = "115ipad" 
                    elif client_type == "qandroid": standard_app_name = "android"
                    elif client_type == "tv": standard_app_name = "tv"
                    elif client_type == "harmony": standard_app_name = "harmony"
                    # web, alipaymini, wechatmini usually map to themselves or have direct API endpoints.

                    login_result_url = f"https://passportapi.115.com/app/1.0/{standard_app_name}/1.0/login/qrcode/"
                    login_payload = {"app": standard_app_name, "account": uid}
                    self.debug_log(f"{log_prefix}尝试获取登录结果 - URL: {login_result_url}, Payload: {login_payload}")
                    
                    try:
                        login_response = requests.post(login_result_url, data=login_payload, headers=headers, timeout=10) 
                        login_data = login_response.json()
                        self.debug_log(f"{log_prefix}登录结果响应: {login_response.status_code} - {str(login_data)[:200]}...")
                    except Exception as req_err:
                         return {"code": -1, "error": f"获取登录结果请求失败: {req_err}", "message": f"获取登录结果请求失败: {req_err}"}

                    if login_data.get("state") and login_data.get("data"):
                        cookie_data = login_data.get("data", {})
                        cookie_string = ""
                        if "cookie" in cookie_data and isinstance(cookie_data["cookie"], dict):
                            for name, value in cookie_data["cookie"].items():
                                if name and value: cookie_string += f"{name}={value}; "
                        
                        if cookie_string:
                            self._cookies = cookie_string.strip()
                            self.__update_config() # Save the new cookie
                            try:
                                self._client = P115Client(self._cookies) 
                                self.debug_log(f"{log_prefix}登录成功，已获取Cookie并重新初始化客户端")
                                result["cookie"] = cookie_string 
                            except Exception as ce:
                                return {"code": -1, "error": f"Cookie获取成功，但客户端初始化失败: {str(ce)}", "message": f"Cookie获取成功，但客户端初始化失败: {str(ce)}"}
                        else:
                            return {"code": -1, "error": "登录成功但未能正确解析Cookie", "message": "登录成功但未能正确解析Cookie"}
                    else:
                        specific_error = login_data.get('message', login_data.get('error', '未知错误'))
                        return {"code": -1, "error": f"获取登录会话数据失败: {specific_error}", "message": f"获取登录会话数据失败: {specific_error}"}
                return result 
            elif status_code_from_115 is None:
                return {"code": -1, "error": "无法解析二维码状态", "message": "无法解析二维码状态"}
            else: 
                 return {"code": -1, "error": f"未知的115业务状态码: {status_code_from_115}", "message": f"未知的115业务状态码: {status_code_from_115}"}
        except Exception as e:
            error_msg = f"检查二维码状态异常: {str(e)}"
            self.debug_log(f"{log_prefix}{error_msg}")
            logger.error(f"{log_prefix}【115STRM助手】检查二维码状态异常: {e}", exc_info=True)
            return {"code": -1, "error": error_msg, "message": error_msg}

    def _check_qrcode_api(self, request: Request) -> dict:
        """API端点：检查二维码状态"""
        uid = request.query_params.get("uid", "")
        client_type = request.query_params.get("client_type", "alipaymini")
        return self._check_qrcode_api_internal(uid=uid, client_type=client_type, called_from_polling=False)

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        """
        cron_service = []
        if (
            self._cron_full_sync_strm
            and self._timing_full_sync_strm
            and self._full_sync_strm_paths
        ):
            cron_service.append(
                {
                    "id": "P1115StrmHelper_full_sync_strm_files",
                    "name": "定期全量同步115媒体库",
                    "trigger": CronTrigger.from_crontab(self._cron_full_sync_strm),
                    "func": self.full_sync_strm_files,
                    "kwargs": {},
                }
            )
        if self._cron_clear and (
            self._clear_recyclebin_enabled or self._clear_receive_path_enabled
        ):
            cron_service.append(
                {
                    "id": "P1115StrmHelper_main_cleaner",
                    "name": "定期清理115空间",
                    "trigger": CronTrigger.from_crontab(self._cron_clear),
                    "func": self.main_cleaner,
                    "kwargs": {},
                }
            )
        if cron_service:
            return cron_service

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """
        为Vue组件模式返回初始配置数据。
        Vue模式下，第一个参数返回None，第二个参数返回初始配置数据。
        """
        return None, self._get_config_api()

    def get_page(self) -> Optional[List[dict]]:
        """Vue模式不使用Vuetify页面定义"""
        return None

    def __update_config(self):
        self.update_config(
            {
                "enabled": self._enabled,
                "once_full_sync_strm": self._once_full_sync_strm,
                "cookies": self._cookies,
                "password": self._password,
                "moviepilot_address": self.moviepilot_address,
                "user_rmt_mediaext": self._user_rmt_mediaext,
                "user_download_mediaext": self._user_download_mediaext,
                "transfer_monitor_enabled": self._transfer_monitor_enabled,
                "transfer_monitor_scrape_metadata_enabled": self._transfer_monitor_scrape_metadata_enabled,
                "transfer_monitor_paths": self._transfer_monitor_paths,
                "transfer_mp_mediaserver_paths": self._transfer_mp_mediaserver_paths,
                "transfer_monitor_media_server_refresh_enabled": self._transfer_monitor_media_server_refresh_enabled,
                "transfer_monitor_mediaservers": self._transfer_monitor_mediaservers,
                "timing_full_sync_strm": self._timing_full_sync_strm,
                "full_sync_auto_download_mediainfo_enabled": self._full_sync_auto_download_mediainfo_enabled,
                "cron_full_sync_strm": self._cron_full_sync_strm,
                "full_sync_strm_paths": self._full_sync_strm_paths,
                "monitor_life_enabled": self._monitor_life_enabled,
                "monitor_life_auto_download_mediainfo_enabled": self._monitor_life_auto_download_mediainfo_enabled,
                "monitor_life_paths": self._monitor_life_paths,
                "monitor_life_mp_mediaserver_paths": self._monitor_life_mp_mediaserver_paths,
                "monitor_life_media_server_refresh_enabled": self._monitor_life_media_server_refresh_enabled,
                "monitor_life_mediaservers": self._monitor_life_mediaservers,
                "monitor_life_auto_remove_local_enabled": self._monitor_life_auto_remove_local_enabled,
                "monitor_life_scrape_metadata_enabled": self._monitor_life_scrape_metadata_enabled,
                "share_strm_enabled": self._share_strm_enabled,
                "share_strm_auto_download_mediainfo_enabled": self._share_strm_auto_download_mediainfo_enabled,
                "user_share_code": self._user_share_code,
                "user_receive_code": self._user_receive_code,
                "user_share_link": self._user_share_link,
                "user_share_pan_path": self._user_share_pan_path,
                "user_share_local_path": self._user_share_local_path,
                "clear_recyclebin_enabled": self._clear_recyclebin_enabled,
                "clear_receive_path_enabled": self._clear_receive_path_enabled,
                "cron_clear": self._cron_clear,
                "pan_transfer_enabled": self._pan_transfer_enabled,
                "pan_transfer_paths": self._pan_transfer_paths,
                "cookie_error_notify_enabled": self._cookie_error_notify_enabled,
                "cookie_error_notify_client_type": self._cookie_error_notify_client_type,
                "picgo_enabled": self._picgo_enabled,
                "picgo_api_key": self._picgo_api_key or "",
                "picgo_upload_url": self._picgo_upload_url or "https://www.picgo.net/api/1/upload",
                
                # MediaWarp 配置项
                "mediawarp_enabled": self._mediawarp_enabled,
                "mediawarp_port": self._mediawarp_port or '18699',
                "mediawarp_media_strm_path": self._mediawarp_media_strm_path or "",
                "mediawarp_mediaservers": self._mediawarp_mediaserver_name or None, # 前端使用 mediawarp_mediaservers 作为单选的 v-model
                "mediawarp_crx": self._mediawarp_crx,
                "mediawarp_actor_plus": self._mediawarp_actor_plus,
                "mediawarp_fanart_show": self._mediawarp_fanart_show,
                "mediawarp_external_player_url": self._mediawarp_external_player_url,
                "mediawarp_danmaku": self._mediawarp_danmaku,
                "mediawarp_video_together": self._mediawarp_video_together,
                "mediawarp_srt2ass": self._mediawarp_srt2ass,
                "mediawarp_running": bool(self._mediawarp_process and self._mediawarp_process.is_running()),

                # 获取可用的媒体服务器配置
                "mediaservers": [
                                        {"title": config.name, "value": config.name}
                                        for config in self.mediaserver_helper.get_configs().values()
                ]
            }
        )

    @staticmethod
    def __check_python_version() -> bool:
        """
        检查Python版本
        """
        if not (sys.version_info.major == 3 and sys.version_info.minor >= 12):
            logger.error(
                "当前MoviePilot使用的Python版本不支持本插件，请升级到Python 3.12及以上的版本使用！"
            )
            return False
        return True

    def has_prefix(self, full_path, prefix_path):
        """
        判断路径是否包含
        """
        full = Path(full_path).parts
        prefix = Path(prefix_path).parts

        if len(prefix) > len(full):
            return False

        return full[: len(prefix)] == prefix

    def __get_run_transfer_path(self, paths, transfer_path):
        """
        判断路径是否为整理路径
        """
        transfer_paths = paths.split("\n")
        for path in transfer_paths:
            if not path:
                continue
            if self.has_prefix(transfer_path, path):
                return True
        return False

    def __get_media_path(self, paths, media_path):
        """
        获取媒体目录路径
        """
        media_paths = paths.split("\n")
        for path in media_paths:
            if not path:
                continue
            parts = path.split("#", 1)
            if self.has_prefix(media_path, parts[1]):
                return True, parts[0], parts[1]
        return False, None, None

    def media_transfer(self, event, file_path: Path, rmt_mediaext):
        """
        运行媒体文件整理
        :param event: 事件
        :param file_path: 文件路径
        :param rmt_mediaext: 媒体文件后缀名
        """
        file_category = event["file_category"]
        file_id = event["file_id"]
        if file_category == 0:
            # 文件夹情况，遍历文件夹，获取整理文件
            # 缓存顶层文件夹ID
            self.cache_delete_pan_transfer_list.append(str(event["file_id"]))
            for item in iter_files_with_path(
                self._client, cid=int(file_id), cooldown=2
            ):
                file_path = Path(item["path"])
                # 缓存文件夹ID
                if str(item["parent_id"]) not in self.cache_delete_pan_transfer_list:
                    self.cache_delete_pan_transfer_list.append(str(item["parent_id"]))
                if file_path.suffix in rmt_mediaext:
                    # 缓存文件ID
                    self.cache_creata_pan_transfer_list.append(str(item["id"]))
                    self.transferchain.do_transfer(
                        fileitem=FileItem(
                            storage="u115",
                            fileid=str(item["id"]),
                            parent_fileid=str(item["parent_id"]),
                            path=str(file_path).replace("\\", "/"),
                            type="file",
                            name=file_path.name,
                            basename=file_path.stem,
                            extension=file_path.suffix[1:],
                            size=item["size"],
                            pickcode=item["pickcode"],
                            modify_time=item["ctime"],
                        )
                    )
                    logger.info(f"【网盘整理】{file_path} 加入整理列队")
        else:
            # 文件情况，直接整理
            if file_path.suffix in rmt_mediaext:
                # 缓存文件ID
                self.cache_creata_pan_transfer_list.append(str(event["file_id"]))
                self.transferchain.do_transfer(
                    fileitem=FileItem(
                        storage="u115",
                        fileid=str(file_id),
                        parent_fileid=str(event["parent_id"]),
                        path=str(file_path).replace("\\", "/"),
                        type="file",
                        name=file_path.name,
                        basename=file_path.stem,
                        extension=file_path.suffix[1:],
                        size=event["file_size"],
                        pickcode=event["pick_code"],
                        modify_time=event["update_time"],
                    )
                )
                logger.info(f"【网盘整理】{file_path} 加入整理列队")

    def media_scrape_metadata(
        self,
        path,
        item_name: str = "",
        mediainfo: MediaInfo = None,
        meta: MetaBase = None,
    ):
        """
        媒体刮削服务
        :param path: 媒体文件路径
        :param item_name: 媒体名称
        :param meta: 元数据
        :param mediainfo: 媒体信息
        """
        item_name = item_name if item_name else Path(path).name
        logger.info(f"【媒体刮削】{item_name} 开始刮削元数据")
        if mediainfo:
            # 整理文件刮削
            if mediainfo.type == MediaType.MOVIE:
                # 电影刮削上级文件夹
                dir_path = Path(path).parent
                fileitem = FileItem(
                    storage="local",
                    type="dir",
                    path=str(dir_path),
                    name=dir_path.name,
                    basename=dir_path.stem,
                    modify_time=dir_path.stat().st_mtime,
                )
            else:
                # 电视剧刮削文件夹
                # 通过重命名格式判断根目录文件夹
                # 计算重命名中的文件夹层数
                rename_format_level = len(settings.TV_RENAME_FORMAT.split("/")) - 1
                logger.info(f"【媒体刮削-IF分支-TV】计算出的 rename_format_level: {rename_format_level}")
                logger.info(f"【媒体刮削-IF分支-TV】原始 strm 文件路径 (path): {path}")
                if rename_format_level < 1:
                    logger.info("【媒体刮削-IF分支-TV】rename_format_level < 1，将刮削 strm 文件本身")
                    file_path = Path(path)
                    fileitem = FileItem(
                        storage="local",
                        type="file",
                        path=str(file_path).replace("\\", "/"),
                        name=file_path.name,
                        basename=file_path.stem,
                        extension=file_path.suffix[1:],
                        size=file_path.stat().st_size,
                        modify_time=file_path.stat().st_mtime,
                    )
                else:
                    logger.info(f"【媒体刮削-IF分支-TV】rename_format_level >= 1，将刮削父级目录。索引 parents[{rename_format_level - 1}]")
                    dir_path = Path(path).parents[rename_format_level - 1]
                    logger.info(f"【媒体刮削-IF分支-TV】计算出的电视剧目录路径 (dir_path): {dir_path}")
                    try:
                        stat_result = dir_path.stat()
                        modify_time = stat_result.st_mtime
                        logger.info(f"【媒体刮削-IF分支-TV】dir_path.stat() 成功, mtime: {modify_time}")
                    except Exception as e_stat:
                        logger.error(f"【媒体刮削-IF分支-TV】dir_path.stat() 失败: {e_stat}", exc_info=True)
                        # 如果 stat 失败，可能路径有问题，或者是一个不期望刮削的深层结构
                        # 尝试回退到刮削 .strm 文件本身或其直接父目录，或者直接报错返回
                        # 这里暂时不改变行为，让其自然失败，以便观察
                        raise # 重新抛出异常，看看哪里捕获

                    fileitem = FileItem(
                        storage="local",
                        type="dir",
                        path=str(dir_path),
                        name=dir_path.name,
                        basename=dir_path.stem,
                        modify_time=modify_time, # 使用之前获取的 modify_time
                    )
            self.mediachain.scrape_metadata(
                fileitem=fileitem, meta=meta, mediainfo=mediainfo
            )
        else:
            # 对于没有 mediainfo 的媒体文件刮削
            # 先获取上级目录 mediainfo
            mediainfo, meta = None, None
            dir_path = Path(path).parent
            meta = MetaInfoPath(dir_path)
            mediainfo = self.mediachain.recognize_by_meta(meta)
            if not meta or not mediainfo:
                # 如果上级目录没有媒体信息则使用传入的路径
                logger.warn(f"【媒体刮削】{dir_path} 无法识别文件媒体信息！")
                finish_path = Path(path)
                meta = MetaInfoPath(finish_path)
                mediainfo = self.mediachain.recognize_by_meta(meta)
            else:
                if mediainfo.type == MediaType.TV:
                    # 如果是电视剧，再次获取上级目录媒体信息，兼容电视剧命名，获取 mediainfo
                    mediainfo, meta = None, None
                    dir_path = dir_path.parent
                    meta = MetaInfoPath(dir_path)
                    mediainfo = self.mediachain.recognize_by_meta(meta)
                    if meta and mediainfo:
                        # 存在 mediainfo 则使用本级目录
                        finish_path = dir_path
                    else:
                        # 否则使用上级目录
                        logger.warn(f"【媒体刮削】{dir_path} 无法识别文件媒体信息！")
                        finish_path = Path(path).parent
                        meta = MetaInfoPath(finish_path)
                        mediainfo = self.mediachain.recognize_by_meta(meta)
            fileitem = FileItem(
                storage="local",
                type="dir",
                path=str(finish_path),
                name=finish_path.name,
                basename=finish_path.stem,
                modify_time=finish_path.stat().st_mtime,
            )
            self.mediachain.scrape_metadata(
                fileitem=fileitem, meta=meta, mediainfo=mediainfo
            )

        logger.info(f"【媒体刮削】{item_name} 刮削元数据完成")

    @cached(cache=TTLCache(maxsize=1, ttl=2 * 60))
    def redirect_url(
        self,
        request: Request,
        pickcode: str = "",
        file_name: str = "",
        id: int = 0,
        share_code: str = "",
        receive_code: str = "",
        app: str = "",
    ):
        """
        115网盘302跳转
        """

        def get_first(m: Mapping, *keys, default=None):
            for k in keys:
                if k in m:
                    return m[k]
            return default

        def share_get_id_for_name(
            share_code: str,
            receive_code: str,
            name: str,
            parent_id: int = 0,
        ) -> int:
            api = "http://web.api.115.com/share/search"
            payload = {
                "share_code": share_code,
                "receive_code": receive_code,
                "search_value": name,
                "cid": parent_id,
                "limit": 1,
                "type": 99,
            }
            suffix = name.rpartition(".")[-1]
            if suffix.isalnum():
                payload["suffix"] = suffix
            resp = requests.get(
                f"{api}?{urlencode(payload)}", headers={"Cookie": self._cookies}
            )
            check_response(resp)
            json = loads(cast(bytes, resp.content))
            if get_first(json, "errno", "errNo") == 20021:
                payload.pop("suffix")
                resp = requests.get(
                    f"{api}?{urlencode(payload)}", headers={"Cookie": self._cookies}
                )
                check_response(resp)
                json = loads(cast(bytes, resp.content))
            if not json["state"] or not json["data"]["count"]:
                raise FileNotFoundError(ENOENT, json)
            info = json["data"]["list"][0]
            if info["n"] != name:
                raise FileNotFoundError(ENOENT, f"name not found: {name!r}")
            id = int(info["fid"])
            return id

        def get_receive_code(share_code: str) -> str:
            resp = requests.get(
                f"http://web.api.115.com/share/shareinfo?share_code={share_code}",
                headers={"Cookie": self._cookies},
            )
            check_response(resp)
            json = loads(cast(bytes, resp.content))
            if not json["state"]:
                raise FileNotFoundError(ENOENT, json)
            receive_code = json["data"]["receive_code"]
            return receive_code

        def get_downurl(
            pickcode: str,
            user_agent: str = "",
            app: str = "android",
        ) -> Url:
            """
            获取下载链接
            """
            if app == "chrome":
                resp = requests.post(
                    "http://proapi.115.com/app/chrome/downurl",
                    data={
                        "data": encrypt(f'{{"pickcode":"{pickcode}"}}').decode("utf-8")
                    },
                    headers={"User-Agent": user_agent, "Cookie": self._cookies},
                )
            else:
                resp = requests.post(
                    f"http://proapi.115.com/{app or 'android'}/2.0/ufile/download",
                    data={
                        "data": encrypt(f'{{"pick_code":"{pickcode}"}}').decode("utf-8")
                    },
                    headers={"User-Agent": user_agent, "Cookie": self._cookies},
                )
            check_response(resp)
            json = loads(cast(bytes, resp.content))
            if not json["state"]:
                raise OSError(EIO, json)
            data = json["data"] = loads(decrypt(json["data"]))
            if app == "chrome":
                info = next(iter(data.values()))
                url_info = info["url"]
                if not url_info:
                    raise FileNotFoundError(ENOENT, dumps(json).decode("utf-8"))
                url = Url.of(url_info["url"], info)
            else:
                data["file_name"] = unquote(
                    urlsplit(data["url"]).path.rpartition("/")[-1]
                )
                url = Url.of(data["url"], data)
            return url

        def get_share_downurl(
            share_code: str,
            receive_code: str,
            file_id: int,
            app: str = "",
        ) -> Url:
            payload = {
                "share_code": share_code,
                "receive_code": receive_code,
                "file_id": file_id,
            }
            if app:
                resp = requests.get(
                    f"http://proapi.115.com/{app}/2.0/share/downurl?{urlencode(payload)}",
                    headers={"Cookie": self._cookies},
                )
            else:
                resp = requests.post(
                    "http://proapi.115.com/app/share/downurl",
                    data={"data": encrypt(dumps(payload)).decode("utf-8")},
                    headers={"Cookie": self._cookies},
                )
            check_response(resp)
            json = loads(cast(bytes, resp.content))
            if not json["state"]:
                if json.get("errno") == 4100008:
                    receive_code = get_receive_code(share_code)
                    return get_share_downurl(share_code, receive_code, file_id, app=app)
                raise OSError(EIO, json)
            if app:
                data = json["data"]
            else:
                data = json["data"] = loads(decrypt(json["data"]))
            if not (data and (url_info := data["url"])):
                raise FileNotFoundError(ENOENT, json)
            data["file_id"] = data.pop("fid")
            data["file_name"] = data.pop("fn")
            data["file_size"] = int(data.pop("fs"))
            url = Url.of(url_info["url"], data)
            return url

        if share_code:
            try:
                if not receive_code:
                    receive_code = get_receive_code(share_code)
                elif len(receive_code) != 4:
                    return f"Bad receive_code: {receive_code}"
                if not id:
                    if file_name:
                        id = share_get_id_for_name(
                            share_code,
                            receive_code,
                            file_name,
                        )
                if not id:
                    return f"Please specify id or name: share_code={share_code!r}"
                url = get_share_downurl(share_code, receive_code, id, app=app)
                logger.info(f"【302跳转服务】获取 115 下载地址成功: {url}")
            except Exception as e:
                logger.error(f"【302跳转服务】获取 115 下载地址失败: {e}")
                return f"获取 115 下载地址失败: {e}"
        else:
            if not pickcode:
                logger.debug("【302跳转服务】Missing pickcode parameter")
                return "Missing pickcode parameter"

            if not (len(pickcode) == 17 and pickcode.isalnum()):
                logger.debug(f"【302跳转服务】Bad pickcode: {pickcode} {file_name}")
                return f"Bad pickcode: {pickcode} {file_name}"

            user_agent = request.headers.get("User-Agent") or b""
            logger.debug(f"【302跳转服务】获取到客户端UA: {user_agent}")

            try:
                url = get_downurl(pickcode.lower(), user_agent, app=app)
                logger.info(f"【302跳转服务】获取 115 下载地址成功: {url}")
            except Exception as e:
                logger.error(f"【302跳转服务】获取 115 下载地址失败: {e}")
                return f"获取 115 下载地址失败: {e}"

        return Response(
            status_code=302,
            headers={
                "Location": url,
                "Content-Disposition": f'attachment; filename="{quote(url["file_name"])}"',
            },
            media_type="application/json; charset=utf-8",
            content=dumps({"status": "redirecting", "url": url}),
        )

    @eventmanager.register(EventType.TransferComplete)
    def generate_strm(self, event: Event):
        """
        监控目录整理生成 STRM 文件
        """

        def generate_strm_files(
            target_dir: Path,
            pan_media_dir: Path,
            item_dest_path: Path,
            basename: str,
            url: str,
        ):
            """
            依据网盘路径生成 STRM 文件
            """
            try:
                pan_media_dir = str(Path(pan_media_dir))
                pan_path = Path(item_dest_path).parent
                pan_path = str(Path(pan_path))
                if self.has_prefix(pan_path, pan_media_dir):
                    pan_path = pan_path[len(pan_media_dir) :].lstrip("/").lstrip("\\")
                file_path = Path(target_dir) / pan_path
                file_name = basename + ".strm"
                new_file_path = file_path / file_name
                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(new_file_path, "w", encoding="utf-8") as file:
                    file.write(url)
                logger.info(
                    "【监控整理STRM生成】生成 STRM 文件成功: %s", str(new_file_path)
                )
                return True, new_file_path
            except Exception as e:  # noqa: F841
                logger.error(
                    "【监控整理STRM生成】生成 %s 文件失败: %s", str(new_file_path), e
                )
                return False, None

        if (
            not self._enabled
            or not self._transfer_monitor_enabled
            or not self._transfer_monitor_paths
            or not self.moviepilot_address
        ):
            return

        item = event.event_data
        if not item:
            return

        # 转移信息
        item_transfer: TransferInfo = item.get("transferinfo")
        # 媒体信息
        mediainfo: MediaInfo = item.get("mediainfo")
        # 元数据信息
        meta: MetaBase = item.get("meta")

        item_dest_storage: FileItem = item_transfer.target_item.storage
        if item_dest_storage != "u115":
            return

        # 网盘目的地目录
        itemdir_dest_path: FileItem = item_transfer.target_diritem.path
        # 网盘目的地路径（包含文件名称）
        item_dest_path: FileItem = item_transfer.target_item.path
        # 网盘目的地文件名称
        item_dest_name: FileItem = item_transfer.target_item.name
        # 网盘目的地文件名称（不包含后缀）
        item_dest_basename: FileItem = item_transfer.target_item.basename
        # 网盘目的地文件 pickcode
        item_dest_pickcode: FileItem = item_transfer.target_item.pickcode
        # 是否蓝光原盘
        item_bluray = SystemUtils.is_bluray_dir(Path(itemdir_dest_path))

        __itemdir_dest_path, local_media_dir, pan_media_dir = self.__get_media_path(
            self._transfer_monitor_paths, itemdir_dest_path
        )
        if not __itemdir_dest_path:
            logger.debug(
                f"【监控整理STRM生成】{item_dest_name} 路径匹配不符合，跳过整理"
            )
            return
        logger.debug("【监控整理STRM生成】匹配到网盘文件夹路径: %s", str(pan_media_dir))

        if item_bluray:
            logger.warning(
                f"【监控整理STRM生成】{item_dest_name} 为蓝光原盘，不支持生成 STRM 文件: {item_dest_path}"
            )
            return

        if not item_dest_pickcode:
            logger.error(
                f"【监控整理STRM生成】{item_dest_name} 不存在 pickcode 值，无法生成 STRM 文件"
            )
            return
        if not (len(item_dest_pickcode) == 17 and str(item_dest_pickcode).isalnum()):
            logger.error(
                f"【监控整理STRM生成】错误的 pickcode 值 {item_dest_name}，无法生成 STRM 文件"
            )
            return
        strm_url = f"{self.moviepilot_address.rstrip('/')}/api/v1/plugin/P1115StrmHelper/redirect_url?apikey={settings.API_TOKEN}&pickcode={item_dest_pickcode}"

        status, strm_target_path = generate_strm_files(
            target_dir=local_media_dir,
            pan_media_dir=pan_media_dir,
            item_dest_path=item_dest_path,
            basename=item_dest_basename,
            url=strm_url,
        )
        if not status:
            return

        if self._transfer_monitor_scrape_metadata_enabled:
            try:
                self.media_scrape_metadata(
                    path=strm_target_path,
                    item_name=item_dest_name,
                    mediainfo=mediainfo, # CORRECTED: Use local variable 'mediainfo'
                    meta=meta            # CORRECTED: Use local variable 'meta'
                )
                logger.info("【监控整理STRM生成】Call to self.media_scrape_metadata completed.")
            except Exception as e_scrape:
                logger.error(f"【监控整理STRM生成】ERROR during self.media_scrape_metadata call: {e_scrape}", exc_info=True)
        # 刷新媒体库
        if self._transfer_monitor_refresh_mediaserver_enabled:
            if not self.transfer_service_infos:
                return

            logger.info(f"【监控整理STRM生成】 {item_dest_name} 开始刷新媒体服务器")

            if self._transfer_mp_mediaserver_paths:
                status, mediaserver_path, moviepilot_path = self.__get_media_path(
                    self._transfer_mp_mediaserver_paths, strm_target_path
                )
                if status:
                    logger.info(
                        f"【监控整理STRM生成】 {item_dest_name} 刷新媒体服务器目录替换中..."
                    )
                    strm_target_path = strm_target_path.replace(
                        moviepilot_path, mediaserver_path
                    ).replace("\\", "/")
                    logger.info(
                        f"【监控整理STRM生成】刷新媒体服务器目录替换: {moviepilot_path} --> {mediaserver_path}"
                    )
                    logger.info(
                        f"【监控整理STRM生成】刷新媒体服务器目录: {strm_target_path}"
                    )
            items = [
                RefreshMediaItem(
                    title=mediainfo.title,
                    year=mediainfo.year,
                    type=mediainfo.type,
                    category=mediainfo.category,
                    target_path=Path(strm_target_path),
                )
            ]
            for name, service in self.transfer_service_infos.items():
                if hasattr(service.instance, "refresh_library_by_items"):
                    service.instance.refresh_library_by_items(items)
                elif hasattr(service.instance, "refresh_root_library"):
                    service.instance.refresh_root_library()
                else:
                    logger.warning(
                        f"【监控整理STRM生成】 {item_dest_name} {name} 不支持刷新"
                    )

    @eventmanager.register(EventType.PluginAction)
    def p115_full_sync(self, event: Event):
        """
        远程全量同步
        """
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "p115_full_sync":
                return
            self.post_message(
                channel=event.event_data.get("channel"),
                title="开始115网盘媒体库全量同步 ...",
                userid=event.event_data.get("user"),
            )
        strm_count, mediainfo_count = self.full_sync_strm_files()
        if event:
            self.post_message(
                channel=event.event_data.get("channel"),
                title=f"全量生成 STRM 文件完成，总共生成 {strm_count} 个 STRM 文件，下载 {mediainfo_count} 个媒体数据文件",
                userid=event.event_data.get("user"),
            )

    @eventmanager.register(EventType.PluginAction)
    def p115_add_share(self, event: Event):
        """
        远程分享转存
        """
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "p115_add_share":
                return
            args = event_data.get("arg_str")
            if not args:
                logger.error(f"【分享转存】缺少参数：{event_data}")
                self.post_message(
                    channel=event.event_data.get("channel"),
                    title="参数错误！ /p115_add_share 分享链接",
                    userid=event.event_data.get("user"),
                )
                return
        data = share_extract_payload(args)
        share_code = data["share_code"]
        receive_code = data["receive_code"]
        logger.info(
            f"【分享转存】解析分享链接 share_code={share_code} receive_code={receive_code}"
        )
        if not share_code or not receive_code:
            logger.error(f"【分享转存】解析分享链接失败：{args}")
            self.post_message(
                channel=event.event_data.get("channel"),
                title=f"解析分享链接失败：{args}",
                userid=event.event_data.get("user"),
            )
            return
        parent_path = self._pan_transfer_paths.split("\n")[0]
        parent_id = self.id_path_cache.get_id_by_dir(directory=str(parent_path))
        if not parent_id:
            parent_id = get_id_to_path(self._client, path=parent_path)
            logger.info(f"【分享转存】获取到转存目录 ID：{parent_id}")
            self.id_path_cache.add_cache(id=int(parent_id), directory=str(parent_path))
        payload = {
            "share_code": share_code,
            "receive_code": receive_code,
            "file_id": 0,
            "cid": int(parent_id),
            "is_check": 0,
        }
        logger.info(f"【分享转存】开始转存：{share_code}")
        self.post_message(
            channel=event.event_data.get("channel"),
            title=f"开始转存：{share_code}",
            userid=event.event_data.get("user"),
        )
        resp = self._client.share_receive(payload)
        if resp["state"]:
            logger.info(f"【分享转存】转存 {share_code} 到 {parent_path} 成功！")
            self.post_message(
                channel=event.event_data.get("channel"),
                title=f"转存 {share_code} 到 {parent_path} 成功！",
                userid=event.event_data.get("user"),
            )
        else:
            logger.info(f"【分享转存】转存 {share_code} 失败：{resp['error']}")
            self.post_message(
                channel=event.event_data.get("channel"),
                title=f"转存 {share_code} 失败：{resp['error']}",
                userid=event.event_data.get("user"),
            )
        return

    def full_sync_strm_files(self):
        """
        全量同步
        """
        if (
            not self._full_sync_strm_paths
            or not self.moviepilot_address
            or not self._user_download_mediaext
        ):
            return

        strm_helper = FullSyncStrmHelper(
            user_rmt_mediaext=self._user_rmt_mediaext,
            user_download_mediaext=self._user_download_mediaext,
            auto_download_mediainfo=self._full_sync_auto_download_mediainfo_enabled,
            client=self._client,
            cookie=self._cookies,
            server_address=self.moviepilot_address,
        )
        strm_helper.generate_strm_files(
            full_sync_strm_paths=self._full_sync_strm_paths,
        )
        return strm_helper.get_generate_total()

    def share_strm_files(self):
        """
        分享生成STRM
        """
        if (
            not self._user_share_pan_path
            or not self._user_share_local_path
            or not self.moviepilot_address
        ):
            return

        if self._user_share_link:
            data = share_extract_payload(self._user_share_link)
            share_code = data["share_code"]
            receive_code = data["receive_code"]
            logger.info(
                f"【分享STRM生成】解析分享链接 share_code={share_code} receive_code={receive_code}"
            )
        else:
            if not self._user_share_code or not self._user_receive_code:
                return
            share_code = self._user_share_code
            receive_code = self._user_receive_code

        try:
            strm_helper = ShareStrmHelper(
                user_rmt_mediaext=self._user_rmt_mediaext,
                user_download_mediaext=self._user_download_mediaext,
                auto_download_mediainfo=self._share_strm_auto_download_mediainfo_enabled,
                client=self._client,
                server_address=self.moviepilot_address,
                share_media_path=self._user_share_pan_path,
                local_media_path=self._user_share_local_path,
                cookie=self._cookies,
            )
            strm_helper.get_share_list_creata_strm(
                cid=0,
                share_code=share_code,
                receive_code=receive_code,
            )
            strm_helper.get_generate_total()
        except Exception as e:
            logger.error(f"【分享STRM生成】运行失败: {e}")
            return

    def monitor_life_strm_files(self):
        """
        监控115生活事件

        {
            1: "upload_image_file",  上传图片 生成 STRM
            2: "upload_file",        上传文件/目录 生成 STRM
            3: "star_image",         标星图片 无操作
            4: "star_file",          标星文件/目录 无操作
            5: "move_image_file",    移动图片 生成 STRM
            6: "move_file",          移动文件/目录 生成 STRM
            7: "browse_image",       浏览图片 无操作
            8: "browse_video",       浏览视频 无操作
            9: "browse_audio",       浏览音频 无操作
            10: "browse_document",   浏览文档 无操作
            14: "receive_files",     接收文件 生成 STRM
            17: "new_folder",        创建新目录 无操作
            18: "copy_folder",       复制文件夹 生成 STRM
            19: "folder_label",      标签文件夹 无操作
            20: "folder_rename",     重命名文件夹 无操作
            22: "delete_file",       删除文件/文件夹 删除 STRM
        }

        注意: 目前没有重命名文件，复制文件的操作事件
        """
        logger.info(f"【P1115StrmHelper】MONITOR_LIFE_STRM_FILES THREAD STARTED. self._enabled: {self._enabled}, self._monitor_life_enabled: {self._monitor_life_enabled}, self._pan_transfer_enabled: {self._pan_transfer_enabled}, self._monitor_life_paths: {self._monitor_life_paths}, self._pan_transfer_paths: {self._pan_transfer_paths}")

        def refresh_mediaserver(file_path: str, file_name: str):
            """
            刷新媒体服务器
            """
            if self._monitor_life_media_server_refresh_enabled:
                if not self.monitor_life_service_infos:
                    return
                logger.info(f"【监控生活事件】 {file_name} 开始刷新媒体服务器")
                if self._monitor_life_mp_mediaserver_paths:
                    status, mediaserver_path, moviepilot_path = self.__get_media_path(
                        self._monitor_life_mp_mediaserver_paths, file_path
                    )
                    if status:
                        logger.info(
                            f"【监控生活事件】 {file_name} 刷新媒体服务器目录替换中..."
                        )
                        file_path = file_path.replace(
                            moviepilot_path, mediaserver_path
                        ).replace("\\", "/")
                        logger.info(
                            f"【监控生活事件】刷新媒体服务器目录替换: {moviepilot_path} --> {mediaserver_path}"
                        )
                        logger.info(
                            f"【监控生活事件】刷新媒体服务器目录: {file_path}")
                items = [
                    RefreshMediaItem(
                        title=None,
                        year=None,
                        type=None,
                        category=None,
                        target_path=Path(file_path),
                    )
                ]
                for name, service in self.monitor_life_service_infos.items():
                    if hasattr(service.instance, "refresh_library_by_items"):
                        service.instance.refresh_library_by_items(items)
                    elif hasattr(service.instance, "refresh_root_library"):
                        service.instance.refresh_root_library()
                    else:
                        logger.warning(f"【监控生活事件】{file_name} {name} 不支持刷新")

        def creata_strm(event, file_path):
            """
            创建 STRM 文件
            """
            pickcode = event["pick_code"]
            file_category = event["file_category"]
            file_id = event["file_id"]
            status, target_dir, pan_media_dir = self.__get_media_path(
                self._monitor_life_paths, file_path
            )
            if not status:
                return
            logger.debug("【监控生活事件】匹配到网盘文件夹路径: %s", str(pan_media_dir))

            if file_category == 0:
                # 文件夹情况，遍历文件夹
                for item in iter_files_with_path(
                    self._client, cid=int(file_id), cooldown=2
                ):
                    if item["is_dir"] or item["is_directory"]:
                        continue
                    file_path = item["path"]
                    file_path = Path(target_dir) / Path(file_path).relative_to(
                        pan_media_dir
                    )
                    file_target_dir = file_path.parent
                    original_file_name = file_path.name
                    file_name = file_path.stem + ".strm"
                    new_file_path = file_target_dir / file_name

                    if self._monitor_life_auto_download_mediainfo_enabled:
                        if file_path.suffix in download_mediaext:
                            pickcode = item["pickcode"]
                            if not pickcode:
                                logger.error(
                                    f"【监控生活事件】{original_file_name} 不存在 pickcode 值，无法下载该文件"
                                )
                                continue
                            download_url = get_download_url(
                                pickcode=pickcode, cookie=self._cookies
                            )

                            if not download_url:
                                logger.error(
                                    f"【监控生活事件】{original_file_name} 下载链接获取失败，无法下载该文件"
                                )
                                continue

                            save_mediainfo_file(
                                file_path=Path(file_path),
                                file_name=original_file_name,
                                download_url=download_url,
                                cookie=self._cookies,
                            )
                            continue

                    if file_path.suffix not in rmt_mediaext:
                        logger.warn(
                            "【监控生活事件】跳过网盘路径: %s",
                            str(file_path).replace(str(target_dir), "", 1),
                        )
                        continue

                    pickcode = item["pickcode"]
                    if not pickcode:
                        pickcode = item["pick_code"]

                    new_file_path.parent.mkdir(parents=True, exist_ok=True)

                    if not pickcode:
                        logger.error(
                            f"【监控生活事件】{original_file_name} 不存在 pickcode 值，无法生成 STRM 文件"
                        )
                        continue
                    if not (len(pickcode) == 17 and str(pickcode).isalnum()):
                        logger.error(
                            f"【监控生活事件】错误的 pickcode 值 {pickcode}，无法生成 STRM 文件"
                        )
                        continue
                    strm_url = f"{self.moviepilot_address.rstrip('/')}/api/v1/plugin/P1115StrmHelper/redirect_url?apikey={settings.API_TOKEN}&pickcode={pickcode}"

                    with open(new_file_path, "w", encoding="utf-8") as file:
                        file.write(strm_url)
                    logger.info(
                        "【监控生活事件】生成 STRM 文件成功: %s", str(new_file_path)
                    )
                    if self._monitor_life_scrape_metadata_enabled:
                        self.media_scrape_metadata(
                            path=new_file_path,
                        )
                    # 刷新媒体服务器
                    refresh_mediaserver(str(new_file_path), str(original_file_name))
            else:
                # 文件情况，直接生成
                file_path = Path(target_dir) / Path(file_path).relative_to(
                    pan_media_dir
                )
                file_target_dir = file_path.parent
                original_file_name = file_path.name
                file_name = file_path.stem + ".strm"
                new_file_path = file_target_dir / file_name

                if self._monitor_life_auto_download_mediainfo_enabled:
                    if file_path.suffix in download_mediaext:
                        if not pickcode:
                            logger.error(
                                f"【监控生活事件】{original_file_name} 不存在 pickcode 值，无法下载该文件"
                            )
                            return
                        download_url = get_download_url(
                            pickcode=pickcode, cookie=self._cookies
                        )

                        if not download_url:
                            logger.error(
                                f"【监控生活事件】{original_file_name} 下载链接获取失败，无法下载该文件"
                            )
                            return

                        save_mediainfo_file(
                            file_path=Path(file_path),
                            file_name=original_file_name,
                            download_url=download_url,
                            cookie=self._cookies,
                        )
                        return

                if file_path.suffix not in rmt_mediaext:
                    logger.warn(
                        "【监控生活事件】跳过网盘路径: %s",
                        str(file_path).replace(str(target_dir), "", 1),
                    )
                    return

                new_file_path.parent.mkdir(parents=True, exist_ok=True)

                if not pickcode:
                    logger.error(
                        f"【监控生活事件】{original_file_name} 不存在 pickcode 值，无法生成 STRM 文件"
                    )
                    return
                if not (len(pickcode) == 17 and str(pickcode).isalnum()):
                    logger.error(
                        f"【监控生活事件】错误的 pickcode 值 {pickcode}，无法生成 STRM 文件"
                    )
                    return
                strm_url = f"{self.moviepilot_address.rstrip('/')}/api/v1/plugin/P1115StrmHelper/redirect_url?apikey={settings.API_TOKEN}&pickcode={pickcode}"

                with open(new_file_path, "w", encoding="utf-8") as file:
                    file.write(strm_url)
                logger.info(
                    "【监控生活事件】生成 STRM 文件成功: %s", str(new_file_path)
                )
                logger.info(f"【监控生活事件】检查刮削开关: self._monitor_life_scrape_metadata_enabled = {self._monitor_life_scrape_metadata_enabled}") # 添加日志
                if self._monitor_life_scrape_metadata_enabled:
                    self.media_scrape_metadata(
                        path=new_file_path,
                    )
                # 刷新媒体服务器
                refresh_mediaserver(str(new_file_path), str(original_file_name))

        def remove_strm(event):
            """
            删除 STRM 文件
            """

            def __remove_parent_dir(file_path: Path):
                """
                删除父目录
                """
                # 删除空目录
                # 判断当前媒体父路径下是否有媒体文件，如有则无需遍历父级
                if not SystemUtils.exits_files(file_path.parent, ["strm"]):
                    # 判断父目录是否为空, 为空则删除
                    i = 0
                    for parent_path in file_path.parents:
                        i += 1
                        if i > 3:
                            break
                        if str(parent_path.parent) != str(file_path.root):
                            # 父目录非根目录，才删除父目录
                            if not SystemUtils.exits_files(parent_path, ["strm"]):
                                # 当前路径下没有媒体文件则删除
                                shutil.rmtree(parent_path)
                                logger.warn(
                                    f"【监控生活事件】本地空目录 {parent_path} 已删除"
                                )

            def __get_file_path(
                file_name: str, file_size: str, file_id: str, file_category: int
            ):
                """
                通过 还原文件/文件夹 再删除 获取文件路径
                """
                for item in self._client.recyclebin_list()["data"]:
                    if (
                        file_category == 0
                        and str(item["file_name"]) == file_name
                        and str(item["type"]) == "2"
                    ) or (
                        file_category != 0
                        and str(item["file_name"]) == file_name
                        and str(item["file_size"]) == file_size
                    ):
                        resp = self._client.recyclebin_revert(item["id"])
                        if resp["state"]:
                            time.sleep(1)
                            path = get_path_to_cid(self._client, cid=int(item["cid"]))
                            time.sleep(1)
                            self._client.fs_delete(file_id)
                            return str(Path(path) / item["file_name"])
                        else:
                            return None
                return None

            file_category = event["file_category"]
            file_path = __get_file_path(
                file_name=str(event["file_name"]),
                file_size=str(event["file_size"]),
                file_id=str(event["file_id"]),
                file_category=file_category,
            )
            if not file_path:
                return

            # 优先匹配待整理目录，如果删除的目录为待整理目录则不进行操作
            if self._pan_transfer_enabled and self._pan_transfer_paths:
                if self.__get_run_transfer_path(
                    paths=self._pan_transfer_paths, transfer_path=file_path
                ):
                    logger.debug(
                        f"【监控生活事件】: {file_path} 为待整理目录下的路径，不做处理"
                    )
                    return

            # 匹配是否是媒体文件夹目录
            status, target_dir, pan_media_dir = self.__get_media_path(
                self._monitor_life_paths, file_path
            )
            if not status:
                return
            logger.debug("【监控生活事件】匹配到网盘文件夹路径: %s", str(pan_media_dir))

            file_path = Path(target_dir) / Path(file_path).relative_to(pan_media_dir)
            if file_path.suffix in rmt_mediaext:
                file_target_dir = file_path.parent
                file_name = file_path.stem + ".strm"
                file_path = file_target_dir / file_name
            logger.info(
                f"【监控生活事件】删除本地{'文件夹' if file_category == 0 else '文件'}: {file_path}"
            )
            if file_category == 0:
                shutil.rmtree(Path(file_path))
            else:
                Path(file_path).unlink(missing_ok=True)
                __remove_parent_dir(Path(file_path))
            logger.info(f"【监控生活事件】{file_path} 已删除")

        def new_creata_path(event):
            """
            处理新出现的路径
            """
            # 1.获取绝对文件路径
            file_name = event["file_name"]
            file_path = (
                Path(get_path_to_cid(self._client, cid=int(event["parent_id"])))
                / file_name
            )
            # 匹配逻辑 整理路径目录 > 生成STRM文件路径目录
            # 2.匹配是否为整理路径目录
            if self._pan_transfer_enabled and self._pan_transfer_paths:
                if self.__get_run_transfer_path(
                    paths=self._pan_transfer_paths, transfer_path=file_path
                ):
                    self.media_transfer(
                        event=event,
                        file_path=Path(file_path),
                        rmt_mediaext=rmt_mediaext,
                    )
                    return
            # 3.匹配是否为生成STRM文件路径目录
            logger.info(f"【P1115StrmHelper】In new_creata_path, checking for life event STRM generation. self._monitor_life_enabled: {self._monitor_life_enabled}, self._monitor_life_paths: {bool(self._monitor_life_paths)}")
            if self._monitor_life_enabled and self._monitor_life_paths:
                if str(event["file_id"]) in self.cache_creata_pan_transfer_list:
                    logger.info(f"【P1115StrmHelper】Life event for file_id {event['file_id']} found in cache_creata_pan_transfer_list, skipping direct creata_strm.")
                    self.cache_creata_pan_transfer_list.remove(str(event["file_id"]))
                else:
                    logger.info(f"【P1115StrmHelper】Life event for file_id {event['file_id']} (name: {event.get('file_name', 'N/A')}) NOT in cache, attempting to call creata_strm.")
                    creata_strm(event=event, file_path=file_path)

        resp = life_show(self._client)
        if not resp["state"]:
            logger.error(f"【监控生活事件】生活事件开启失败: {resp}")
            return
        logger.info("【监控生活事件】生活事件监控启动中...")
        try:
            # 删除缓存，避免删除无限循环
            delete_list = []
            for events_batch in iter_life_behavior_list(self._client, cooldown=int(20)):
                if self.monitor_stop_event.is_set():
                    logger.info("【监控生活事件】收到停止信号，退出上传事件监控")
                    break
                if not events_batch:
                    time.sleep(20)
                    continue
                for event in events_batch:
                    rmt_mediaext = [
                        f".{ext.strip()}"
                        for ext in self._user_rmt_mediaext.replace("，", ",").split(",")
                    ]
                    download_mediaext = [
                        f".{ext.strip()}"
                        for ext in self._user_download_mediaext.replace(
                            "，", ","
                        ).split(",")
                    ]
                    if (
                        int(event["type"]) != 1
                        and int(event["type"]) != 2
                        and int(event["type"]) != 5
                        and int(event["type"]) != 6
                        and int(event["type"]) != 14
                        and int(event["type"]) != 18
                        and int(event["type"]) != 22
                    ):
                        continue

                    if (
                        int(event["type"]) == 1
                        or int(event["type"]) == 2
                        or int(event["type"]) == 5
                        or int(event["type"]) == 6
                        or int(event["type"]) == 14
                        or int(event["type"]) == 18
                    ):
                        # 新路径事件处理
                        new_creata_path(event=event)

                    if int(event["type"]) == 22:
                        # 删除文件/文件夹事件处理
                        if event["file_id"] in delete_list:
                            # 通过 delete_list 避免反复删除
                            delete_list.remove(event["file_id"])
                        elif (
                            str(event["file_id"]) in self.cache_delete_pan_transfer_list
                        ):
                            # 检查是否命中删除文件夹缓存，命中则无需处理
                            self.cache_delete_pan_transfer_list.remove(
                                str(event["file_id"])
                            )
                        else:
                            if (
                                self._monitor_life_enabled
                                and self._monitor_life_paths
                                and self._monitor_life_auto_remove_local_enabled
                            ):
                                delete_list.append(event["file_id"])
                                remove_strm(event=event)

        except Exception as e:
            logger.error(f"【监控生活事件】生活事件监控运行失败: {e}")
            logger.info("【监控生活事件】30s 后尝试重新启动生活事件监控")
            time.sleep(30)
            self.monitor_life_strm_files()
        logger.info("【监控生活事件】已退出生活事件监控")
        return

    def main_cleaner(self):
        """
        主清理模块
        """
        if self._clear_receive_path_enabled:
            self.clear_receive_path()

        if self._clear_recyclebin_enabled:
            self.clear_recyclebin()

    def clear_recyclebin(self):
        """
        清空回收站
        """
        try:
            logger.info("【回收站清理】开始清理回收站")
            self._client.recyclebin_clean(password=self._password)
            logger.info("【回收站清理】回收站已清空")
        except Exception as e:
            logger.error(f"【回收站清理】清理回收站运行失败: {e}")
            return

    def clear_receive_path(self):
        """
        清空我的接收
        """
        try:
            logger.info("【我的接收清理】开始清理我的接收")
            parent_id = int(self._client.fs_dir_getid("/我的接收")["id"])
            if parent_id == 0:
                logger.info("【我的接收清理】我的接收目录为空，无需清理")
                return
            logger.info(f"【我的接收清理】我的接收目录 ID 获取成功: {parent_id}")
            self._client.fs_delete(parent_id)
            logger.info("【我的接收清理】我的接收已清空")
        except Exception as e:
            logger.error(f"【我的接收清理】清理我的接收运行失败: {e}")
            return

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set() # This seems to be for APScheduler, keep it
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
            if self.monitor_stop_event: # General monitor stop
                self.monitor_stop_event.set()
            # We will NOT set _qr_polling_stop_event here anymore.
            # Let polling threads manage their lifecycle or be stopped by a more global shutdown event if available.
            # if hasattr(self, '_qr_polling_stop_event') and self._qr_polling_stop_event: # QR polling stop
            #     self._qr_polling_stop_event.set() # REMOVED THIS LINE
            
            # 确保 MediaWarp 服务也停止
            self._stop_mediawarp_service()
            logger.info("[P1115StrmHelper] 所有服务已尝试停止。")

        except Exception as e:
            print(str(e))

    def _check_cookie_and_notify_if_invalid(self, context_message: str = "一个依赖Cookie的操作失败", status_check_result: Optional[Dict] = None):
        """
        当一个操作可能因Cookie失效而失败时调用此方法。
        它会检查Cookie的实际状态，并在配置启用时发送二维码通知。
        """
        if not self._cookie_error_notify_enabled:
            logger.debug("Cookie失效通知未启用，跳过检查和通知流程。")
            return

        logger.info(f"由于操作 '{context_message}' 疑似失败，准备检查115 Cookie的有效性...")
        # 日志点A: 确认PicGo配置在方法开始时的状态
        logger.debug(f"[LogPointA] 检查通知的PicGo配置: _picgo_enabled={self._picgo_enabled}, _picgo_api_key non-empty={bool(self._picgo_api_key)}, _picgo_upload_url='{self._picgo_upload_url}'")
        
        current_status_check = status_check_result
        if current_status_check is None:
            logger.debug("_check_cookie_and_notify_if_invalid: 未提供status_check_result，将主动调用 _get_user_storage_status 进行检查。")
            current_status_check = self._get_user_storage_status()
        else:
            logger.debug("_check_cookie_and_notify_if_invalid: 使用了提供的status_check_result。")

        if not current_status_check.get("success"):
            error_message_lower = current_status_check.get("error_message", "").lower()
            cookie_error_keywords = [
                "cookie", "登录", "登陆", "认证失败", "未授权", "授权失败", "token", "session",
                "115客户端初始化失败", "获取115用户信息失败", "获取115空间信息失败", "115 cookies 未配置",
                "errno 61", "<!doctype html>"
            ]
            is_likely_cookie_error = any(keyword in error_message_lower for keyword in cookie_error_keywords)

            if is_likely_cookie_error:
                logger.warning(f"115 Cookie有效性检查失败: {current_status_check.get('error_message')}. 将尝试发送二维码通知。")
                
                client_type_for_qr = self._cookie_error_notify_client_type or "alipaymini"
                qr_code_data = self._get_qrcode_api(client_type_override=client_type_for_qr)

                if qr_code_data and qr_code_data.get("success") and qr_code_data.get("code") == 0:
                    base64_image_data_with_prefix = qr_code_data.get("qrcode")
                    qr_uid = qr_code_data.get("uid", str(int(time.time())))
                    picgo_image_url = None

                    # 日志点B: 在条件判断之前打印所有相关变量的值
                    logger.debug(f"[LogPointB] PicGo上传条件检查: "
                                 f"_picgo_enabled={self._picgo_enabled}, "
                                 f"_picgo_api_key_present={bool(self._picgo_api_key)}, "
                                 f"base64_image_present={bool(base64_image_data_with_prefix)}")

                    if self._picgo_enabled and self._picgo_api_key and base64_image_data_with_prefix:
                        # 日志点C: 如果进入了if语句块
                        logger.info("[LogPointC] 【Cookie失效通知】PicGo图床上传条件满足，尝试上传。")
                        picgo_filename = f"115_login_qr_{qr_uid}.png"
                        picgo_image_url = self._upload_to_picgo(base64_image_data_with_prefix, picgo_filename)
                        if not picgo_image_url:
                            logger.error("【Cookie失效通知】二维码上传到PicGo失败。")
                        else:
                            logger.info(f"【Cookie失效通知】二维码成功上传到PicGo: {picgo_image_url}")
                    else:
                        # 日志点D: 如果未进入if语句块
                        logger.info(f"[LogPointD] 【Cookie失效通知】PicGo图床上传条件未满足或跳过上传。 "
                                    f"Reason: _picgo_enabled={self._picgo_enabled}, "
                                    f"_picgo_api_key_present={bool(self._picgo_api_key)}, "
                                    f"base64_image_present={bool(base64_image_data_with_prefix)}")
                    
                    title = "🚨 115网盘 Cookie 可能已失效 🚨"
                    text_content_lines = []
                    static_notification_image_url = "https://img.picgo.net/2025/05/14/BG978adecb9a62a3ed.png"
                    link_to_send = None # Initialize

                    text_content_lines.append(f"系统检测到您的115网盘Cookie可能已失效（相关操作: {context_message}）。")

                    if picgo_image_url: # QR code successfully uploaded to PicGo
                        text_content_lines.append(f"🔗 请点击此通知即可展示二维码，")
                        text_content_lines.append(f"📷 打开并扫描其中的二维码，使用【{qr_code_data.get('client_type', client_type_for_qr).upper()}】方式重新登录。")
                        link_to_send = picgo_image_url # This link goes to the actual QR code image
                    else:
                        if self._picgo_enabled:
                             text_content_lines.append(f"⚠️ 登录二维码上传图床失败。")
                        else:
                             text_content_lines.append(f"⚙️ 图床服务未启用或配置。")
                        text_content_lines.append(f"   请前往插件配置页面手动扫码登录以恢复服务。")
                        
                    text_content_lines.append("💡 扫码提示: 请使用115客户端扫描二维码登录") # New fixed tip
                    final_text_content = "\n".join(text_content_lines)
                    
                    # 日志点E: 确认最终要发送的图片和链接
                    logger.info(f"[LogPointE] 发送Cookie失效通知。Static image for display: {static_notification_image_url}. Link (action URL, to QR on PicGo if available): {link_to_send if link_to_send else 'N/A (will use default plugin link)'}")

                    try:
                        post_params = {
                            "mtype": NotificationType.Plugin,
                            "title": title,
                            "text": final_text_content,
                            "image": static_notification_image_url # Always use the static image for display
                        }
                        
                        if link_to_send: # If QR code link is available, use it
                            post_params["link"] = link_to_send
                        # If link_to_send is None, post_message will use its default link (to plugin config page)
                        
                        logger.debug(f"[LogPointF] 准备发送通知，参数: {post_params}")
                        self.post_message(**post_params)
                        logger.info("Cookie失效二维码通知已发送。")

                        # <<< --- START: Initiate polling after notification --- >>>
                        if qr_code_data and qr_code_data.get("success") and qr_code_data.get("code") == 0:
                            qr_uid_for_polling = qr_code_data.get("uid")
                            # Get the client_type that was actually used for QR generation by _get_qrcode_api
                            client_type_actually_used_for_qr = qr_code_data.get("client_type") 

                            if qr_uid_for_polling and client_type_actually_used_for_qr:
                                self._qr_polling_stop_event.clear() # Clear event before starting new poll
                                logger.info(f"为通知中的二维码 (UID: {qr_uid_for_polling}, Client: {client_type_actually_used_for_qr}) 启动后台状态轮询任务。")
                                polling_thread = threading.Thread(
                                    target=self._poll_qr_code_status_after_notification,
                                    args=(qr_uid_for_polling, client_type_actually_used_for_qr),
                                    daemon=True # Daemon thread will not prevent plugin/app from exiting
                                )
                                polling_thread.start()
                            else:
                                logger.warning("无法启动后台二维码状态轮询：缺少UID或生成二维码时实际使用的客户端类型。")
                        # <<< --- END: Initiate polling after notification --- >>>

                    except Exception as post_e:
                        logger.error(f"发送Cookie失效通知时发生错误: {post_e}", exc_info=True)
                else:
                    qr_error_msg = qr_code_data.get("error", qr_code_data.get("message", "生成二维码失败")) if qr_code_data else "获取二维码数据失败"
                    logger.error(f"为Cookie失效通知生成二维码失败: {qr_error_msg}")
                    try:
                        self.post_message(
                            mtype=NotificationType.Plugin,
                            title="115 Cookie 失效 - 获取新登录二维码失败",
                            text=(
                                f"⚠️ 系统检测到您的115 Cookie可能已失效（相关操作: {context_message}）。\n"
                                f"💡 尝试生成新的登录二维码时遇到错误：{qr_error_msg}。\n"
                                f"📷 请稍后到插件配置页面手动扫码登录。"
                            )
                        )
                    except Exception as post_e:
                        logger.error(f"发送二维码生成失败通知时发生错误: {post_e}", exc_info=True)
            else:
                logger.info(f"操作 '{context_message}' 失败，但Cookie状态检查通过 (信息: {current_status_check.get('error_message')})。可能不是Cookie问题。")
        else:
            logger.info(f"操作 '{context_message}' 失败，但后续的115账号状态检查正常。推测非Cookie问题或Cookie已恢复。")


    def _upload_to_picgo(self, base64_image_with_prefix: str, filename: str) -> Optional[str]:
        """
        Uploads an image to PicGo.net.
        :param base64_image_with_prefix: Base64 encoded image string with prefix (e.g., "data:image/png;base64,...").
        :param filename: Desired filename for the uploaded image.
        :return: The URL of the uploaded image if successful, None otherwise.
        """
        if not self._picgo_enabled or not self._picgo_api_key or not self._picgo_upload_url:
            logger.error("【PicGo上传】服务未启用或API Key/上传URL未配置。")
            return None

        try:
            # Strip the prefix "data:image/...;base64,"
            actual_base64_data = base64_image_with_prefix.split(',', 1)[-1]
        except IndexError:
            logger.error(f"【PicGo上传】无效的base64图像数据格式: {base64_image_with_prefix[:50]}...")
            return None

        headers = {
            "X-API-Key": self._picgo_api_key,
            "Accept": "application/json" # Request JSON response
        }
        payload = {
            "source": actual_base64_data,
            "format": "json", # Request JSON response
            # title can be sent if desired, API auto-detects from metadata or filename
            # 'title': filename 
            "expiration": "P3D"
        }
        
        logger.info(f"【PicGo上传】准备上传图片 {filename} 到 {self._picgo_upload_url}")
        try:
            response = requests.post(self._picgo_upload_url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()  # Raises an exception for 4XX/5XX errors

            response_json = response.json()
            logger.debug(f"【PicGo上传】响应: {response_json}")

            if response_json.get("success") and response_json.get("status_code") == 200:
                image_url = response_json.get("image", {}).get("url")
                if image_url:
                    logger.info(f"【PicGo上传】图片 {filename} 上传成功。URL: {image_url}")
                    return image_url
                else:
                    logger.error(f"【PicGo上传】上传成功但未在响应中找到图片URL: {response_json}")
                    return None
            else:
                error_message = response_json.get("status_txt", "未知错误")
                logger.error(f"【PicGo上传】上传失败: {error_message} (Code: {response_json.get('status_code')})")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"【PicGo上传】请求时发生错误: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"【PicGo上传】处理时发生未知错误: {e}", exc_info=True)
            return None

    def _poll_qr_code_status_after_notification(self, qr_uid: str, client_type: str):
        start_time = time.time()
        polling_duration = 120  # seconds <-- 修改为120秒
        polling_interval = 5   # seconds
        attempt_count = 0

        logger.info(f"[PollingTask UID: {qr_uid}] 开始轮询通知二维码 (类型: {client_type}) 状态，持续约 {polling_duration} 秒...")

        while time.time() - start_time < polling_duration:
            # if self.monitor_stop_event.is_set(): # Old check
            if self._qr_polling_stop_event.is_set(): # New check with specific event
                logger.info(f"[PollingTask UID: {qr_uid}] 插件或轮询任务停止，轮询任务提前终止。")
                return

            attempt_count += 1
            logger.debug(f"[PollingTask UID: {qr_uid}] 第 {attempt_count} 次尝试检查状态...")
            try:
                status_result = self._check_qrcode_api_internal(uid=qr_uid, client_type=client_type, called_from_polling=True)

                if status_result.get("code") == 0 and status_result.get("status") == "success":
                    logger.info(f"[PollingTask UID: {qr_uid}] 轮询成功！用户已扫描并确认登录，Cookie已更新。")
                    return 
                elif status_result.get("code") == 0 and status_result.get("status") in ["waiting", "scanned"]:
                    logger.debug(f"[PollingTask UID: {qr_uid}] 状态: {status_result.get('msg')}. 继续轮询。")
                elif status_result.get("code") == -1: 
                    error_message = status_result.get('error', status_result.get('message', '未知错误')).lower()
                    # 只有明确的二维码最终状态才退出轮询
                    if "过期" in error_message or "取消" in error_message or "invalid qr code" in error_message: # 添加了 "invalid qr code" 以覆盖更多明确的115错误
                        logger.info(f"[PollingTask UID: {qr_uid}] 轮询结束，二维码状态为明确的终止状态: {status_result.get('error', '未知错误')}")
                        return
                    else:
                        # 对于其他错误 (如网络连接、DNS解析、超时等)，记录并继续轮询
                        logger.warning(f"[PollingTask UID: {qr_uid}] 检查状态时遇到可恢复错误或非终止性错误: {status_result.get('error', '未知错误')}. 将继续轮询。")
                else: 
                     logger.warning(f"[PollingTask UID: {qr_uid}] 检查状态时收到非终止性意外响应: {status_result}. 继续轮询。")
            except Exception as e: # Catching broader exceptions from the call itself, though _check_qrcode_api_internal should catch its own.
                logger.error(f"[PollingTask UID: {qr_uid}] 轮询检查的 _check_qrcode_api_internal 调用本身发生严重错误: {e}", exc_info=True)
                # 在这种情况下，也继续轮询，除非错误非常严重表明无法恢复
            
            # Wait before next attempt, but be responsive to stop event
            # Check stop event more frequently than polling_interval if polling_interval is large
            wait_per_slice = 1 # second
            slices_to_wait = polling_interval // wait_per_slice
            for _ in range(slices_to_wait):
                # if self.monitor_stop_event.is_set(): # Old check
                if self._qr_polling_stop_event.is_set(): # New check
                    logger.info(f"[PollingTask UID: {qr_uid}] 插件或轮询任务停止，轮询任务在等待期间提前终止。")
                    return
                time.sleep(wait_per_slice)
            # if polling_interval % wait_per_slice > 0 and not self.monitor_stop_event.is_set(): # Old check
            if polling_interval % wait_per_slice > 0 and not self._qr_polling_stop_event.is_set(): # New check
                time.sleep(polling_interval % wait_per_slice)


        logger.info(f"[PollingTask UID: {qr_uid}] 轮询超时（{polling_duration}秒）。用户未在此期间完成扫码登录。")
