import datetime
import threading
from typing import List, Tuple, Dict, Any, Optional

import pytz
from app.core.config import settings
from app.core.context import Context
from app.core.event import eventmanager, Event
from app.db.downloadhistory_oper import DownloadHistoryOper
from app.db.models.downloadhistory import DownloadHistory
from app.helper.downloader import DownloaderHelper
from app.helper.sites import SitesHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import ServiceInfo
from app.schemas.types import EventType, MediaType
from app.utils.string import StringUtils
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class DownloadSiteTag1(_PluginBase):
    # 插件名称
    plugin_name = "自用下载任务分类与标签"
    # 插件描述
    plugin_desc = "自动给下载任务分类与打站点标签、剧集名称标签"
    # 插件图标
    plugin_icon = "Youtube-dl_B.png"
    # 插件版本
    plugin_version = "0.0.1"
    # 插件作者
    plugin_author = "shy"
    # 作者主页
    author_url = "https://github.com/shyblacktea"
    # 插件配置项ID前缀
    plugin_config_prefix = "DownloadSiteTag1_"
    # 插件配置文件路径，需根据实际情况设置
    config_file_path = "your_config_file_path.yaml"
    # 加载顺序
    plugin_order = 2
    # 可使用的用户级别
    auth_level = 2
    # 日志前缀
    LOG_TAG = "[DownloadSiteTag1] "

    # 退出事件
    _event = threading.Event()
    # 私有属性
    downloadhistory_oper = None
    sites_helper = None
    downloader_helper = None
    _scheduler = None
    _enabled = False
    _onlyonce = False
    _interval = "计划任务"
    _interval_cron = "5 4 * * *"
    _interval_time = 6
    _interval_unit = "小时"
    _enabled_media_tag = False
    _enabled_tag = True
    _enabled_category = False
    _category_movie = []
    _category_tv = []
    _category_anime = []
    _downloaders = None

    def __init__(self):
        super().__init__()
        self.downloadhistory_oper = DownloadHistoryOper()
        self.downloader_helper = DownloaderHelper()
        self.sites_helper = SitesHelper()
        self.config_data = self.read_config_file(self.config_file_path)

    def read_config_file(self, config_file_path):
        with open(config_file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return config_data

    def _genre_ids_get_cat(self, mtype, media_info):
        if mtype == MediaType.MOVIE or mtype == MediaType.MOVIE.value:
            movie_config = self.config_data['movie']
            for category, conditions in movie_config.items():
                if all(media_info.get(key) in value.split(',') if key in media_info and value else True
                       for key, value in conditions.items()):
                    return category
            return '未分类'

        elif mtype == MediaType.TV or mtype == MediaType.TV.value:
            tv_config = self.config_data['tv']
            for category, conditions in tv_config.items():
                if all(media_info.get(key) in value.split(',') if key in media_info and value else True
                       for key, value in conditions.items():
                    return category
            return '未分类'

        return None

    def _set_torrent_info(self, service: ServiceInfo, _hash: str, _torrent: Any = None, _tags=None, _cat: str = None,
                          _original_tags: list = None):
        if not service or not service.instance:
            return
        if _tags is None:
            _tags = []
        downloader_obj = service.instance
        if not _torrent:
            _torrent, error = downloader_obj.get_torrents(ids=_hash)
            if not _torrent or error:
                logger.error(
                    f"{self.LOG_TAG}设置种子标签与分类时发生了错误: 通过 {hash} 查询不到任何种子!")
                return
            logger.info(
                f"{self.LOG_TAG}设置种子标签与分类: {_hash} 查询到 {len(_torrent)} 个种子")
            _torrent = _torrent[0]

        # 获取媒体信息，假设这里可以从_torrent对象中获取到相关信息，如media_type、genre_ids、original_language等
        media_info = {
           'media_type': _torrent.media_type if hasattr(_torrent, 'media_type') else None,
            'genre_ids': _torrent.genre_ids if hasattr(_torrent, 'genre_ids') else None,
            'original_language': _torrent.original_language if hasattr(_torrent, 'original_language') else None,
            'production_countries': _torrent.production_countries if hasattr(_torrent, 'production_countries') else None,
            'origin_country': _torrant, origin_country if hasattr(_torrent, 'origin_country') else None
        }

        secondary_category = self._genre_ids_get_cat(media_info['media_type'], media_info)

        if secondary_category:
            if secondary_category not in _tags:
                _tags.append(secondary_category)

        # 下载器api不通用, 所以需要分开处理
        if service.type == "qbittorrent":
            # 设置标签
            if _tags:
                downloader_obj.set_torrents_tag(ids=_hash, tags=_tags)
            # 设置分类 <tr暂不支持>
            if _cat:
                # 尝试设置种子分类, 如失败, 则创建再设置一遍
                try:
                    _torrent.setCategory(category=_cat)
                except Exception as e:
                    logger.warn(f"下载器 {service.name} 种子id: {_hash} 设置分类 {_cat} 失败：{str(e)}, "
                                f"尝试创建分类再设置...")
                    downloader_obj.qbc.torrents_createCategory(name=_cat)
                    _torrent.setCategory(category=_cat)
        else:
        # 设置标签
            if _tags:
                # _original_tags = None表示未指定, 所以需要获取原始标签
                if _original_tags is None:
                    _original_tags = self._get_label(torrent=_torrent, dl_type=service.type)
                # 如果原始标签不是空的, 那么合并原始标签
                if _original_tags:
                    _tags = list(set(_original_tags).union(set(_tags)))
                downloader_obj.set_torrent_tag(ids=_hash, tags=_tags)

        logger.warn(
            f"{self.LOG_TAG}下载器: {service.name} 种子id: {_hash} {('  标签: ' + ','.join(_tags)) if _tags else ''} {('  分类: ' + _cat) if _cat else ''}")

    @eventmanager.register(EventType.DownloadAdded)
    def download_added(self, event: Event):
        if not self.get_state():
            return

        if not event.event_data:
            return

        try:
            downloader = event.event_data.get("downloader")
            if not downloader:
                logger.info("触发添加下载事件，但没有获取到下载器信息，跳过后续处理")
                return

            service = self.service_infos.get(downloader)
            if not service:
                logger.info(f"触发添加下载事件，但没有监听下载器 {downloader}，跳过后续处理")
                return

            context: Context = event.event_data.get("context")
            _hash = event.event_data.get("hash")
            _torrent = context.torrent_info
            _media = context.media_info
            _tags = []
            _cat = None

            # 获取媒体信息，假设这里可以从上下文对象中获取到相关信息，如media_type、genre_ids、original_language等
            media_info = {
               'media_type': _media.type if hasattr(_media, 'type') else None,
                'genre_ids': _media.genre_ids if hasattr(_media, 'genre_ids') else None,
                'original_language': _media.original_language if hasattr(_media, 'original_language') else None,
                'production_countries': _media.production_countries if hasattr(_media, 'production_countries') else None,
                'origin_country = _media.origin_country if hasattr(_media, 'origin_country') else None
            }

            secondary_category = self._genre_ids_get_cat(media_info['media_type'], media_info)

            if secondary_category:
                if secondary_category not in _tags:
                _tags.append(secondary_category)

            if _hash and (_tags or _cat):
                self._set_torrent_info(service=service, _hash=_hash, _tags=_tags, _cat=_cat)
        except Exception as e:
        logger.error(
            f"{self.LOG_TAG}分析下载事件时发生了错误: {str(e)}")

    def get_state(self):
        # 这里假设你有相关逻辑来获取插件的启用状态，示例中暂未详细实现
        return self._enabled

    def get_command(self):
        # 这里假设你有相关逻辑来获取插件支持的命令，示例中暂未详细实现
        return []

    def get_api(self):
        # 这里假设你有相关逻辑来获取插件提供的API，示例中暂未详细实现
        return []

    def get_service(self):
        # 这里假设你有相关的逻辑来获取插件提供的公共服务，示例中暂未详细实现
        return []

def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
    """
    拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
    """
    return [
        {
            'component': 'VForm',
            'content': [
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                                'md': 3
                            },
                            'content': [
                                {
                                    'component': 'VSwitch',
                                    'props': {
                                        'model': 'enabled',
                                        'label': '启用插件',
                                    }
                                }
                            ]
                        },
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                                'md': 3
                            },
                            'content': [
                                {
                                    'component': 'VCheckboxBtn',
                                    'props': {
                                        'model': 'enabled_tag',
                                        'label': '自动站点标签',
                                    }
                                }
                            ]
                        },
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                                'md': 3
                            },
                            'content': [
                                {
                                    'component': 'VCheckboxBtn',
                                    'props': {
                                        'model': 'enabled_media_tag',
                                        'label': '自动剧名标签',
                                    }
                                }
                            ]
                        },
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                                'md': 3
                            },
                            'content': [
                                {
                                    'component': 'VCheckboxBtn',
                                    'props': {
                                        'model': 'enabled_category',
                                        'label': '自动设置分类',
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12
                            },
                            'content': [
                                {
                                    'component': 'VCheckboxBtn',
                                    'props': {
                                        'model': 'onlyonce',
                                        'label': '补全下载历史的标签与分类(一次性任务)'
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12
                            },
                            'content': [
                                {
                                    'component': 'VSelect',
                                    'props': {
                                        'multiple': True,
                                        'chips': True,
                                        'clearable': True,
                                        'model': 'downloaders',
                                        'label': '下载器',
                                        'items': [{"title": config.name, "value": config.name}
                                                  for config in self.downloader_helper.get_configs().values()]
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                                'md': 3
                            },
                            'content': [
                                {
                                    'component': 'VSelect',
                                    'props': {
                                        'model': 'interval',
                                        'label': '定时任务',
                                        'items': [
                                            {'title': '禁用', 'value': '禁用'},
                                            {'title': '计划任务', 'value': '计划任务'},
                                            {'title': '固定间隔', 'value': '固定间隔'}
                                        ]
                                    }
                                }
                            ]
                        },
                {
                    'component': 'VCol',
                    'props': {
                        'cols': 12,
                        'md': 3,
                    },
                    'content': [
                        {
                            'component': 'VTextField',
                            'props': {
                                'model': 'interval_cron',
                                'label': '计划任务设置',
                                'placeholder': '5 4 * * *'
                            }
                        }
                    ]
                },
                {
                    'component': 'VCol',
                    'props': {
                        'cols': 6,
                        'md': 3,
                    },
                    'content': [
                        {
                            'component': 'VTextField',
                            'props': {
                                'model': 'interval_time',
                                'label': '固定间隔设置, 间隔每',
                                'placeholder': '6'
                            }
                        }
                    ]
                },
                {
                    'component': 'VCol',
                    'props': {
                        'cols': 6,
                        'md': 3,
                    },
                    'content': [
                        {
                            'component': 'VSelect',
                            'props': {
                                'model': 'interval_unit',
                                'label': '单位',
                                'items': [
                                    {'title': '小时', 'value': '小时'},
                                    {'title': '分钟', 'value': '分钟'}
                                ]
                            }
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                            },
                            'content': [
                                {
                                    'component': 'VTextField',
                                    'props': {
                                        'model': 'category_movie',
                                        'label': '电影分类名称(默认: 电影)',
                                        'placeholder': '电影'
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                            },
                            'content': [
                                {
                                    'component': 'VTextField',
                                    'props': {
                                        'model': 'category_tv',
                                        'label': '电视分类名称(默认: 电视)',
                                        'placeholder': '电视'
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                            },
                            'content': [
                                {
                                    'component': 'VTextField',
                                    'props': {
                                        'model': 'category_anime',
                                        'label': '动漫分类名称(默认: 动漫)',
                                        'placeholder': '动漫'
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    'component': 'VRow',
                    'content': [
                        {
                            'component': 'VCol',
                            'props': {
                                'cols': 12,
                            },
                            'content': [
                                {
                                    'component': 'VAlert',
                                    'props': {
                                        'type': 'info',
                                        'variant': 'tonal',
                                        'text': '定时任务：支持两种定时方式，主要针对辅种刷流等种子补全站点信息。如没有对应的需求建议切换为禁用。'
                                    }
                                }
                            ]
                        }
