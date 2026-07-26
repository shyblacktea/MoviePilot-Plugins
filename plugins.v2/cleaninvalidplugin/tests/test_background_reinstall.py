import importlib.util
import sys
import threading
import time
import types
import unittest
from pathlib import Path


PLUGIN_FILE = Path(__file__).resolve().parents[1] / "__init__.py"


def _install_stub(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _Settings:
    ROOT_PATH = Path("/tmp/moviepilot-test")


class _PluginBase:
    def update_config(self, _config):
        return True

    def post_message(self, **_kwargs):
        return None


class _SystemConfigKey:
    UserInstalledPlugins = "UserInstalledPlugins"


class _Scheduler:
    def update_plugin_job(self, _plugin_id):
        return None


def _load_plugin_class():
    app = _install_stub("app")
    app.__path__ = []
    for package in ("app.core", "app.db", "app.helper", "app.schemas"):
        module = _install_stub(package)
        module.__path__ = []

    _install_stub("app.core.config", settings=_Settings())
    _install_stub("app.core.plugin", PluginManager=object)
    _install_stub("app.db.systemconfig_oper", SystemConfigOper=object)
    _install_stub("app.helper.plugin", PluginHelper=object)
    log = lambda *_args, **_kwargs: None
    _install_stub(
        "app.log",
        logger=types.SimpleNamespace(error=log, info=log, warning=log, debug=log),
    )
    _install_stub("app.plugins", _PluginBase=_PluginBase)
    _install_stub("app.scheduler", Scheduler=_Scheduler)
    _install_stub("app.schemas.types", SystemConfigKey=_SystemConfigKey)

    module_name = "cleaninvalidplugin_background_test"
    spec = importlib.util.spec_from_file_location(module_name, PLUGIN_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.CleanInvalidPlugin


class BackgroundReinstallTest(unittest.TestCase):
    def setUp(self):
        self.plugin_class = _load_plugin_class()
        self.plugin = self.plugin_class()

    def _wait_until_finished(self, timeout=1.5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = self.plugin.get_last_result_api()["data"]
            if result.get("status") in {"completed", "failed"}:
                return result
            time.sleep(0.01)
        self.fail("background reinstall did not finish")

    def test_reinstall_returns_immediately_and_finishes_in_background(self):
        release_worker = threading.Event()

        def slow_reinstall(*_args, **kwargs):
            progress = kwargs.get("progress_callback")
            if progress:
                progress("DemoPlugin", 0, 1)
            release_worker.wait(0.3)
            if progress:
                progress("", 1, 1)
            return {
                "action": "reinstall",
                "success": True,
                "reinstalled": ["DemoPlugin"],
                "skipped": [],
                "failed": [],
                "message": "已重装 1 个插件",
            }

        self.plugin._reinstall_plugins = slow_reinstall

        started_at = time.monotonic()
        self.plugin.init_plugin(
            {"invalid_plugin_ids": ["DemoPlugin"], "action_mode": "reinstall"}
        )
        elapsed = time.monotonic() - started_at

        self.assertLess(elapsed, 0.1)
        running = self.plugin.get_last_result_api()["data"]
        self.assertIn(running.get("status"), {"queued", "running"})

        release_worker.set()
        finished = self._wait_until_finished()
        self.assertEqual(finished["status"], "completed")
        self.assertEqual(finished["progress"], 100)
        self.assertEqual(finished["completed"], 1)

    def test_second_reinstall_does_not_start_another_worker(self):
        release_worker = threading.Event()
        call_count = 0

        def slow_reinstall(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            release_worker.wait(0.3)
            return {
                "action": "reinstall",
                "success": True,
                "reinstalled": ["DemoPlugin"],
                "skipped": [],
                "failed": [],
                "message": "已重装 1 个插件",
            }

        self.plugin._reinstall_plugins = slow_reinstall
        config = {"invalid_plugin_ids": ["DemoPlugin"], "action_mode": "reinstall"}

        self.plugin.init_plugin(config)
        self.plugin.init_plugin(config)
        release_worker.set()
        self._wait_until_finished()

        self.assertEqual(call_count, 1)

    def test_online_reinstall_hot_reloads_plugin_and_scheduler(self):
        module = sys.modules[self.plugin_class.__module__]
        events = []

        class FakePluginManager:
            def get_plugin_ids(self):
                return []

            def reload_plugin(self, plugin_id):
                events.append(("reload", plugin_id))

        class FakeSystemConfigOper:
            def get(self, _key):
                return ["OnlinePlugin"]

            def set(self, _key, value):
                events.append(("installed", list(value)))

        class FakePluginHelper:
            def install(self, **kwargs):
                events.append(("install", kwargs))
                return True, "ok"

        class FakeScheduler:
            def update_plugin_job(self, plugin_id):
                events.append(("schedule", plugin_id))

        module.PluginManager = FakePluginManager
        module.SystemConfigOper = FakeSystemConfigOper
        module.PluginHelper = FakePluginHelper
        module.Scheduler = FakeScheduler
        self.plugin._CleanInvalidPlugin__build_repo_url_map = (
            lambda _manager: {"OnlinePlugin": "https://example.invalid/plugins"}
        )
        self.plugin._CleanInvalidPlugin__find_local_source_dir = lambda _plugin_id: None
        self.plugin._CleanInvalidPlugin__get_runtime_plugin_dir = (
            lambda _plugin_id: Path("/tmp/moviepilot-test/missing-plugin")
        )

        result = self.plugin._reinstall_plugins(["OnlinePlugin"])

        self.assertTrue(result["success"])
        self.assertIn(("reload", "OnlinePlugin"), events)
        self.assertIn(("schedule", "OnlinePlugin"), events)
        install_event = next(event for event in events if event[0] == "install")
        self.assertTrue(install_event[1]["force_install"])

    def test_invalid_details_identify_local_online_and_missing_sources(self):
        module = sys.modules[self.plugin_class.__module__]

        class FakePluginManager:
            def get_plugin_ids(self):
                return []

        class FakeSystemConfigOper:
            def get(self, _key):
                return ["LocalPlugin", "OnlinePlugin", "MissingPlugin"]

        module.PluginManager = FakePluginManager
        module.SystemConfigOper = FakeSystemConfigOper
        self.plugin_class._CleanInvalidPlugin__build_repo_url_map = staticmethod(
            lambda _manager: {"OnlinePlugin": "https://example.invalid/plugins"}
        )
        self.plugin_class._CleanInvalidPlugin__get_runtime_plugin_dir = staticmethod(
            lambda plugin_id: Path(f"/tmp/moviepilot-test/{plugin_id}")
        )
        self.plugin_class._CleanInvalidPlugin__find_local_source_dir = staticmethod(
            lambda plugin_id: Path("/tmp/local/LocalPlugin")
            if plugin_id == "LocalPlugin"
            else None
        )

        details = {
            item["id"]: item for item in self.plugin_class.get_invalid_plugin_details()
        }

        self.assertEqual(details["LocalPlugin"]["source_type"], "local")
        self.assertEqual(details["OnlinePlugin"]["source_type"], "online")
        self.assertEqual(details["MissingPlugin"]["source_type"], "missing")


if __name__ == "__main__":
    unittest.main()
