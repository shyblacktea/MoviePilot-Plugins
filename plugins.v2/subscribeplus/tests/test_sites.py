import unittest

from subscribeplus.models import PluginConfig
from subscribeplus.sites import SiteResolver
from subscribeplus import SubscribePlus


class SiteResolverTest(unittest.TestCase):
    def test_resolve_for_category_uses_plugin_selected_sites(self):
        resolver = SiteResolver(lambda: [{"id": "baha", "name": "Baha"}, {"id": "cr", "name": "CR"}])
        config = PluginConfig.from_dict({"search_sites": ["baha", "unknown"]})

        self.assertEqual(resolver.resolve_for_category(config, "日番"), ["baha"])
        self.assertEqual(resolver.resolve_for_category(config, "日韩剧"), ["baha"])

    def test_resolve_for_category_defaults_to_all_available_sites(self):
        resolver = SiteResolver(lambda: [{"id": "baha", "name": "Baha"}, {"id": "cr", "name": "CR"}])
        config = PluginConfig.from_dict({})

        self.assertEqual(resolver.resolve_for_category(config, "日番"), ["baha", "cr"])

    def test_site_options_are_normalized_from_mixed_keys(self):
        resolver = SiteResolver(lambda: [{"id": 1, "name": "PT-A"}, {"value": 2, "title": "PT-B"}, {}])

        self.assertEqual(resolver.available_sites(), [{"id": "1", "name": "PT-A"}, {"id": "2", "name": "PT-B"}])

    def test_available_sites_ignore_moviepilot_search_site_selection(self):
        sites = SubscribePlus._normalize_indexer_sites(
            [
                {"id": 1, "name": "PT-A", "is_active": True},
                {"id": 2, "name": "PT-B", "is_active": False},
                {"id": 3, "name": "PT-C"},
            ]
        )

        self.assertEqual(sites, [{"id": "1", "name": "PT-A"}, {"id": "3", "name": "PT-C"}])


if __name__ == "__main__":
    unittest.main()
