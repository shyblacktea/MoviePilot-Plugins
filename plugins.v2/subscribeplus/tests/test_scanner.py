import unittest
from datetime import date
from types import SimpleNamespace

from subscribeplus.scanner import (
    SubscriptionScanner,
    episode_in_seasoninfo,
    episode_in_transfer_history,
    normalize_category,
    should_check_episode,
)
from subscribeplus.models import PluginConfig
from subscribeplus.sites import SiteResolver


class ScannerTest(unittest.TestCase):
    def test_episode_air_date_plus_delay_triggers_on_next_day(self):
        self.assertTrue(should_check_episode(date(2026, 7, 3), delay_days=1, today=date(2026, 7, 4)))
        self.assertFalse(should_check_episode(date(2026, 7, 3), delay_days=1, today=date(2026, 7, 3)))

    def test_transfer_history_episode_range_matches_target(self):
        histories = [{"tmdbid": 100, "season": 1, "episodes": "1-3"}]

        self.assertTrue(episode_in_transfer_history(histories, tmdbid=100, season=1, episode=2))
        self.assertFalse(episode_in_transfer_history(histories, tmdbid=100, season=1, episode=4))

    def test_seasoninfo_matches_episode_lists(self):
        seasoninfo = [{"season": 1, "episodes": [1, 2, 3]}]

        self.assertTrue(episode_in_seasoninfo(seasoninfo, season=1, episode=2))
        self.assertFalse(episode_in_seasoninfo(seasoninfo, season=1, episode=4))

    def test_seasoninfo_matches_moviepilot_dict_keys(self):
        seasoninfo = {"1": [1, 2, 3]}

        self.assertTrue(episode_in_seasoninfo(seasoninfo, season=1, episode=2))
        self.assertFalse(episode_in_seasoninfo(seasoninfo, season=1, episode=4))

    def test_blank_category_is_uncategorized(self):
        self.assertEqual(normalize_category(""), "未分类")
        self.assertEqual(normalize_category(None), "未分类")

    def test_collect_categories_prefers_moviepilot_category_strategy(self):
        scanner = SubscriptionScanner(
            load_subscribes=lambda: [
                SimpleNamespace(id=1, state="R", type="电视剧", media_category="", category=""),
            ],
            load_tmdb_episodes=lambda tmdbid, season, episode_group: [],
            is_episode_downloaded=lambda tmdbid, season, episode: (False, ""),
            load_categories=lambda: ["日番", "日韩剧"],
        )

        self.assertEqual(scanner.collect_categories(), ["日番", "日韩剧", "未分类"])

    def test_scan_filters_by_resolved_category_when_subscribe_has_no_category(self):
        subscribe = SimpleNamespace(
            id=1,
            state="R",
            type="电视剧",
            name="测试日番",
            tmdbid=100,
            season=1,
            media_category="",
            category="",
            include="",
            episode_group=None,
        )
        scanner = SubscriptionScanner(
            load_subscribes=lambda: [subscribe],
            load_tmdb_episodes=lambda tmdbid, season, episode_group: [
                {"episode_number": 1, "air_date": "2026-07-03"},
            ],
            is_episode_downloaded=lambda tmdbid, season, episode: (False, "未命中"),
            load_categories=lambda: ["日番", "日韩剧"],
            resolve_subscribe_category=lambda item: "日番",
        )
        resolver = SiteResolver(lambda: [{"id": "1", "name": "PT1"}])

        results = scanner.scan(
            PluginConfig(selected_categories=["日番"], delay_days=1),
            resolver,
            today=date(2026, 7, 4),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].category, "日番")


if __name__ == "__main__":
    unittest.main()
