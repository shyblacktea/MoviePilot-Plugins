import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.plugin import PluginManager
from app.db.systemconfig_oper import SystemConfigOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import SystemConfigKey, EventType
from app.helper.plugin import PluginHelper


class CleanInvalidPlugin(_PluginBase):
    # 插件名称
    plugin_name = "清理无效插件"
    # 插件描述
    plugin_desc = "删除或重新安装数据库中无法安装的插件记录。"
    # 插件图标
    plugin_icon = "delete.jpg"
    # 插件版本
    plugin_version = "1.1"
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
    _invalid_plugin_ids = []
    # 操作模式：clean 清理 / reinstall 重新安装
    _action_mode = "clean"

    def init_plugin(self, config: dict = None):
        """
        生效配置信息

        :param config: 配置信息字典
        """
        try:
            if not config:
                return
            self._invalid_plugin_ids = config.get("invalid_plugin_ids") or []
            self._action_mode = config.get("action_mode") or "clean"

            if not self._invalid_plugin_ids:
                return

            if self._action_mode == "reinstall":
                self._reinstall_plugins()
            else:
                self._clean_plugins()

        except Exception as e:
            logger.error(f"异常: {e}", exc_info=True)

    def _clean_plugins(self):
        """
        清理选中的无效插件
        """
        config_oper = SystemConfigOper()
        plugin_manager = PluginManager()

        valid_plugins = set(plugin_manager.get_plugin_ids() or [])
        all_plugins: List[str] = (
            config_oper.get(SystemConfigKey.UserInstalledPlugins) or []
        )

        all_plugins_modified = []
        for plugin_id in all_plugins:
            if plugin_id not in self._invalid_plugin_ids:
                all_plugins_modified.append(plugin_id)
                continue
            try:
                if plugin_id in valid_plugins:
                    all_plugins_modified.append(plugin_id)
                    logger.warn(f"{plugin_id} 是有效插件，跳过清理")
                    continue
                logger.info(f"正在清理无效插件 {plugin_id}")
                plugin_dir = (
                    Path(settings.ROOT_PATH) / "app" / "plugins" / plugin_id.lower()
                )
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir, ignore_errors=True)
                else:
                    logger.warn(f"插件目录 {plugin_dir} 不存在")
            except Exception as e:
                logger.warn(
                    f"清理无效插件 {plugin_id} 产生异常: {e}", exc_info=True
                )

        config_oper.set(SystemConfigKey.UserInstalledPlugins, all_plugins_modified)
        self._invalid_plugin_ids = []
        self.update_config(
            {
                "invalid_plugin_ids": [],
                "action_mode": self._action_mode,
            }
        )

    def _reinstall_plugins(self):
        """
        重新安装选中的无效插件
        """
        config_oper = SystemConfigOper()
        plugin_manager = PluginManager()
        plugin_helper = PluginHelper()

        valid_plugins = set(plugin_manager.get_plugin_ids() or [])
        all_plugins: List[str] = (
            config_oper.get(SystemConfigKey.UserInstalledPlugins) or []
        )

        success_count = 0
        fail_count = 0

        for plugin_id in self._invalid_plugin_ids:
            try:
                # 检查是否有效
                if plugin_id in valid_plugins:
                    logger.warn(f"{plugin_id} 已是有效插件，跳过重装")
                    continue

                logger.info(f"正在重装插件 {plugin_id}")

                # 1. 清理旧插件目录
                plugin_dir = (
                    Path(settings.ROOT_PATH) / "app" / "plugins" / plugin_id.lower()
                )
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir, ignore_errors=True)

                # 2. 从已安装列表中移除
                all_plugins = [p for p in all_plugins if p != plugin_id]

                # 3. 尝试从插件市场安装
                plugin_info = plugin_helper.get_plugin_by_id(plugin_id)
                if plugin_info:
                    plugin_helper.download_plugin(
                        plugin_id=plugin_id,
                        plugin_info=plugin_info,
                    )
                    success_count += 1
                    logger.info(f"插件 {plugin_id} 重装成功")
                else:
                    logger.warn(f"插件 {plugin_id} 在市场中未找到，跳过重装")
                    fail_count += 1

            except Exception as e:
                logger.warn(
                    f"重装插件 {plugin_id} 产生异常: {e}", exc_info=True
                )
                fail_count += 1

        # 更新安装记录
        config_oper.set(SystemConfigKey.UserInstalledPlugins, all_plugins)

        # 发送通知
        if success_count > 0:
            self.post_message(
                title="插件重装完成",
                text=f"成功重装 {success_count} 个插件"
                + (f"，{fail_count} 个失败" if fail_count > 0 else ""),
            )

        self._invalid_plugin_ids = []
        self.update_config(
            {
                "invalid_plugin_ids": [],
                "action_mode": self._action_mode,
            }
        )

    def get_state(self) -> bool:
        """
        获取插件运行状态
        """
        return False

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        注册插件远程命令
        """
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        """
        注册插件API
        """
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面

        :return: 1、页面配置（vuetify模式）；2、默认数据结构
        """
        invalid_items = self.get_invalid_plugins()
        has_invalid = len(invalid_items) > 0

        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "multiple": True,
                                            "chips": True,
                                            "model": "invalid_plugin_ids",
                                            "label": "选择要处理的插件",
                                            "items": invalid_items,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "action_mode",
                                            "label": "操作方式",
                                            "items": [
                                                {"title": "清理（删除插件记录）", "value": "clean"},
                                                {"title": "重新安装（从市场重装）", "value": "reinstall"},
                                            ],
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
                                },
                                "content": [
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "info" if has_invalid else "success",
                                            "variant": "tonal",
                                            "text": (
                                                f"当前有{len(invalid_items)}个插件无法安装，"
                                                f"选择插件后选择操作方式，点击【保存】执行"
                                                if has_invalid
                                                else "所有插件均已成功安装，无需处理"
                                            ),
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
                                "props": {
                                    "cols": 12,
                                },
                                "content": [
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "warning",
                                            "variant": "tonal",
                                            "text": (
                                                "提示：重新安装需要网络连接正常，"
                                                "且插件市场中有对应插件源。"
                                            ),
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ], {
            "invalid_plugin_ids": self._invalid_plugin_ids,
            "action_mode": "clean",
        }

    def get_page(self) -> List[dict]:
        """
        拼装插件详情页面
        """
        pass

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
        try:
            config_oper = SystemConfigOper()
            plugin_manager = PluginManager()

            all_plugins = set(
                config_oper.get(SystemConfigKey.UserInstalledPlugins) or []
            )
            valid_plugins = set(plugin_manager.get_plugin_ids() or [])
            invalid_plugins = all_plugins - valid_plugins

            return [
                {"title": f"{plugin_id}", "value": plugin_id}
                for plugin_id in invalid_plugins
            ]
        except Exception as e:
            logger.error(f"异常: {e}", exc_info=True)
            return []