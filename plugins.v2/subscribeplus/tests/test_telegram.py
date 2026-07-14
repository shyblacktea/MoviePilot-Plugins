import sys
import types
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import subscribeplus as subscribeplus_module
from subscribeplus import SubscribePlus
from subscribeplus.telegram import (
    build_ci_done_menu,
    build_ci_manual_type_menu,
    build_ci_mode_menu,
    build_main_menu,
    build_pending_menu,
    build_resource_menu,
    build_rule_confirm_menu,
    build_rule_done_menu,
    build_rule_menu,
    make_callback,
    render_identifier_fix_result_text,
    render_notification_text,
    render_rule_preview_text,
)


def flatten_buttons(menu):
    return [button for row in menu for button in row]


def install_fake_scheduler(scheduler_cls):
    app_module = types.ModuleType("app")
    app_module.__path__ = []
    scheduler_module = types.ModuleType("app.scheduler")
    scheduler_module.Scheduler = scheduler_cls
    old_app = sys.modules.get("app")
    old_scheduler = sys.modules.get("app.scheduler")
    sys.modules["app"] = app_module
    sys.modules["app.scheduler"] = scheduler_module

    def restore():
        if old_app is None:
            sys.modules.pop("app", None)
        else:
            sys.modules["app"] = old_app
        if old_scheduler is None:
            sys.modules.pop("app.scheduler", None)
        else:
            sys.modules["app.scheduler"] = old_scheduler

    return restore


def install_fake_download_chain(download_chain_cls):
    app_module = types.ModuleType("app")
    app_module.__path__ = []
    chain_module = types.ModuleType("app.chain")
    chain_module.__path__ = []
    download_module = types.ModuleType("app.chain.download")
    download_module.DownloadChain = download_chain_cls
    old_app = sys.modules.get("app")
    old_chain = sys.modules.get("app.chain")
    old_download = sys.modules.get("app.chain.download")
    sys.modules["app"] = app_module
    sys.modules["app.chain"] = chain_module
    sys.modules["app.chain.download"] = download_module

    def restore():
        if old_app is None:
            sys.modules.pop("app", None)
        else:
            sys.modules["app"] = old_app
        if old_chain is None:
            sys.modules.pop("app.chain", None)
        else:
            sys.modules["app.chain"] = old_chain
        if old_download is None:
            sys.modules.pop("app.chain.download", None)
        else:
            sys.modules["app.chain.download"] = old_download

    return restore


