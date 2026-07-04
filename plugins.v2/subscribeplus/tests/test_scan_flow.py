import unittest
from types import SimpleNamespace
from unittest.mock import patch

import subscribeplus as subscribeplus_module
from subscribeplus import SubscribePlus
from subscribeplus.models import DiagnosisInput, DiagnosisItem, PluginConfig, StaleEpisode


class FakeStore:
    def __init__(self):
        self.saved_results = None

    def save_scan_results(self, results):
        self.saved_results = results

    def save_scan_meta(self, *_args, **_kwargs):
        pass


class FakeScanner:
    def __init__(self, items):
        self.items = items

    def scan(self, _config, _resolver):
        return self.items


class FakeSiteResolver:
    def __init__(self, sites):
        self.sites = sites

    def resolve_for_category(self, _config, _category):
        return self.sites


def make_input():
    return DiagnosisInput(
        subscribe_id=12,
        title="One Piece",
        tmdbid=37854,
        season=23,
        category="日番",
        include="Baha",
        sites=["13"],
        episodes=[StaleEpisode(season=23, episode=1156, air_date="2026-07-01")],
    )


class ScanFlowTest(unittest.TestCase):
    def make_plugin(self, item):
        plugin = SubscribePlus()
        plugin._plugin_config = PluginConfig(enabled=True, notify_tg=False, max_scan_subscribes=20)
        plugin._store = FakeStore()
        plugin._scanner = FakeScanner([item])
        plugin._site_resolver = object()
        return plugin

    def test_mp_downloadable_result_is_left_to_moviepilot_without_tg_result(self):
        item = make_input()
        plugin = self.make_plugin(item)
        native_calls = []
        fallback_calls = []
        plugin._run_moviepilot_subscribe_search_for_item = lambda scanned: native_calls.append(scanned.subscribe_id)
        plugin._diagnose_with_moviepilot_subscription_scope = lambda _item, _mp_search=None: DiagnosisItem(
            subscribe_id=item.subscribe_id,
            title=item.title,
            tmdbid=item.tmdbid,
            season=item.season,
            category=item.category,
            reason="downloadable",
            message="MP 订阅搜索已存在可匹配资源",
            candidates=[{"title": "One.Piece.S23E1156.Baha-FROGWeb"}],
        )
        plugin._ensure_diagnoser = lambda: type(
            "FallbackDiagnoser",
            (),
            {"diagnose": lambda _self, _item: fallback_calls.append(_item.subscribe_id)},
        )()

        infos = []
        with patch.object(subscribeplus_module.logger, "info", side_effect=infos.append):
            result = plugin.run_scan()

        self.assertEqual(native_calls, [12])
        self.assertEqual(fallback_calls, [])
        self.assertEqual(result["count"], 0)
        self.assertEqual(plugin._store.saved_results, [])
        self.assertTrue(any("触发 MP 订阅搜索后发现可匹配资源" in item for item in infos))
        self.assertTrue(any("剧名=One Piece" in item and "订阅ID=12" in item and "E1156" in item for item in infos))

    def test_subscription_scope_missing_target_notifies_when_plugin_pt_scope_has_target(self):
        item = DiagnosisInput(
            subscribe_id=88,
            title="吞噬星空",
            tmdbid=94664,
            season=1,
            category="国漫",
            include="HHWEB|FROGWeb",
            sites=["13"],
            episodes=[StaleEpisode(season=1, episode=230, air_date="2026-07-04")],
        )
        plugin = self.make_plugin(item)
        plugin._plugin_config.search_sites = ["13", "20", "27"]
        plugin._site_resolver = FakeSiteResolver(["13", "20", "27"])
        plugin._load_moviepilot_subscribe_sites = lambda _item: ["13"]
        plugin._run_moviepilot_subscribe_search_for_item = lambda _item: {
            "matched_contexts": [],
            "diagnostic_contexts": [],
            "raw_torrents": [
                SimpleNamespace(
                    site=13,
                    site_name="憨憨",
                    title="吞噬星空 S01E229 2026 2160p WEB-DL H265-HHWEB",
                    seeders=23,
                )
            ],
        }
        search_calls = []

        def fake_search(scanned):
            search_calls.append(scanned.sites)
            return [
                {
                    "site": "20",
                    "site_name": "观众",
                    "title": "吞噬星空 S01E230 2026 2160p WEB-DL H265-HHWEB",
                    "recognized": True,
                    "season": 1,
                    "episode": 230,
                    "seeders": 9,
                },
                {
                    "site": "27",
                    "site_name": "青蛙",
                    "title": "吞噬星空 S01E229 2026 2160p WEB-DL H265-FROGWeb",
                    "recognized": True,
                    "season": 1,
                    "episode": 229,
                    "seeders": 20,
                },
            ]

        plugin._search_torrents = fake_search

        result = plugin.run_scan()

        self.assertEqual(result["count"], 1)
        self.assertEqual(search_calls, [["20", "27"]])
        saved = plugin._store.saved_results[0]
        self.assertEqual(saved["reason"], "site_scope_blocked")
        self.assertEqual(saved["source"], "plugin_pt_scope")
        self.assertEqual(saved["sites"], ["20", "27"])
        self.assertEqual([candidate["episode"] for candidate in saved["candidates"]], [230])
        self.assertEqual(saved["subscription_site_progress"][0]["site_name"], "憨憨")
        self.assertEqual(saved["subscription_site_progress"][0]["latest_episode"], 229)

    def test_diagnose_one_api_scans_single_episode_and_notifies_result(self):
        plugin = SubscribePlus()
        plugin._plugin_config = PluginConfig(enabled=True, notify_tg=True, max_scan_subscribes=20)
        plugin._store = FakeStore()
        plugin._site_resolver = FakeSiteResolver(["13", "20"])
        plugin._get_subscribe = lambda subscribe_id: SimpleNamespace(
            id=subscribe_id,
            name="Swallowed Star",
            tmdbid=101172,
            season=1,
            media_category="anime",
            include="HHWEB",
            type="tv",
            episode_group=None,
        )
        plugin._load_tmdb_episodes = lambda _tmdbid, _season, _group: [
            {"episode_number": 230, "air_date": "2026-06-29"}
        ]
        plugin._is_episode_downloaded = lambda _tmdbid, _season, _episode: (False, "manual diagnosis")
        captured_inputs = []

        def fake_diagnose(scanned):
            captured_inputs.append(scanned)
            return DiagnosisItem(
                subscribe_id=scanned.subscribe_id,
                title=scanned.title,
                tmdbid=scanned.tmdbid,
                season=scanned.season,
                category=scanned.category,
                reason="site_scope_blocked",
                message="other PT sites have target episode",
                episodes=[episode.to_dict() for episode in scanned.episodes],
                candidates=[{"site": "20", "site_name": "Audiences", "title": "S01E230"}],
                sites=["20"],
                source="plugin_pt_scope",
            )

        plugin._diagnose_item = fake_diagnose
        notified = []
        plugin._notify_each_show = lambda results: notified.extend(results)

        result = plugin.diagnose_one_api({"subscribe_id": 91, "episode": 230, "notify": True})

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(captured_inputs), 1)
        self.assertEqual(captured_inputs[0].subscribe_id, 91)
        self.assertEqual(captured_inputs[0].episodes[0].episode, 230)
        self.assertEqual(captured_inputs[0].sites, ["13", "20"])
        self.assertEqual(plugin._store.saved_results[0]["reason"], "site_scope_blocked")
        self.assertEqual(notified[0]["source"], "plugin_pt_scope")

    def test_mp_rule_blocked_candidates_are_notified_without_plugin_fallback(self):
        item = make_input()
        plugin = self.make_plugin(item)
        fallback_calls = []
        plugin._run_moviepilot_subscribe_search_for_item = lambda _item: None
        plugin._diagnose_with_moviepilot_subscription_scope = lambda _item, _mp_search=None: DiagnosisItem(
            subscribe_id=item.subscribe_id,
            title=item.title,
            tmdbid=item.tmdbid,
            season=item.season,
            category=item.category,
            reason="rule_blocked",
            message="MP 订阅搜索范围内存在季集正确资源，但被订阅规则拦截",
            candidates=[{"title": "One.Piece.S23E1156.CR-ADWeb"}],
        )
        plugin._ensure_diagnoser = lambda: type(
            "FallbackDiagnoser",
            (),
            {"diagnose": lambda _self, _item: fallback_calls.append(_item.subscribe_id)},
        )()

        result = plugin.run_scan()

        self.assertEqual(fallback_calls, [])
        self.assertEqual(result["count"], 1)
        self.assertEqual(plugin._store.saved_results[0]["reason"], "rule_blocked")

    def test_plugin_pt_scope_without_target_keeps_scan_quiet(self):
        item = make_input()
        plugin = self.make_plugin(item)
        search_calls = []
        plugin._site_resolver = FakeSiteResolver(["13", "20"])
        plugin._run_moviepilot_subscribe_search_for_item = lambda _item: {"matched_contexts": [], "diagnostic_contexts": [], "raw_torrents": []}
        plugin._diagnose_with_moviepilot_subscription_scope = lambda _item, _mp_search=None: DiagnosisItem(
            subscribe_id=item.subscribe_id,
            title=item.title,
            tmdbid=item.tmdbid,
            season=item.season,
            category=item.category,
            reason="no_pt_resource",
            message="MP 订阅搜索范围未搜索到覆盖目标集的 PT 资源",
            candidates=[],
            sites=["13"],
        )
        plugin._search_torrents = lambda scanned: search_calls.append(scanned.sites) or []

        result = plugin.run_scan()

        self.assertEqual(search_calls, [["20"]])
        self.assertEqual(result["count"], 0)
        self.assertEqual(plugin._store.saved_results, [])

    def test_moviepilot_diagnostic_contexts_are_converted_to_rule_blocked_candidates(self):
        item = make_input()
        plugin = self.make_plugin(item)
        plugin._load_moviepilot_subscribe_sites = lambda _item: ["13"]
        context = SimpleNamespace(
            torrent_info=SimpleNamespace(
                site=13,
                site_name="春天",
                title="One.Piece.S23E1156.2026.1080p.Baha.WEB-DL.H264-ADWeb",
                description="",
                seeders=5,
                size=1024,
                downloadvolumefactor=0,
            ),
            media_info=SimpleNamespace(tmdb_id=37854),
            meta_info=SimpleNamespace(season_list=[23], episode_list=[1156]),
            candidate_recognized=False,
            media_info_is_target=True,
        )

        diagnosis = plugin._diagnose_with_moviepilot_subscription_scope(
            item,
            {"matched_contexts": [], "diagnostic_contexts": [context]},
        )

        self.assertEqual(diagnosis.reason, "rule_blocked")
        self.assertEqual(diagnosis.sites, ["13"])
        self.assertEqual(len(diagnosis.candidates), 1)
        self.assertEqual(diagnosis.candidates[0]["site_name"], "春天")
        self.assertEqual(diagnosis.candidates[0]["episode"], 1156)
        self.assertIn("Baha", diagnosis.candidates[0]["platforms"])
        self.assertIn("ADWeb", diagnosis.candidates[0]["release_groups"])
        self.assertTrue(diagnosis.candidates[0]["download_payload"])


if __name__ == "__main__":
    unittest.main()
