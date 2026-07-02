import unittest

from subscribeplus.models import PluginConfig
from subscribeplus.sites import SiteResolver


class SiteResolverTest(unittest.TestCase):
    def test_category_sites_are_limited_to_moviepilot_sites(self):
        resolver = SiteResolver(lambda: [{"id": "baha", "name": "Baha"}, {"id": "cr", "name": "CR"}])
        config = PluginConfig.from_dict({"category_sites": {"日番": ["baha", "unknown"]}})

        self.assertEqual(resolver.resolve_for_category(config, "日番"), ["baha"])
        self.assertEqual(resolver.resolve_for_category(config, "日韩剧"), ["baha", "cr"])

    def test_site_options_are_normalized_from_mixed_keys(self):
        resolver = SiteResolver(lambda: [{"id": 1, "name": "PT-A"}, {"value": 2, "title": "PT-B"}, {}])

        self.assertEqual(resolver.available_sites(), [{"id": "1", "name": "PT-A"}, {"id": "2", "name": "PT-B"}])


if __name__ == "__main__":
    unittest.main()
