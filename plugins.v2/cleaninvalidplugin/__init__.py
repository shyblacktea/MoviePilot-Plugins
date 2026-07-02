import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.plugin import PluginManager
from app.db.systemconfig_oper import SystemConfigOper
from app.helper.plugin import PluginHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import SystemConfigKey


class CleanInvalidPlugin(_PluginBase):
    # 插件名称
    plugin_name = "清理无效插件"
    # 插件描述
    plugin_desc = "扫描、清理或重新安装数据库中无法加载的插件记录。"
    # 插件图标
    plugin_icon = "delete.jpg"
    # 插件版本
    plugin_version = "1.3"
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
                self._last_result = None
                return

            if self._action_mode == "reinstall":
                self._last_result = self._reinstall_plugins()
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

    def _reinstall_plugins(self) -> Dict[str, Any]:
        """
        重新安装选中的无效插件
        """
        config_oper = SystemConfigOper()
        plugin_manager = PluginManager()
        plugin_helper = PluginHelper()

        valid_plugins = set(plugin_manager.get_plugin_ids() or [])
        all_plugins = self.__get_installed_plugins(config_oper)
        selected_plugins = set(self._invalid_plugin_ids)
        next_plugins = [p for p in all_plugins if p not in selected_plugins]

        reinstalled_plugins = []
        skipped_plugins = []
        failed_plugins = []

        for plugin_id in self._invalid_plugin_ids:
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
                    reinstalled_plugins.append(plugin_id)
                    logger.info(f"已从本地插件源重装 {plugin_id}: {local_source_dir}")
                    continue

                plugin_info = plugin_helper.get_plugin_by_id(plugin_id)
                if plugin_info:
                    plugin_helper.download_plugin(
                        plugin_id=plugin_id,
                        plugin_info=plugin_info,
                    )
                    next_plugins.append(plugin_id)
                    reinstalled_plugins.append(plugin_id)
                    logger.info(f"插件 {plugin_id} 已从插件市场重装")
                else:
                    next_plugins.append(plugin_id)
                    failed_plugins.append(plugin_id)
                    logger.warning(f"插件 {plugin_id} 在本地源和插件市场中均未找到，保留原记录")

            except Exception as e:
                next_plugins.append(plugin_id)
                failed_plugins.append(plugin_id)
                logger.warning(f"重装插件 {plugin_id} 产生异常: {e}", exc_info=True)

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
                "last_result": self._last_result,
            },
        }

    def get_last_result_api(self) -> Dict[str, Any]:
        """
        获取最近执行结果API
        """
        return {"success": True, "data": self._last_result or {}}

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

            details = []
            for plugin_id in invalid_plugins:
                plugin_dir = CleanInvalidPlugin.__get_runtime_plugin_dir(plugin_id)
                source_dir = CleanInvalidPlugin.__find_local_source_dir(plugin_id)
                status = "运行目录存在但未被加载" if plugin_dir.exists() else "运行目录缺失"
                if source_dir:
                    status += "，本地源可用"

                details.append(
                    {
                        "id": plugin_id,
                        "title": f"{plugin_id} · {status}",
                        "status": status,
                        "runtime_path": str(plugin_dir),
                        "runtime_exists": plugin_dir.exists(),
                        "local_source_path": str(source_dir) if source_dir else "",
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