class TelegramTest(unittest.TestCase):
    def test_callback_uses_short_token_and_plugin_prefix(self):
        callback = make_callback("download", "abc123")

        self.assertEqual(callback, "[PLUGIN]SubscribePlus|download:abc123")
        self.assertLessEqual(len(callback.encode("utf-8")), 64)

    def test_each_show_gets_own_token(self):
        first = build_main_menu(token="show1", allow_rule_update=True)
        second = build_main_menu(token="show2", allow_rule_update=True)

        self.assertNotEqual(first, second)

    def test_main_menu_has_snooze_3_days_button(self):
        callbacks = [button["callback_data"] for button in flatten_buttons(build_main_menu("show1", True))]

        self.assertIn("[PLUGIN]SubscribePlus|snooze3d:show1", callbacks)

    def test_main_menu_has_manual_pt_scope_search_button_on_own_row(self):
        menu = build_main_menu("show1", True)

        self.assertIn({"text": "PT范围搜索", "callback_data": make_callback("ptscope", "show1")}, menu[1])
        self.assertEqual(len(menu[1]), 1)

    def test_main_menu_can_page_candidate_details(self):
        menu = build_main_menu("show1", True, candidate_count=13, candidate_page=0)
        callbacks = [button["callback_data"] for button in flatten_buttons(menu)]

        self.assertIn(make_callback("cand2", "show1"), callbacks)

    def test_ci_command_is_registered(self):
        commands = SubscribePlus.get_command()
        command = next(item for item in commands if item["cmd"] == "/ci")

        self.assertEqual(command["data"]["action"], "subscribeplus_ci")

    def test_sp_command_is_registered(self):
        commands = SubscribePlus.get_command()
        command = next(item for item in commands if item["cmd"] == "/sp")

        self.assertEqual(command["data"]["action"], "subscribeplus_pending")

    def test_resource_menu_has_back_button(self):
        menu = build_resource_menu("tok", [{"site_name": "PT-A", "seeders": 10, "title": "Show"}])
        callbacks = [button["callback_data"] for button in menu[-1]]

        self.assertEqual(callbacks, [make_callback("back", "tok"), make_callback("close", "tok")])

    def test_resource_menu_can_page_candidates(self):
        candidates = [{"site_name": f"PT-{index}", "seeders": index, "title": "Show"} for index in range(1, 9)]
        menu = build_resource_menu("tok", candidates, page=1, page_size=5)
        callbacks = [button["callback_data"] for button in flatten_buttons(menu)]

        self.assertIn(make_callback("rpage1", "tok"), callbacks)
        self.assertIn(make_callback("pick6", "tok"), callbacks)

    def test_pending_menu_opens_each_show(self):
        menu = build_pending_menu(
            [
                ("tok1", {"title": "新进职员姜会长", "season": 1, "episodes": [{"episode": 11}]}),
                ("tok2", {"title": "关于我转生变成史莱姆这档事", "season": 4, "episodes": [{"episode": 13}]}),
            ]
        )
        callbacks = [button["callback_data"] for button in flatten_buttons(menu)]

        self.assertIn(make_callback("open", "tok1"), callbacks)
        self.assertIn(make_callback("open", "tok2"), callbacks)

    def test_ci_mode_menu_has_auto_manual_and_end(self):
        callbacks = [button["callback_data"] for button in flatten_buttons(build_ci_mode_menu("tok"))]

        self.assertEqual(callbacks, [make_callback("ci-auto", "tok"), make_callback("ci-manual", "tok"), make_callback("close", "tok")])

    def test_ci_manual_type_menu_has_movie_tv_back_and_end(self):
        callbacks = [button["callback_data"] for button in flatten_buttons(build_ci_manual_type_menu("tok"))]

        self.assertEqual(
            callbacks,
            [
                make_callback("ci-tv", "tok"),
                make_callback("ci-movie", "tok"),
                make_callback("ci-back", "tok"),
                make_callback("close", "tok"),
            ],
        )

    def test_ci_done_menu_has_retry_back_and_end(self):
        callbacks = [button["callback_data"] for button in flatten_buttons(build_ci_done_menu("tok"))]

        self.assertEqual(
            callbacks,
            [
                make_callback("ci-retry", "tok"),
                make_callback("ci-back", "tok"),
                make_callback("close", "tok"),
            ],
        )

    def test_identifier_fix_result_text_shows_added_rules_or_failure_reason(self):
        success_text = render_identifier_fix_result_text(
            {
                "success": True,
                "message": "ok",
                "data": {
                    "added": ["Foo => Bar {tmdbid=107371;type=tv;s=1}"],
                },
            }
        )
        failure_text = render_identifier_fix_result_text(
            {"success": False, "message": "AI unavailable", "reason": "ai_unavailable"}
        )

        self.assertIn("Foo => Bar", success_text)
        self.assertIn("AI unavailable", failure_text)

    def test_rule_menu_has_back_and_end_button(self):
        menu = build_rule_menu("tok", [{"text": "Add ADWeb"}])
        callbacks = [button["callback_data"] for button in menu[-1]]

        self.assertEqual(callbacks, [make_callback("back", "tok"), make_callback("close", "tok")])

    def test_rule_confirm_menu_has_confirm_and_back(self):
        callbacks = [button["callback_data"] for button in flatten_buttons(build_rule_confirm_menu("confirm", "main"))]

        self.assertEqual(
            callbacks,
            [
                make_callback("rule-confirm", "confirm"),
                make_callback("rule", "main"),
                make_callback("close", "main"),
            ],
        )

    def test_rule_done_menu_has_back_and_end(self):
        callbacks = [button["callback_data"] for button in flatten_buttons(build_rule_done_menu("main"))]

        self.assertEqual(callbacks, [make_callback("rule", "main"), make_callback("close", "main")])

    def test_rule_preview_text_asks_before_adding_rule(self):
        text = render_rule_preview_text(
            {
                "old_include": "(?=.*HHWeb|MWeb|ADWeb)(?=.*Viu|friDay)",
                "new_include": "(?=.*HHWeb|MWeb|ADWeb|cctc)(?=.*Viu|friDay|Baha)",
            },
            "Add cctc",
        )

        self.assertIn("(?=.*HHWeb|MWeb|ADWeb)(?=.*Viu|friDay)", text)
        self.assertIn("(?=.*HHWeb|MWeb|ADWeb|cctc)(?=.*Viu|friDay|Baha)", text)

    def test_rule_preview_text_supports_site_field(self):
        text = render_rule_preview_text(
            {
                "field": "sites",
                "old_site_names": ["3"],
                "new_site_names": ["3", "Spring"],
            },
            "添加PT站点：Spring",
        )

        self.assertIn("订阅站点", text)
        self.assertIn("Spring", text)

    def test_notification_text_lists_candidate_details(self):
        text = render_notification_text(
            {
                "title": "Princess",
                "season": 1,
                "episodes": [{"episode": 12, "air_date": "2026-06-25"}],
                "message": "blocked",
                "sites": ["13", "20"],
                "candidates": [
                    {
                        "site_name": "青蛙",
                        "title": "Monster Eater S01 2026 1080p Baha WEB-DL H.264 AAC-FROGWeb",
                        "seeders": 13,
                        "platforms": ["Baha"],
                        "release_groups": ["FROGWeb"],
                        "quality": "WEB-DL",
                        "resolution": "1080p",
                        "video_codec": "H264",
                        "volume_factor": "50%",
                    }
                ],
            }
        )

        self.assertIn("[青蛙]", text)
        self.assertIn("平台：Baha", text)
        self.assertIn("官组：FROGWeb", text)
        self.assertIn("WEB-DL / 1080p / H264", text)
        self.assertIn("优惠：50%", text)

    def test_notification_text_can_page_candidate_details(self):
        candidates = [
            {
                "site_name": f"站点{index}",
                "title": f"Show S01E{index:02d}",
                "seeders": index,
            }
            for index in range(1, 8)
        ]
        text = render_notification_text(
            {
                "title": "Show",
                "season": 1,
                "episodes": [{"episode": 7, "air_date": "2026-07-04"}],
                "message": "blocked",
                "candidates": candidates,
            },
            candidate_page=1,
        )

        self.assertIn("候选资源第 2/3 页", text)
        self.assertIn("4. [站点4]", text)
        self.assertNotIn("1. [站点1]", text)

    def test_notification_title_uses_chinese_plugin_name(self):
        self.assertEqual(
            SubscribePlus._notification_title({"title": "关于我转生变成史莱姆这档事"}),
            "订阅下载增强：关于我转生变成史莱姆这档事",
        )

    def test_notification_text_shows_subscription_site_progress(self):
        text = render_notification_text(
            {
                "title": "吞噬星空",
                "season": 1,
                "episodes": [{"episode": 230, "air_date": "2026-07-04"}],
                "message": "订阅站点暂无目标集，其他 PT 站点存在目标集资源",
                "sites": ["20", "27"],
                "subscription_site_progress": [
                    {"site_name": "憨憨", "latest_episode": 229, "target_episode": 230}
                ],
                "candidates": [
                    {
                        "site_name": "观众",
                        "title": "吞噬星空 S01E230 2026 2160p WEB-DL H265-HHWEB",
                        "episode": 230,
                        "seeders": 9,
                    }
                ],
            }
        )

        self.assertIn("订阅站点：", text)
        self.assertIn("憨憨：最新疑似 E229，未发现 E230", text)
        self.assertIn("其他站点候选：", text)
        self.assertIn("[观众]", text)

    def test_close_action_can_delete_original_message(self):
        class FakeChain:
            def __init__(self):
                self.calls = []

            def delete_message(self, channel, source, message_id, chat_id):
                self.calls.append((channel, source, message_id, chat_id))

        plugin = SubscribePlus()
        plugin.chain = FakeChain()

        deleted = plugin._delete_callback_message(
            {
                "channel": "telegram",
                "source": "bot",
                "original_message_id": 123,
                "original_chat_id": 456,
            }
        )

        self.assertTrue(deleted)
        self.assertEqual(plugin.chain.calls, [("telegram", "bot", 123, 456)])

    def test_close_callback_deletes_message_even_when_interaction_expired(self):
        class FakeStore:
            def __init__(self):
                self.deleted = []

            def load_interaction(self, _token):
                return None

            def delete_interaction(self, token):
                self.deleted.append(token)

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        deleted = []
        posts = []
        advanced = []
        plugin._delete_callback_message = lambda event_data: deleted.append(event_data) or True
        plugin._post_callback_message = lambda *args, **kwargs: posts.append(kwargs)
        plugin._notify_next_queued_show = lambda: advanced.append(True)

        plugin._handle_callback("[PLUGIN]SubscribePlus|close:missing", {"original_message_id": 1, "original_chat_id": 2})

        self.assertEqual(plugin._store.deleted, ["missing"])
        self.assertEqual(len(deleted), 1)
        self.assertEqual(posts, [])
        self.assertEqual(advanced, [True])

    def test_sp_menu_close_does_not_advance_notification_queue(self):
        class FakeStore:
            def __init__(self):
                self.deleted = []

            def delete_interaction(self, token):
                self.deleted.append(token)

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        deleted = []
        posts = []
        advanced = []
        plugin._delete_callback_message = lambda event_data: deleted.append(event_data) or True
        plugin._post_callback_message = lambda *args, **kwargs: posts.append(kwargs)
        plugin._notify_next_queued_show = lambda: advanced.append(True)

        plugin._handle_callback("[PLUGIN]SubscribePlus|close:spmenu", {"original_message_id": 1, "original_chat_id": 2})

        self.assertEqual(plugin._store.deleted, ["spmenu"])
        self.assertEqual(len(deleted), 1)
        self.assertEqual(posts, [])
        self.assertEqual(advanced, [])

    def test_candidate_page_callback_renders_next_page(self):
        class FakeStore:
            def load_interaction(self, _token):
                return {
                    "diagnosis": {
                        "title": "Show",
                        "season": 1,
                        "episodes": [{"episode": 7, "air_date": "2026-07-04"}],
                        "candidates": [
                            {"site_name": f"站点{index}", "title": f"Show S01E{index:02d}"}
                            for index in range(1, 8)
                        ],
                    }
                }

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        posts = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)

        plugin._handle_callback("[PLUGIN]SubscribePlus|cand2:tok", {})

        self.assertIn("候选资源第 2/3 页", posts[-1]["text"])
        self.assertIn("4. [站点4]", posts[-1]["text"])

    def test_sp_command_lists_scan_results(self):
        class FakeStore:
            def __init__(self):
                self.saved = {}

            def load_scan_results(self):
                return [
                    {"subscribe_id": 1, "title": "新进职员姜会长", "season": 1, "episodes": [{"episode": 11}]}
                ]

            def is_ignored(self, _key):
                return False

            def is_snoozed(self, _key):
                return False

            def save_interaction(self, token, state):
                self.saved[token] = state

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        posts = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)

        plugin._handle_sp_command_text("/sp", {})

        self.assertIn("待处理诊断", posts[-1]["title"])
        self.assertIn("新进职员姜会长", posts[-1]["text"])
        self.assertTrue(plugin._store.saved)

    def test_download_callback_starts_moviepilot_subscribe_search(self):
        class FakeStore:
            def load_interaction(self, _token):
                return {"diagnosis": {"subscribe_id": 12, "title": "One Piece"}}

            def delete_interaction(self, _token):
                pass

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        posts = []
        searched = []
        advanced = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)
        plugin._start_moviepilot_subscribe_search = lambda diagnosis: searched.append(diagnosis["subscribe_id"]) or {
            "success": True,
            "message": "started",
        }
        plugin._notify_next_queued_show = lambda: advanced.append(True)

        plugin._handle_callback("[PLUGIN]SubscribePlus|download:tok", {})

        self.assertEqual(searched, [12])
        self.assertIn("started", posts[-1]["text"])
        self.assertEqual(advanced, [True])

    def test_start_moviepilot_subscribe_search_uses_scheduler_job(self):
        calls = []

        class FakeScheduler:
            def start(self, job_id, **kwargs):
                calls.append((job_id, kwargs))

        restore = install_fake_scheduler(FakeScheduler)
        try:
            infos = []
            with patch.object(subscribeplus_module.logger, "info", side_effect=infos.append):
                result = SubscribePlus()._start_moviepilot_subscribe_search(
                    {"subscribe_id": 12, "title": "One Piece", "tmdbid": 37854, "season": 23}
                )
        finally:
            restore()

        self.assertTrue(result["success"])
        self.assertIn("已触发 MP 原生订阅搜索", result["message"])
        self.assertEqual(calls, [("subscribe_search", {"sid": 12, "state": None, "manual": True})])
        self.assertTrue(any("触发 MP 原生订阅搜索成功" in item for item in infos))
        self.assertTrue(any("剧名=One Piece" in item and "订阅ID=12" in item and "TMDB=37854" in item for item in infos))

    def test_candidate_download_logs_submitted_download_action(self):
        calls = []

        class FakeDownloadChain:
            def download_single(self, context, username):
                calls.append((context, username))

        plugin = SubscribePlus()
        plugin._download_contexts["c1"] = SimpleNamespace(name="context")
        posts = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)
        restore = install_fake_download_chain(FakeDownloadChain)
        try:
            infos = []
            with patch.object(subscribeplus_module.logger, "info", side_effect=infos.append):
                plugin._download_candidate(
                    {
                        "subscribe_id": 12,
                        "title": "One Piece",
                        "tmdbid": 37854,
                        "season": 23,
                        "episodes": [{"season": 23, "episode": 1156}],
                        "candidates": [
                            {
                                "candidate_id": "c1",
                                "title": "One.Piece.S23E1156.Baha-ADWeb",
                                "site_name": "春天",
                                "episode": 1156,
                            }
                        ],
                    },
                    0,
                    {},
                )
        finally:
            restore()

        self.assertEqual(calls, [(plugin._download_contexts["c1"], "SubscribePlus")])
        self.assertIn("已提交下载任务", posts[-1]["text"])
        self.assertTrue(any("提交候选资源下载成功" in item for item in infos))
        self.assertTrue(any("剧名=One Piece" in item and "站点=春天" in item and "E1156" in item for item in infos))

    def test_candidate_download_without_context_falls_back_to_subscribe_search(self):
        plugin = SubscribePlus()
        posts = []
        searched = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)
        plugin._start_moviepilot_subscribe_search = lambda diagnosis: searched.append(diagnosis["subscribe_id"]) or {
            "success": True,
            "message": "已触发 MP 原生订阅搜索：One Piece",
        }

        plugin._download_candidate(
            {
                "subscribe_id": 12,
                "title": "One Piece",
                "candidates": [{"candidate_id": "gone", "title": "One Piece S01E01"}],
            },
            0,
            {},
        )

        self.assertEqual(searched, [12])
        self.assertIn("已触发 MP 原生订阅搜索", posts[-1]["text"])

    def test_pt_scope_callback_replaces_interaction_with_plugin_search_result(self):
        class FakeStore:
            def __init__(self):
                self.saved = []

            def load_interaction(self, _token):
                return {
                    "diagnosis": {
                        "subscribe_id": 12,
                        "title": "One Piece",
                        "tmdbid": 37854,
                        "season": 23,
                        "category": "日番",
                        "episodes": [{"season": 23, "episode": 1156, "air_date": "2026-07-01"}],
                    }
                }

            def save_interaction(self, token, state):
                self.saved.append((token, state))

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        plugin._plugin_config.search_sites = ["13", "20"]
        posts = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)
        plugin._manual_pt_scope_diagnosis = lambda diagnosis: {
            **diagnosis,
            "reason": "rule_blocked",
            "message": "插件 PT 范围搜索结果：资源存在且识别正确，但被订阅包含规则拦截",
            "source": "plugin_pt_scope",
            "sites": ["13", "20"],
            "candidates": [{"title": "One.Piece.S23E1156.Baha-ADWeb", "site_name": "春天"}],
        }

        plugin._handle_callback("[PLUGIN]SubscribePlus|ptscope:tok", {})

        self.assertEqual(plugin._store.saved[0][0], "tok")
        self.assertEqual(plugin._store.saved[0][1]["diagnosis"]["source"], "plugin_pt_scope")
        self.assertEqual(plugin._store.saved[0][1]["diagnosis"]["sites"], ["13", "20"])
        self.assertIn("插件 PT 范围搜索结果", posts[-1]["text"])
        self.assertIn("PT范围搜索", [button["text"] for row in posts[-1]["buttons"] for button in row])

    def test_download_after_pt_scope_search_opens_candidate_picker(self):
        class FakeStore:
            def load_interaction(self, _token):
                return {
                    "diagnosis": {
                        "subscribe_id": 12,
                        "title": "One Piece",
                        "source": "plugin_pt_scope",
                        "candidates": [
                            {"candidate_id": "c1", "title": "One.Piece.S23E1156.Baha-ADWeb", "site_name": "春天", "seeders": 8}
                        ],
                    }
                }

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        posts = []
        searched = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)
        plugin._start_moviepilot_subscribe_search = lambda diagnosis: searched.append(diagnosis["subscribe_id"])

        plugin._handle_callback("[PLUGIN]SubscribePlus|download:tok", {})

        self.assertEqual(searched, [])
        self.assertIn("请选择要下载的候选资源", posts[-1]["text"])
        callbacks = [button["callback_data"] for row in posts[-1]["buttons"] for button in row]
        self.assertIn(make_callback("pick1", "tok"), callbacks)

    def test_snooze_3_days_saves_until_and_advances_queue(self):
        class FakeStore:
            def __init__(self):
                self.snoozed = []
                self.deleted = []

            def load_interaction(self, _token):
                return {
                    "diagnosis": {
                        "subscribe_id": 33,
                        "title": "One Piece",
                        "season": 23,
                        "episodes": [{"episode": 1156}],
                    }
                }

            def save_snooze(self, key, until):
                self.snoozed.append((key, until))

            def delete_interaction(self, token):
                self.deleted.append(token)

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        posts = []
        advanced = []
        plugin._post_callback_message = lambda _event_data, **kwargs: posts.append(kwargs)
        plugin._notify_next_queued_show = lambda: advanced.append(True)

        plugin._handle_callback("[PLUGIN]SubscribePlus|snooze3d:tok", {})

        key, until = plugin._store.snoozed[0]
        self.assertIn("33", key)
        self.assertGreater(datetime.fromisoformat(until), datetime.now() + timedelta(days=2, hours=23))
        self.assertIn("3", posts[-1]["text"])
        self.assertEqual(plugin._store.deleted, ["tok"])
        self.assertEqual(advanced, [True])


if __name__ == "__main__":
    unittest.main()
