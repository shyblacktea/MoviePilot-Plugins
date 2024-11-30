import datetime
import threading
from typing import List, Tuple, Dict, Any, Optional

import pytz
from app.helper.sites import SitesHelper
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.context import Context
from app.core.event import eventmanager, Event
from app.db.downloadhistory_oper import DownloadHistoryOper
from app.db.models.downloadhistory import DownloadHistory
from app.helper.downloader import DownloaderHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import ServiceInfo
from app.schemas.types import EventType, MediaType
from app.utils.string import StringUtils


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
    # 存储电影二级分类列表，初始化为包含默认分类
    _category_movie = None
    # 存储电视二级分类列表，初始化为包含默认分类
    _category_tv = None
    # 存储动漫二级分类列表，初始化为包含默认分类
    _category_anime = None
    _downloaders = None

    def init_plugin(self, config: dict = None):
        self.downloadhistory_oper = DownloadHistoryOper()
        self.downloader_helper = DownloaderHelper()
        self.sites_helper = SitesHelper()
        # 读取配置
        if config:
            self._enabled = config.get("enabled")
            self._onlyonce = config.get("onlyonce")
            self._interval = config.get("interval") or "计划任务"
            self._interval_cron = config.get("interval_cron") or "5 4 * * *"
            self._interval_time = self.str_to_number(config.get("interval_time"), 6)
            self._interval_unit = config.get("interval_unit") or "小时"
            self._enabled_media_tag = config.get("enabled_media_tag")
            self._enabled_tag = config.get("enabled_tag")
            self._enabled_category = config.get("enabled_category")
            # 获取电影二级分类配置，若为空则用默认分类
            self._category_movie = config.get("category_movie", ["电影/热门电影", "电影/经典电影"])
            # 获取电视二级分类配置，若为空则用默认分类
            self._category_tv = config.get("category_tv", ["电视/国产剧", "电视/美剧"])
            # 获取动漫二级分类配置，若为空则用默认分
            self._category_anime = config.get("category_anime", ["动漫/国漫", "动漫/日番"])
            self._downloaders = config.get("downloaders")

        # 停止现有任务
        self.stop_service()

        if self._onlyonce:
            # 创建定时任务控制器
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            # 执行一次, 关闭onlyonce
            self._onlyonce = False
            config.update({"onlyonce": self._onlyonce})
            self.update_config(config)
            # 添加 补全下载历史的标签与分类 任务
            self._scheduler.add_job(func=self._complemented_history, trigger='date',
                                    run_date=datetime.datetime.now(
                                        tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3)
                                    )

            if self._scheduler and self._scheduler.get_jobs():
                # 启动服务
                self._scheduler.print_jobs()
                self._scheduler.start()

    @property
    def service_infos(self) -> Optional[Dict[str, ServiceInfo]]:
        """
        服务信息
        """
        if not self._downloaders:
            logger.warning("尚未配置下载器，请检查配置")
            return None

        services = self.downloader_helper.get_services(name_filters=self._downloaders)
        if not services:
            logger.warning("获取下载器实例失败，请检查配置")
            return None

        active_services = {}
        for service_name, service_info in services.items():
            if service_info.instance.is_inactive():
                logger.warning(f"下载器 {service_name} 未连接，请检查配置")
            else:
                active_services[service_name] = service_info

        if not active_services:
            logger.warning("没有已连接的下载器，请检查配置")
            return None

        return active_services

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api() -> List[Dict[str, Any]]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        [{
            "id": "服务ID",
            "name": "服务ID",
            "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数
        }]
        """
        if self._enabled:
            if self._interval == "计划任务" or self._interval == "固定间隔":
                if self._interval == "固定间隔":
                    if self._interval_unit == "日前":
                        return [{
                            "id": "DownloadSiteTag1",
                            "name": "补全下载历史的标签与分类",
                            "trigger": "interval",
                            "func": self._complemented_history,
                            "kwargs": {
                                "hours": self._interval_time
                            }
                        }]
                    else:
                        if self._interval_time < 5:
                            self._interval_time = 5
                            logger.info(f"{self.LOG_TAG}启动定时服务: 最小不少于5分钟, 防止执行间隔太短任务冲突")
                        return [{
                            "id": "DownloadSiteTag1",
                            "name": "补全下载历史的标签与分类",
                            "trigger": "interval",
                            "func": self._complemented_history,
                            "kwargs": {
                                "minutes": self._interval_time
                            }
                        }]
                else:
                    return [{
                        "id": "DownloadSiteTag1",
                        "name": "补全下载历史的标签与分类",
                        "trigger": CronTrigger.from_crontab(self._interval_cron),
                        "func": self._complemented_history,
                        "kwargs": {}
                    }]
        return []

    @staticmethod
    def str_to_number(s: str, i: int) -> int:
        try:
            return int(s)
        except ValueError:
            return i

    def _complemented_history(self):
        """
        补全下载历史的标签与分类
        """
        if not self.service_infos:
            return
        logger.info(f"{self.LOG_TAG}开始执行...")
        # 记录处理的种子, 供辅种(无下载历史)使用
        dispose_history = {}
        # 所有站点索引
        indexers = [indexer.get("name") for indexer in self.sites_helper.get_indexers()]
        # JackettIndexers索引器支持多个站点, 如果不存在历史记录, 则通过tracker会再次附加其他站点名称
        indexers.append("JackettIndexers")
        indexers = set(indexers)
        tracker_mappings = {
            "chdbits.xyz": "ptchdbits.co",
            "agsvpt.trackers.work": "agsvpt.com",
            "tracker.cinefiles.info": "audiences.me",
        }
        for service in self.service_infos.values():
            downloader = service.name
            downloader_obj = service.instance
            logger.info(f"{self.LOG_TAG}开始扫描下载器 {downloader}...")
            if not downloader_obj:
                logger.error(f"{self.LOG_TAG} 获取下载器失败 {downloader}")
                continue
            # 获取下载器中的种子
            torrents, error = downloader_obj.get_torrents()
            # 如果下载器获取种子发生错误 或 没有种子 则跳过
            if error or not torrents:
                continue
            logger.info(f"{self.LOG_TAG}按时间重新排序 {downloader} 种子数：{len(torrents)}")
            # 按添加时间进行排序, 时间靠前的按大小和名称加入处理历史, 判定为原始种子, 其他为辅种
            torrents = self._torrents_sort(torrents=torrents, dl_type=service.type)
            logger.info(f"{self.LOG_TAG}下载器 {downloader} 分析种子信息中...")
            for torrent in torrents:
                try:
                    if self._event.is_set():
                        logger.info(
                            f"{self.LOG_TAG}停止服务")
                        return
                    # 获取已处理种子的key (size, name)
                    _key = self._torrent_key(torrent=torrent, dl_type=service.type)
                    # 获取种子hash
                    _hash = self._get_hash(torrent=torrent, dl_type=service.type)
                    if not _hash:
                        continue
                    # 获取种子当前标签
                    torrent_tags = self._get_label(torrent=torrent, dl_type=service.type)
                    torrent_cat = self._get_category(torrent=torrent, dl_type=service.type)
                    # 提取种子hash对应的下载历史
                    history: DownloadHistory = self.downloadhistory_oper.get_by_hash(_hash)
                    if not history:
                        # 如果找到已处理种子的历史, 表明当前种子是辅种, 否则创建一个空DownloadHistory
                        if _key and _key in dispose_history:
                            history = dispose_history[_key]
                            # 因为辅种站点必定不同, 所以需要软化站点名字 history.torrent_site
                            history.torrent_site = None
                        else:
                            history = DownloadHistory()
                    else:
                        # 加入历史记录
                        if _key:
                            dispose_history[_key] = history
                    # 如果标签已经存在任意站点, 则不再添加站点标签
                    if indexers.intersection(set(torrent_tags)):
                        history.torrent_site = None
                    # 如果站点名称为空, 尝试通过trackers识别
                    elif not history.torrent_site:
                        trackers = self._get_trackers(torrent=torrent, dl_type=service.type)
                        for tracker in trackers:
                            # 检查tracker是否包含特定的关键字，并进行相应的映射
                            for key, mapped_domain in tracker_mappings.items():
                                if key in tracker:
                                    domain = mapped_domain
                                    break
                            else:
                                domain = StringUtils.get_url_domain(tracker)
                            site_info = self.sites_helper.get_indexer(domain)
                            if site_info:
                                history.torrent_site = site_info.get("name")
                                break
                        # 如果通过tracker还是无法获取站点名称, 且tmdbid, type, title都是空的, 那么跳过当前种子
                        if not history.torrent_site and not history.tmdbid and not history.type and not history.title:
                            continue
                    # 按设置生成需要写入的标签与分类
                    _tags = []
                    _cat = None
                    # 站点标签, 如果勾选开关的话 因允许torrent_site为空时运行到此, 因此需要判断torrent_site不为空
                    if self._enabled_tag and history.torrent_site:
                        _tags.append(history.torrent_site)
                    # 媒体标题标签, 如果勾选开关的话 因允许title为空时运行到此, 因此需要判断title不为空
                    if self._enabled_media_tag and history.title:
                        _tags.append(history.title)
                    # 分类, 如果勾选开关的话 <tr暂不支持> 因允许mtype为空时运行到此, 因此需要判断mtype不为空。为防止不必要的识别, 种子已经存在分类torrent_cat时 也不执行
                    if service.type == "qbittorrent" and self._enabled_category and not torrent_cat and history.type:
                        # 如果是电视剧 需要区分是否动漫
                        genre_ids = None
                        origin_country = None
                        # 因允许tmdbid为空时运行到此, 因此需要判断tmdbid不为空
                        history_type = MediaType(history.type) if history.type else None
                        if history.tmdbid and history_type == MediaType.TV:
                            # tmdb_id获取tmdb信息
                            tmdb_info = self.chain.tmdb_info(mtype=history_type, tmdbid=history.tmdbid)
                            if tmdb_info:
                                genre_ids = tmdb_info.get("genre_ids")
                                origin_country = tmdb_info.get("origin_country")
                        elif history.tmdbid and history_type == MediaType.MOVIE:
                            tmdb_info = self.chain.tmdb_info(mtype=history_type, tmdbid=history.tmdbid)
                            if tmdb_info:
                                genre_ids = tmdb_info.get("genre_ids")
                                original_language = tmdb_info.get("original_language")
                        _cat = self._determine_category(history_type, genre_ids, origin_country, original_language)
                    # 去除种子已经存在的标签
                    if _tags and torrent_tags:
                        _tags = list(set(_tags) - set(torrent_tags))
                    # 如果分类一样, 那么不需要修改
                    if _cat == torrent_cat:
                        _cat = None
                    # 判断当前种子是否不需要修改
                    if not _cat and not _tags:
                        continue
                    # 执行通用方法, 设置种子标签与分类
                    self._set_torrent_info(service=service, _hash=_hash, _torrent=torrent, _tags=_tags, _cat=_cat,
                                           _original_tags=torrent_tags)
                except Exception as e:
                    logger.error(
                        f"{self.LOG_TAG}分析种子信息时发生了错误: {str(e)}")

        logger.info(f"{self.LOG_TAG}执行完成")

    def _determine_category(self, mtype, genre_ids, origin_country, original_language):
        """
        根据媒体类型及相关属性确定二级分类
        """
        if mtype == MediaType.MOVIE or mtype == MediaType.MOVIE.value:
            if genre_ids and '16' in genre_ids:
                return "电影/动画电影"
            elif original_language and any(lang in original_language for lang in ['zh', 'cn', 'bo', 'za']):
                return "电影/华语电影"
            else:
                return "电影/外语电影"
        elif mtype == MediaType.TV or mtype == MediaType.TV.value:
            if genre_ids and '16' in genre_ids:
                if origin_country and any(country in origin_country for country in ['CN', 'TW', 'HK']):
                    return "电视/国漫"
                elif origin_country and any(country in origin_country for country in ['JP', 'US']):
                    return "电视/日番"
            elif genre_ids and '99' in genre_ids:
                return "电视/纪录片"
            elif genre_ids and '10762' in genre_ids:
                return "电视/儿童"
            elif genre_ids and any(id in genre_ids for id in ['10764', '10767']):
                return "电视/综艺"
            elif origin_country and any(country in origin_country for country in ['CN', 'TW', 'HK']):
                return "电视/国产剧"
            elif origin_country and any(country in origin_country for country in ['US', 'FR', 'GB', 'DE', 'ES', 'IT', 'NL', 'PT', 'RU', 'UK']):
                return "电视/欧美剧"
            elif origin_country and any(country in origin_country for country in ['JP', 'KP', 'KR', 'TH', 'IN', 'SG']):
                return "电视/日韩剧"
            else:
                return "电视/未分类"
        elif mtype == MediaType.ANIME or mtype == MediaType.ANIME.value:
            if genre_ids and '16' in genre_ids:
                if origin_country and any(country in origin_country for country in ['CN', 'TW', 'HK']):
                    return "动漫/国漫"
                elif origin_country and any(country in origin_country for

def init_plugin(self, config: dict = None):
    self.downloadhistory_oper = DownloadHistoryOper()
    self.downloader_helper = DownloaderHelper()
    self.sites_helper = SitesHelper()
    # 读取配置
    if config:
        self._enabled = config.get("enabled")
        self._onlyonce = config.get("onlyonce")
        self._interval = config.get("interval") or "计划任务"
        self._interval_cron = config.get("interval_cron") or "5 4 * * *"
        self._interval_time = self.str_to_number(config.get("interval_time"), 6)
        self._interval_unit = config.get("interval_unit") or "小时"
        self._enabled_media_tag = config.get("enabled_media_tag")
        self._enabled_tag = config.get("enabled_tag")
        self._enabled_category = config.get("enabled_category")
        # 获取电影二级分类配置，若为空则用默认分类
        self._category_movie = config.get("category_movie", ["电影/热门电影", "电影/经典电影"])
        # 获取电视二级分类配置，若为空则用默认分类
        self._category_tv = config.get("category_tv", ["电视/国产剧", "电视/美剧"])
        # 获取动漫二级分类配置，若为空则用默认分类
        self._category_anime = config.get("category_anime", ["动漫/国漫", "动漫/日番"])
        self._downloaders = config.get("downloaders")

    # 停止现有任务
    self.stop_service()

    if self._onlyonce:
        # 创建定时任务控制器
        self._scheduler = BackgroundScheduler(timezone=settings.TZ)
        # 执行一次, 关闭onlyonce
        self._onlyonce = False
        config.update({"onlyonce": self._onlyonce})
        self.update_config(config)
        # 添加 补全下载历史的标签与分类 任务
        self._scheduler.add_job(func=self._complemented_history, trigger='date',
                                run_date=datetime.datetime.now(
                                    tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3)
                                )

        if self._scheduler and self._scheduler.get_jobs():
            # 启动服务
            self._scheduler.print_jobs()
            self._scheduler.start()

@property
def service_infos(self) -> Optional[Dict[str, ServiceInfo]]:
    """
    服务信息
    """
    if not self._downloaders:
        logger.warning("尚未配置下载器，请检查配置")
        return None

    services = self.downloader_helper.get_services(name_filters=self._downloaders)
    if not services:
        logger.warning("获取下载器实例失败，请检查配置")
        return None

    active_services = {}
    for service_name, service_info in services.items():
        if service_info.instance.is_inactive():
            logger.warning(f"下载器 {service_name} 未连接，请检查配置")
        else:
            active_services[service_name] = service_info

    if not active_services:
        logger.warning("没有已连接的下载器，请检查配置")
        return None

    return active_services

def get_state(self) -> bool:
    return self._enabled

@staticmethod
def get_command() -> List[Dict[str, Any]]:
    pass

def get_api(self) -> List[Dict[str, Any]]:
    pass

def get_service(self) -> List[Dict[str, Any]]:
    """
    注册插件公共服务
    [{
        "id": "服务ID",
        "name": "服务名称",
        "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
        "func": self.xxx,
        "kwargs": {} # 定时器参数
    }]
    """
    if self._enabled:
        if self._interval == "计划任务" or self._interval == "固定间隔":
            if self._interval == "固定间隔":
                if self._interval_unit == "小时":
                    return [{
                        "id": "DownloadSiteTag1",
                        "name": "补全下载历史的标签与分类",
                        "trigger": "interval",
                        "func": self._complemented_history,
                        "kwargs": {
                            "hours": self._interval_time
                        }
                    }]
                else:
                    if self._interval_time < 5:
                        self._interval_time = 5
                        logger.info(f"{self.LOG_TAG}启动定时服务: 最小不少于5分钟, 防止执行间隔太短任务冲突")
                    return [{
                        "id": "DownloadSiteTag1",
                        "name": "补全下载历史的标签与分类",
                        "trigger": "interval",
                        "func": self._complemented_history,
                        "kwargs": {
                            "minutes": self._interval_time
                        }
                    }]
            else:
                return [{
                    "id": "DownloadSiteTag1",
                    "name": "补全下载历史的标签与分类",
                    "trigger": CronTrigger.from_crontab(self._interval_cron),
                    "func": self._complemented_history,
                    "kwargs": {}
                }]
    return []

@staticmethod
def str_to_number(s: str, i: int) -> int:
    try:
        return int(s)
    except ValueError:
        return i

def _complemented_history(self):
    """
    补全下载历史的标签与分类
    """
    if not self.service_infos:
        return
    logger.info(f"{self.LOG_TAG}开始执行...")
    # 记录处理的种子, 供辅种(无下载历史)使用
    dispose_history = {}
    # 所有站点索引
    indexers = [indexer.get("name") for indexer in self.sites_helper.get_indexers()]
    # JackettIndexers索引器支持多个站点, 不存在历史记录, 则通过tracker会再次附加其他站点名称
    indexers.append("JackettIndexers")
    indexers = set(indexers)
    tracker_mappings = {
        "chdbits.xyz": "ptchdbits.co",
        "agsvpt.trackers.work": "agsvpt.com",
        "tracker.cinefiles.info": "audiences.me",
    }
    for service in self.service_infos.values():
        downloader = service.name
        downloader_obj = service.instance
        logger.info(f"{self.LOG_TAG}开始扫描下载器 {downloader}...")
        if not downloader_obj:
            logger.error(f"{self.LOG_TAG} 获取下载器失败 {downloader}")
            continue
        # 获取下载器中的种子
        torrents, error = downloader_obj.get_torrents()
        # 如果下载器获取种子发生错误 或 没有种子 则跳过
        if error or not torrents:
            continue
        logger.info(f"{self.LOG_TAG}按时间重新排序 {downloader} 种子数：{len(torrents)}")
        # 按添加时间进行排序, 时间靠前的按大小和名称加入处理历史, 判定为原始种子, 其他为辅种
        torrents = self._torrents_sort(torrents=torrents, dl_type=service.type)
        logger.info(f"{self.LOG_TAG}下载器 {downloader} 分析种子信息中...")
        for torrent in torrents:
            try:
                if self._event.is_set():
                    logger.info(
                        f"{self.LOG_TAG}停止服务")
                    return
                # 获取已处理种子的key (size, name)
                _key = self._torrent_key(torrent=torrent, dl_type=service.type)
                # 获取种子hash
                _hash = self._get_hash(torrent=torrent, dl_type=service.type)
                if not _hash:
                    continue
                # 获取种子当前标签
                torrent_tags = self._get_label(torrent=torrent, dl_type=service.type)
                torrent_cat = self._get_category(torrent=torrent, dl_type=service.type)
                # 提取种子hash对应的下载历史
                history: DownloadHistory = self.downloadhistory_oper.get_by_hash(_hash)
                if not history:
                    # 如果找到已处理种子的历史, 表明当前种子是辅种, 否则创建一个空DownloadHistory
                    if _key and _key in dispose_history:
                        history = dispose_history[_key]
                        # 因为辅种站点必定不同, 所以需要更新站点名字 history.torrent_site
                        history.torrent_site = None
                    else:
                        history = DownloadHistory()
                else:
                    # 加入历史记录
                    if _key:
                        dispose_history[_key] = history
                # 如果标签已经存在任意站点, 则不再添加站点标签
                if indexers.intersection(set(torrent_tags)):
                    history.torrent_site = None
                # 如果站点名称为空, 尝试通过trackers识别
                elif not history.torrent_site:
                    trackers = self._get_trackers(torrent=torrent, dl_type=service.type)
                    for tracker in trackers:
                        # 检查tracker是否包含特定的关键字，并进行相应的映射
                        for key, mapped_domain in tracker_mappings.items():
                            if key in tracker:
                                domain = mapped_domain
                                break
                        else:
                            domain = StringUtils.get_url_domain(tracker)
                        site_info = self.sites_helper.get_indexer(domain)
                        if site_info:
                            history.torrent_site = site_info.get("name")
                            break
                    # 如果通过tracker还是无法获取站点名称, 且tmdbid, type, title都是空的, 那么跳过当前种子
                    if not history.torrent_site and not history.tmdbid and not history.type and not history.title:
                        continue
                # 按设置生成需要写入的标签与分类
                _tags = []
                _cat = None
                # 站点标签, 如果勾选开关的话 因允许torrent_site为空时运行到此, 因此需要判断torrent_site不为空
                if self._enabled_tag and history.torrent_site:
                    _tags.append(history.torrent_site)
                # 媒体标题标签, 如果勾选开关的话 因允许title为空时运行到此, 因此需要判断title不为空
                if self._enabled_media_tag and history.title:
                    _tags.append(history.title)
                # 分类, 如果勾选开关的话 <tr暂不支持> 因允许mtype为空时运行到此, 因此需要判断mtype不为空。为防止不必要的识别, 种子已经存在分类torrent_cat时 也不执行
                if service.type == "qbittorrent" and self._enabled_category and not torrent_cat and history.type:
                    # 如果是电视剧 需要区分是否动漫
                    genre_ids = None
                    origin_country = None
                    # 因允许tmdbid为空时运行到此, 因此需要判断tmdbid不为空
                    history_type = MediaType(history.type) if history.type else None
                    if history.tmdbid and history_type == MediaType.TV:
                        # tmdb_id获取tmdb信息
                        tmdb_info = self.chain.tmdb_info(mtype=history_type, tmdbid=history.tmdbid)
                        if tmdb_info:
                            genre_ids = tmdb_info.get("genre_ids")
                            origin_country = tmdb_info.get("origin_country")
                    elif history.tmdbid and history_type == MediaType.MOVIE:
                        tmdb_info = self.chain.tmdb_info(mtype=history_type, tmdbid=history.tmdbid)
                        if tmdb_info:
                            genre_ids = tmdb_info.get("genre_ids")
                            original_language = tmdb_info.get("original_language")
                    _cat = self._determine_category(history_type, genre_ids, origin_country, original_language)
                # 去除种子已经存在的标签
                if _tags and torrent_tags:
                    _tags = list(set(_tags) - set(torrent_tags))
                # 如果分类一样, 那么不需要修改
                if _cat == torrent_cat:
                    _cat = None
                # 判断当前种子是否不需要修改
                if not _cat and not _tags:
                    continue
                # 执行通用方法, 设置种子标签与分类
                self._set_torrent_info(service=service, _hash=_hash, _torrent=torrent, _tags=_tags, _cat=_cat,
                                       _original_tags=torrent_tags)
            except Exception as e:
                logger.error(
                    f"{self.LOG_TAG}分析种子信息时发生了错误: {str(e)}")

    logger.info(f"{self.LOG_TAG}执行完成")

def _determine_category(self, mtype, genre_ids, origin_country, original_language):
    """
    根据媒体类型及相关属性确定二级分类
    """
    if mtype == MediaType.MOVIE or mtype == MediaType.MOVIE.value:
        if genre_ids and '16' in genre_ids:
            return "电影/动画电影"
        elif original_language and any(lang in original_language for lang in ['zh', 'cn', 'bo', 'za']):
            return "电影/华语电影"
        else:
            return "电影/外语电影"
    elif mtype == MediaType.TV or mtype == MediaType.TV.value:
        if genre_ids and '16' in genre_ids:
            if origin_country and any(country in origin_country for country in ['CN', 'TW', 'HK']):
                return "电视/国漫"
            elif origin_country and any(country in origin_country for country in ['JP', 'US']):
                return "电视/日番"
        elif genre_ids and '99' in genre_ids:
            return "电视/纪录片"
        elif genre_ids and '10762' in genre_ids:
            return "电视/儿童"
        elif genre_ids and any(id in genre_ids for id in ['10764', '10767']):
            return "电视/综艺"
        elif origin_country and any(country in origin_country for country in ['CN', 'TW', 'HK']):
            return "电视/国产剧"
        elif origin_country and any(country in origin_country for country in ['US', 'FR', 'GB', 'DE', 'ES', 'IT', 'NL', 'PT', 'RU', 'UK']):
            return "电视/欧美剧"
        elif origin_country and any(country in origin_country for country in ['JP', 'KP', 'KR', 'TH', 'IN', 'SG']):
            return "电视/日韩剧"
        else:
            return "电视/未分类"
    elif mtype == MediaType.ANIME or mtype == MediaType.ANIME.value:
        if genre_ids and '16' in genre_ids:
