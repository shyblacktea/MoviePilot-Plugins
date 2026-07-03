import unittest
import inspect
from types import SimpleNamespace

from subscribeplus import SubscribePlus
from subscribeplus.models import PluginConfig


class PluginConfigTest(unittest.TestCase):
    def test_plugin_metadata_and_vue_render_mode(self):
        plugin = SubscribePlus()

        self.assertEqual(plugin.plugin_name, "订阅下载增强")
        self.assertEqual(plugin.plugin_config_prefix, "subscribeplus_")
        self.assertEqual(plugin.get_render_mode(), ("vue", "dist/assets"))

    def test_config_defaults_select_all_categories_and_mp_sites(self):
        config = PluginConfig.from_dict({})

        self.assertFalse(config.enabled)
        self.assertEqual(config.delay_days, 1)
        self.assertEqual(config.selected_categories, [])
        self.assertTrue(config.notify_tg)
        self.assertFalse(config.allow_tg_rule_update)

    def test_config_normalizes_numeric_bounds(self):
        config = PluginConfig.from_dict({"delay_days": "-1", "max_scan_subscribes": "0"})

        self.assertEqual(config.delay_days, 0)
        self.assertEqual(config.max_scan_subscribes, 1)

    def test_post_api_endpoints_do_not_require_var_kwargs(self):
        plugin = SubscribePlus()
        post_apis = [api for api in plugin.get_api() if "POST" in api.get("methods", [])]

        self.assertTrue(post_apis)
        for api in post_apis:
            signature = inspect.signature(api["endpoint"])
            self.assertNotIn(
                inspect.Parameter.VAR_KEYWORD,
                {parameter.kind for parameter in signature.parameters.values()},
                msg=f"{api['path']} should use an explicit optional body parameter",
            )

    def test_subscribe_log_label_includes_title_and_ids(self):
        plugin = SubscribePlus()
        subscribe = SimpleNamespace(id=102, name="一念永恒", tmdbid=107371)

        self.assertEqual(plugin._describe_subscribe(subscribe), "一念永恒 ID=102 TMDB=107371")


if __name__ == "__main__":
    unittest.main()
