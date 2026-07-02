import unittest

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
        self.assertTrue(config.use_moviepilot_search_sites)
        self.assertEqual(config.category_sites, {})
        self.assertTrue(config.notify_tg)
        self.assertFalse(config.allow_tg_rule_update)

    def test_config_normalizes_numeric_bounds(self):
        config = PluginConfig.from_dict({"delay_days": "-1", "max_scan_subscribes": "0"})

        self.assertEqual(config.delay_days, 0)
        self.assertEqual(config.max_scan_subscribes, 1)


if __name__ == "__main__":
    unittest.main()
