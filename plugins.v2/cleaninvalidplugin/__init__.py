import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.plugin import PluginManager
from app.db.systemconfig_oper import SystemConfigOper
from app.helper.plugin import PluginHelper
from app.log import logger
from app.plugins import _PluginBase
from app.scheduler import Scheduler
from app.schemas.types import SystemConfigKey


class CleanInvalidPlugin(_PluginBase):
    # 插件名称
    plugin_name = "清理无效插件"
    # 插件描述
    plugin_desc = "扫描、清理或重新安装数据库中无法加载的插件记录。"
    # 插件图标
    plugin_icon = "delete.jpg"
    # 插件版本
    plugin_version = "1.6"
    # 插件作者
    plugin_author = "cddjr,shyblacktea"
    # 作者主页
    author_url = "https://github.com/cddjr"
    # 插件配置项ID前缀
    plugin_config_prefix = "cleaninvalidplugin_"
    # 加载顺序
    plugin_order = 999
    # 可使用的用户级别
    auth_level = 1

    # 需要处理的插件
    _invalid_plugin_ids: List[str] = []
    # 操作模式：clean 清理 / reinstall 重新安装
    _action_mode = "clean"
    # 最近一次执行结果
    _last_result: Optional[Dict[str, Any]] = None
    # 后台重装任务
    _job_lock = threading.RLock()
    _job_thread: Optional[threading.Thread] = None
    _reinstall_job: Dict[str, Any] = {}

    def init_plugin(self, config: dict = None):
        """
        生效配置信息

        :param config: 配置信息字典
        """
        self.__ensure_static_asset_permissions()

        try:
            if not config:
                return

            self._invalid_plugin_ids = self.__normalize_plugin_ids(
                config.get("invalid_plugin_ids")
            )
            self._action_mode = config.get("action_mode") or "clean"

            if not self._invalid_plugin_ids:
                if not self.__is_reinstall_running():
                    self._last_result = None
                return

            if self._action_mode == "reinstall":
                self._start_reinstall_job(list(self._invalid_plugin_ids))
            else:
                self._last_result = self._clean_plugins()

        except Exception as e:
            logger.error(f"清理无效插件异常: {e}", exc_info=True)

    def _clean_plugins(self) -> Dict[str, Any]:
        """
        清理选中的无效插件
        """
        config_oper = SystemConfigOper()
        plugin_manager = PluginManager()

        valid_plugins = set(plugin_manager.get_plugin_ids() or [])
        all_plugins = self.__get_installed_plugins(config_oper)
        selected_plugins = set(self._invalid_plugin_ids)
        next_plugins = []
        cleaned_plugins = []
        skipped_plugins = []
        failed_plugins = []

        for plugin_id in all_plugins:
            if plugin_id not in selected_plugins:
                next_plugins.append(plugin_id)
                continue

            try:
                if plugin_id in valid_plugins:
                    next_plugins.append(plugin_id)
                    skipped_plugins.append(plugin_id)
                    logger.warning(f"{plugin_id} 是有效插件，跳过清理")
                    continue

                logger.info(f"正在清理无效插件 {plugin_id}")
                plugin_dir = self.__get_runtime_plugin_dir(plugin_id)
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir, ignore_errors=True)
                cleaned_plugins.append(plugin_id)
            except Exception as e:
                next_plugins.append(plugin_id)
                failed_plugins.append(plugin_id)
                logger.warning(f"清理无效插件 {plugin_id} 产生异常: {e}", exc_info=True)

        config_oper.set(SystemConfigKey.UserInstalledPlugins, self.__dedupe(next_plugins))
        self.__clear_pending_config()

        message = f"已清理 {len(cleaned_plugins)} 个无效插件"
        if failed_plugins:
            message += f"，{len(failed_plugins)} 个失败"
        self.post_message(title="无效插件清理完成", text=message)

        return {
            "action": "clean",
            "success": len(failed_plugins) == 0,
            "cleaned": cleaned_plugins,
            "skipped": skipped_plugins,
            "failed": failed_plugins,
            "message": message,
        }

    def _start_reinstall_job(self, plugin_ids: List[str]) -> bool:
        """启动单个后台重装任务，已有任务运行时复用当前任务。"""
        with self._job_lock:
            if self.__is_reinstall_running():
                self._last_result = dict(self._reinstall_job)
                logger.info("已有无效插件重装任务运行中，忽略重复提交")
                return False

            total = len(plugin_ids)
            self._reinstall_job = {
                "action": "reinstall",
                "status": "queued",
                "success": None,
                "progress": 0,
                "completed": 0,
                "total": total,
                "current": "",
                "reinstalled_count": 0,
                "skipped_count": 0,
                "failed_count": 0,
                "message": f"已提交 {total} 个插件到后台重装",
                "started_at": self.__now_text(),
                "finished_at": "",
            }
            self._last_result = dict(self._reinstall_job)
            self._job_thread = threading.Thread(
                target=self._run_reinstall_job,
                args=(list(plugin_ids),),
                name="CleanInvalidPlugin-Reinstall",
                daemon=True,
            )
            self._job_thread.start()
            return True

    def _run_reinstall_job(self, plugin_ids: List[str]):
        """执行后台重装并持续发布可轮询的进度状态。"""
        self.__update_job(
            status="running",
            message=f"正在后台重装 0/{len(plugin_ids)}",
        )
        try:
            result = self._reinstall_plugins(
                plugin_ids=plugin_ids,
                progress_callback=self._update_reinstall_progress,
            )
            final_status = "completed"
            self.__update_job(
                **result,
                status=final_status,
                progress=100,
                completed=len(plugin_ids),
                total=len(plugin_ids),
                current="",
                reinstalled_count=len(result.get("reinstalled") or []),
                skipped_count=len(result.get("skipped") or []),
                failed_count=len(result.get("failed") or []),
                finished_at=self.__now_text(),
            )
        except Exception as e:
            logger.error(f"后台重装无效插件异常: {e}", exc_info=True)
            self.__update_job(
                status="failed",
                success=False,
                current="",
                message=f"后台重装失败：{e}",
                finished_at=self.__now_text(),
            )

    def _update_reinstall_progress(
        self,
        current: str,
        completed: int,
        total: int,
        reinstalled_count: int = 0,
        skipped_count: int = 0,
        failed_count: int = 0,
    ):
        """接收逐插件进度，供前端轮询展示。"""
        progress = int(completed * 100 / total) if total else 100
        message = f"正在后台重装 {completed}/{total}"
        if current and completed < total:
            message += f"：{current}"
        self.__update_job(
            status="running",
            progress=progress,
            completed=completed,
            total=total,
            current=current if completed < total else "",
            reinstalled_count=reinstalled_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            message=message,
        )

    def _reinstall_plugins(
        self,
        plugin_ids: Optional[List[str]] = None,
        progress_callback: Optional[Callable[..., None]] = None,
    ) -> Dict[str, Any]:
        """
        重新安装选中的无效插件
        """
        target_plugin_ids = list(plugin_ids or self._invalid_plugin_ids)
        config_oper = SystemConfigOper()
        plugin_manager = PluginManager()
        plugin_helper = PluginHelper()

        valid_plugins = set(plugin_manager.get_plugin_ids() or [])
        all_plugins = self.__get_installed_plugins(config_oper)
        selected_plugins = set(target_plugin_ids)
        next_plugins = [p for p in all_plugins if p not in selected_plugins]

        # 构建 plugin_id -> repo_url 映射（用于市场重装）
        repo_url_map = self.__build_repo_url_map(plugin_manager)

        reinstalled_plugins = []
        skipped_plugins = []
        failed_plugins = []

        total = len(target_plugin_ids)
        for index, plugin_id in enumerate(target_plugin_ids):
            if progress_callback:
                progress_callback(
                    plugin_id,
                    index,
                    total,
                    len(reinstalled_plugins),
                    len(skipped_plugins),
                    len(failed_plugins),
                )
            try:
                if plugin_id in valid_plugins:
                    next_plugins.append(plugin_id)
                    skipped_plugins.append(plugin_id)
                    logger.warning(f"{plugin_id} 已是有效插件，跳过重装")
                    continue

                logger.info(f"正在重装插件 {plugin_id}")
                plugin_dir = self.__get_runtime_plugin_dir(plugin_id)
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir, ignore_errors=True)

                local_source_dir = self.__find_local_source_dir(plugin_id)
                if local_source_dir:
                    shutil.copytree(
                        local_source_dir,
                        plugin_dir,
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
                    )
                    next_plugins.append(plugin_id)
                    if self.__reload_reinstalled_plugin(plugin_manager, plugin_id):
                        reinstalled_plugins.append(plugin_id)
                        logger.info(f"已从本地插件源重装并热重载 {plugin_id}: {local_source_dir}")
                    else:
                        failed_plugins.append(plugin_id)
                    continue

                repo_url = repo_url_map.get(plugin_id)
                if repo_url:
                    state, msg = plugin_helper.install(
                        pid=plugin_id,
                        repo_url=repo_url,
                        force_install=True,
                    )
                    if state:
                        next_plugins.append(plugin_id)
                        if self.__reload_reinstalled_plugin(plugin_manager, plugin_id):
                            reinstalled_plugins.append(plugin_id)
                            logger.info(f"插件 {plugin_id} 已从插件市场重装并热重载：{repo_url}")
                        else:
                            failed_plugins.append(plugin_id)
                    else:
                        next_plugins.append(plugin_id)
                        failed_plugins.append(plugin_id)
                        logger.warning(f"插件 {plugin_id} 从插件市场重装失败：{msg}")
                else:
                    next_plugins.append(plugin_id)
                    failed_plugins.append(plugin_id)
                    logger.warning(f"插件 {plugin_id} 在本地源和插件市场中均未找到，保留原记录")

            except Exception as e:
                next_plugins.append(plugin_id)
                failed_plugins.append(plugin_id)
                logger.warning(f"重装插件 {plugin_id} 产生异常: {e}", exc_info=True)
            finally:
                if progress_callback:
                    progress_callback(
                        plugin_id,
                        index + 1,
                        total,
                        len(reinstalled_plugins),
                        len(skipped_plugins),
                        len(failed_plugins),
                    )

        config_oper.set(SystemConfigKey.UserInstalledPlugins, self.__dedupe(next_plugins))
        self.__clear_pending_config()

        message = f"已重装 {len(reinstalled_plugins)} 个插件"
        if failed_plugins:
            message += f"，{len(failed_plugins)} 个失败并已保留记录"
        self.post_message(title="无效插件重装完成", text=message)

        return {
            "action": "reinstall",
            "success": len(failed_plugins) == 0,
            "reinstalled": reinstalled_plugins,
            "skipped": skipped_plugins,
            "failed": failed_plugins,
            "message": message,
        }

    def get_state(self) -> bool:
        """
        获取插件运行状态
        """
        return False

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """
        获取插件渲染模式。
        """
        return "vue", "dist/assets"

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        注册插件远程命令
        """
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """
        注册插件API
        """
        return [
            {
                "path": "/invalid_plugins",
                "endpoint": self.get_invalid_plugins_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取无效插件列表",
                "description": "获取已安装记录中无法被当前 MoviePilot 加载的插件。",
            },
            {
                "path": "/last_result",
                "endpoint": self.get_last_result_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取最近执行结果",
                "description": "获取清理或重装操作的最近一次执行结果。",
            },
        ]

    def get_invalid_plugins_api(self) -> Dict[str, Any]:
        """
        获取无效插件列表API
        """
        return {
            "success": True,
            "data": {
                "items": self.get_invalid_plugin_details(),
                "last_result": self.__get_last_result(),
            },
        }

    def get_last_result_api(self) -> Dict[str, Any]:
        """
        获取最近执行结果API
        """
        return {"success": True, "data": self.__get_last_result()}

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """
        拼装插件配置页面

        :return: 1、页面配置（vue模式返回None）；2、默认数据结构
        """
        invalid_items = self.get_invalid_plugins()
        current_selection = [
            item["value"] for item in invalid_items if item["value"] in self._invalid_plugin_ids
        ]

        return None, {
            "invalid_plugin_ids": current_selection,
            "action_mode": self._action_mode or "clean",
        }

    def get_page(self) -> Optional[List[dict]]:
        """
        拼装插件详情页面
        """
        return None

    def stop_service(self):
        """
        停止插件
        """
        pass

    @staticmethod
    def get_invalid_plugins() -> List[Dict[str, Any]]:
        """
        获取本地无效插件列表

        :return: VSelect 数据格式的无效插件列表
        """
        return [
            {
                "title": item["title"],
                "value": item["id"],
            }
            for item in CleanInvalidPlugin.get_invalid_plugin_details()
        ]

    @staticmethod
    def get_invalid_plugin_details() -> List[Dict[str, Any]]:
        """
        获取本地无效插件明细
        """
        try:
            config_oper = SystemConfigOper()
            plugin_manager = PluginManager()

            all_plugins = set(CleanInvalidPlugin.__get_installed_plugins(config_oper))
            valid_plugins = set(plugin_manager.get_plugin_ids() or [])
            invalid_plugins = sorted(all_plugins - valid_plugins, key=str.lower)
            repo_url_map = CleanInvalidPlugin.__build_repo_url_map(plugin_manager)

            details = []
            for plugin_id in invalid_plugins:
                plugin_dir = CleanInvalidPlugin.__get_runtime_plugin_dir(plugin_id)
                source_dir = CleanInvalidPlugin.__find_local_source_dir(plugin_id)
                repo_url = repo_url_map.get(plugin_id) or ""
                source_type = "local" if source_dir else ("online" if repo_url else "missing")
                status = "运行目录存在但未被加载" if plugin_dir.exists() else "运行目录缺失"
                if source_dir:
                    status += "，本地源可用"
                elif repo_url:
                    status += "，在线源可用"

                details.append(
                    {
                        "id": plugin_id,
                        "title": f"{plugin_id} · {status}",
                        "status": status,
                        "runtime_path": str(plugin_dir),
                        "runtime_exists": plugin_dir.exists(),
                        "local_source_path": str(source_dir) if source_dir else "",
                        "repo_url": repo_url,
                        "source_type": source_type,
                    }
                )
            return details
        except Exception as e:
            logger.error(f"获取无效插件列表异常: {e}", exc_info=True)
            return []

    @staticmethod
    def __get_runtime_plugin_dir(plugin_id: str) -> Path:
        return Path(settings.ROOT_PATH) / "app" / "plugins" / plugin_id.lower()

    @staticmethod
    def __get_installed_plugins(config_oper: Optional[SystemConfigOper] = None) -> List[str]:
        config_oper = config_oper or SystemConfigOper()
        plugins = config_oper.get(SystemConfigKey.UserInstalledPlugins) or []
        return [str(plugin_id) for plugin_id in plugins if plugin_id]

    @staticmethod
    def __build_repo_url_map(plugin_manager: PluginManager) -> Dict[str, str]:
        """
        构建 plugin_id -> repo_url 映射，用于从市场或本地仓库重装。
        """
        repo_url_map: Dict[str, str] = {}
        try:
            online_plugins = plugin_manager.get_online_plugins() or []
        except Exception as e:
            online_plugins = []
            logger.warning(f"获取在线插件列表失败: {e}")
        try:
            local_repo_plugins = plugin_manager.get_local_repo_plugins() or []
        except Exception as e:
            local_repo_plugins = []
            logger.warning(f"获取本地仓库插件列表失败: {e}")

        for plugin in list(online_plugins) + list(local_repo_plugins):
            try:
                pid = getattr(plugin, "id", None)
                repo_url = getattr(plugin, "repo_url", None)
                if pid and repo_url and pid not in repo_url_map:
                    repo_url_map[pid] = repo_url
            except Exception:
                continue
        return repo_url_map

    @staticmethod
    def __reload_reinstalled_plugin(
        plugin_manager: PluginManager, plugin_id: str
    ) -> bool:
        """重装完成后立即载入插件，并刷新它的调度任务。"""
        try:
            plugin_manager.reload_plugin(plugin_id)
        except Exception as e:
            logger.warning(f"插件 {plugin_id} 重装后热重载失败: {e}", exc_info=True)
            return False

        try:
            Scheduler().update_plugin_job(plugin_id)
        except Exception as e:
            logger.warning(f"插件 {plugin_id} 热重载成功，但刷新调度任务失败: {e}")
        return True

    @staticmethod
    def __find_local_source_dir(plugin_id: str) -> Optional[Path]:
        candidates = []
        normalized_id = plugin_id.lower()

        try:
            current_file = Path(__file__).resolve()
            for parent in current_file.parents:
                if parent.name in ("plugins.v2", "plugins") and parent.parent.name == "localplugins":
                    candidates.append(parent / normalized_id)
                    candidates.append(parent / plugin_id)
        except Exception:
            pass

        for root in (
            Path("/config/localplugins/plugins.v2"),
            Path("/config/localplugins/plugins"),
            Path("/opt/moviepilot/config/localplugins/plugins.v2"),
            Path("/opt/moviepilot/config/localplugins/plugins"),
        ):
            candidates.append(root / normalized_id)
            candidates.append(root / plugin_id)

        for candidate in candidates:
            try:
                if candidate.exists() and candidate.is_dir() and (candidate / "__init__.py").exists():
                    return candidate
            except Exception:
                continue
        return None

    @staticmethod
    def __normalize_plugin_ids(plugin_ids: Any) -> List[str]:
        if not plugin_ids:
            return []
        if isinstance(plugin_ids, str):
            return [plugin_ids]
        if isinstance(plugin_ids, list):
            return [str(plugin_id) for plugin_id in plugin_ids if plugin_id]
        return []

    @staticmethod
    def __dedupe(plugin_ids: List[str]) -> List[str]:
        result = []
        seen = set()
        for plugin_id in plugin_ids:
            if plugin_id in seen:
                continue
            seen.add(plugin_id)
            result.append(plugin_id)
        return result

    @staticmethod
    def __ensure_static_asset_permissions():
        dist_dir = Path(__file__).resolve().parent / "dist"
        if not dist_dir.exists():
            return

        for path in [dist_dir, *dist_dir.rglob("*")]:
            try:
                if path.is_dir():
                    path.chmod(0o755)
                elif path.is_file():
                    path.chmod(0o644)
            except Exception as e:
                logger.debug(f"Skip static asset chmod for {path}: {e}")

    def __clear_pending_config(self):
        self._invalid_plugin_ids = []
        self.update_config(
            {
                "invalid_plugin_ids": [],
                "action_mode": self._action_mode,
            }
        )

    def __is_reinstall_running(self) -> bool:
        thread = self._job_thread
        return bool(
            thread
            and thread.is_alive()
            and self._reinstall_job.get("status") in {"queued", "running"}
        )

    def __update_job(self, **changes):
        with self._job_lock:
            self._reinstall_job = {**self._reinstall_job, **changes}
            self._last_result = dict(self._reinstall_job)

    def __get_last_result(self) -> Dict[str, Any]:
        with self._job_lock:
            return dict(self._last_result or {})

    @staticmethod
    def __now_text() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")
