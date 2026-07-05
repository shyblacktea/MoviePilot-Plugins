import unittest
import types
from types import SimpleNamespace
from unittest.mock import patch

import subscribeplus as subscribeplus_module
from subscribeplus.models import PluginConfig
from subscribeplus import SubscribePlus
from subscribeplus.season_cleanup import (
    CLEANUP_OFF,
    CLEANUP_RECORD,
    CLEANUP_SOURCE,
    build_cleanup_plan,
    normalize_cleanup_mode,
)


def history(**kwargs):
    defaults = {
        "id": 1,
        "tmdbid": 301944,
        "type": "电视剧",
        "seasons": "S01",
        "episodes": "E01",
        "download_hash": "old-hash",
        "torrent_name": "Marriage Toxin S01E01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        "src": "/downloads/Marriage.Toxin.S01E01.mkv",
        "src_fileitem": {"path": "/downloads/Marriage.Toxin.S01E01.mkv"},
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def fake_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


class SeasonPackCleanupTest(unittest.TestCase):
    def test_config_normalizes_cleanup_mode(self):
        self.assertEqual(PluginConfig.from_dict({}).season_pack_cleanup, CLEANUP_OFF)
        self.assertFalse(PluginConfig.from_dict({}).season_pack_full_download)
        self.assertTrue(PluginConfig.from_dict({"season_pack_full_download": True}).season_pack_full_download)
        self.assertEqual(
            PluginConfig.from_dict({"season_pack_cleanup": CLEANUP_SOURCE}).season_pack_cleanup,
            CLEANUP_SOURCE,
        )
        self.assertEqual(
            PluginConfig.from_dict({"season_pack_cleanup": "unknown"}).season_pack_cleanup,
            CLEANUP_OFF,
        )

    def test_normalize_cleanup_mode_accepts_aliases(self):
        self.assertEqual(normalize_cleanup_mode("record"), CLEANUP_RECORD)
        self.assertEqual(normalize_cleanup_mode("source"), CLEANUP_SOURCE)
        self.assertEqual(normalize_cleanup_mode(True), CLEANUP_SOURCE)
        self.assertEqual(normalize_cleanup_mode(False), CLEANUP_OFF)

    def test_final_episode_from_season_pack_selects_old_split_histories(self):
        current = history(
            id=99,
            episodes="E13",
            download_hash="season-pack",
            torrent_name="Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        )
        histories = [
            history(id=10, episodes="E10", download_hash="old-10"),
            history(id=11, episodes="E11", download_hash="old-11"),
            history(id=12, episodes="E12", download_hash="old-12"),
            current,
            history(id=1, episodes="E01", download_hash="season-pack"),
            history(id=20, tmdbid=123, episodes="E01", download_hash="other"),
        ]

        plan = build_cleanup_plan(
            current=current,
            histories=histories,
            total_episode=13,
            mode=CLEANUP_SOURCE,
        )

        self.assertTrue(plan.should_cleanup)
        self.assertTrue(plan.delete_source)
        self.assertEqual([item.id for item in plan.histories], [10, 11, 12])
        self.assertEqual(plan.episode_numbers, [10, 11, 12])

    def test_final_episode_uses_attached_download_torrent_name(self):
        current = history(
            id=99,
            episodes="E13",
            download_hash="season-pack",
            torrent_name="",
            src="/downloads/Marriage Toxin S01/Marriage Toxin S01E13.mkv",
        )
        setattr(current, "_subscribeplus_torrent_name", "Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb")

        plan = build_cleanup_plan(
            current=current,
            histories=[history(id=12, episodes="E12", download_hash="old-12"), current],
            total_episode=13,
            mode=CLEANUP_SOURCE,
        )

        self.assertTrue(plan.should_cleanup)
        self.assertEqual([item.id for item in plan.histories], [12])

    def test_single_episode_release_does_not_cleanup(self):
        current = history(
            id=99,
            episodes="E13",
            download_hash="single",
            torrent_name="Marriage Toxin S01E13 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        )

        plan = build_cleanup_plan(
            current=current,
            histories=[history(id=12, episodes="E12"), current],
            total_episode=13,
            mode=CLEANUP_SOURCE,
        )

        self.assertFalse(plan.should_cleanup)
        self.assertIn("not season pack", plan.reason)

    def test_non_final_episode_does_not_cleanup(self):
        current = history(
            id=99,
            episodes="E12",
            download_hash="season-pack",
            torrent_name="Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        )

        plan = build_cleanup_plan(
            current=current,
            histories=[history(id=11, episodes="E11"), current],
            total_episode=13,
            mode=CLEANUP_SOURCE,
        )

        self.assertFalse(plan.should_cleanup)
        self.assertIn("not finale", plan.reason)

    def test_incomplete_subscribe_final_episode_does_not_cleanup(self):
        # 回归：未完结剧集（11/12），种子名是裸 S01 单集，恰好补到 TMDB 当前最后一集，
        # 不应被误判为完结整季包。
        current = history(
            id=99,
            episodes="E11",
            download_hash="single-e11",
            torrent_name="Reborn.Rookie.S01.2026.1080p.FriDay.WEB-DL.H.264.AAC2.0-HHWEB",
        )

        plan = build_cleanup_plan(
            current=current,
            histories=[history(id=10, episodes="E10"), current],
            total_episode=11,
            mode=CLEANUP_SOURCE,
            subscribe_completed=False,
        )

        self.assertFalse(plan.should_cleanup)
        self.assertIn("subscribe not completed", plan.reason)

    def test_single_episode_torrent_name_with_dot_separator_not_season_pack(self):
        # 回归：点分隔的单集种子名不应被判为整季包。
        current = history(
            id=99,
            episodes="E13",
            download_hash="single",
            torrent_name="Reborn.Rookie.S01.E13.2026.1080p.HHWEB",
        )

        plan = build_cleanup_plan(
            current=current,
            histories=[history(id=12, episodes="E12"), current],
            total_episode=13,
            mode=CLEANUP_SOURCE,
            subscribe_completed=True,
        )

        self.assertFalse(plan.should_cleanup)
        self.assertIn("not season pack", plan.reason)

    def test_full_download_skips_single_file_torrent(self):
        # 回归：单文件种子（单集）不应被 qB 全选重下。
        plugin = SubscribePlus()
        calls = []

        class FakeQBittorrent:
            def get_files(self, torrent_hash):
                calls.append(("get_files", torrent_hash))
                return [SimpleNamespace(index=0, name="Reborn.Rookie.S01E11.mkv")]

            def set_files(self, torrent_hash, file_ids, priority):
                calls.append(("set_files", torrent_hash, file_ids, priority))

            def start_torrents(self, ids):
                calls.append(("start_torrents", ids))

        class FakeDownloaderHelper:
            def get_service(self, name=None, type_filter=None):
                calls.append(("get_service", name, type_filter))
                return SimpleNamespace(instance=FakeQBittorrent())

        fake_modules = {
            "app": fake_module("app"),
            "app.helper": fake_module("app.helper"),
            "app.helper.downloader": fake_module("app.helper.downloader", DownloaderHelper=FakeDownloaderHelper),
        }

        with patch.dict("sys.modules", fake_modules):
            result = plugin._ensure_season_pack_full_download(
                history(download_hash="single-e11", downloader="qb-main"),
                {"download_hash": "single-e11", "downloader": "qb-main"},
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["file_count"], 1)
        self.assertIn("single-file", result["reason"])
        # 不应调用 set_files / start_torrents
        self.assertNotIn(("set_files", "single-e11", "0", 1), calls)
        self.assertFalse(any(c[0] == "set_files" for c in calls))
        self.assertFalse(any(c[0] == "start_torrents" for c in calls))
        plugin = SubscribePlus()
        plugin._plugin_config = PluginConfig(season_pack_cleanup=CLEANUP_SOURCE)
        current = history(
            id=99,
            episodes="E13",
            download_hash="season-pack",
            torrent_name="Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        )
        old = history(id=12, episodes="E12", download_hash="old-12")
        calls = []

        plugin._get_transfer_history_for_cleanup = lambda history_id: current if history_id == 99 else None
        plugin._resolve_total_episode_for_cleanup = lambda _history, _event_data: 13
        plugin._resolve_subscribe_completed_for_cleanup = lambda _history, _event_data, _total: True
        plugin._load_transfer_histories_for_cleanup = lambda _history: [old, current]
        plugin._delete_transfer_history_for_cleanup = lambda item, delete_source: calls.append((item.id, delete_source)) or True
        plugin._notify_season_cleanup = lambda *_args, **_kwargs: None

        plugin._handle_transfer_complete_cleanup(SimpleNamespace(event_data={"transfer_history_id": 99}))

        self.assertEqual(calls, [(12, True)])

    def test_transfer_complete_cleanup_off_mode_does_nothing(self):
        plugin = SubscribePlus()
        plugin._plugin_config = PluginConfig(season_pack_cleanup=CLEANUP_OFF)
        calls = []
        plugin._get_transfer_history_for_cleanup = lambda _history_id: calls.append("loaded")

        plugin._handle_transfer_complete_cleanup(SimpleNamespace(event_data={"transfer_history_id": 99}))

        self.assertEqual(calls, [])

    def test_transfer_complete_full_download_runs_when_cleanup_off(self):
        plugin = SubscribePlus()
        plugin._plugin_config = PluginConfig(
            season_pack_cleanup=CLEANUP_OFF,
            season_pack_full_download=True,
        )
        current = history(
            id=99,
            episodes="E13",
            download_hash="season-pack",
            torrent_name="Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        )
        calls = []
        notifications = []

        plugin._get_transfer_history_for_cleanup = lambda history_id: current if history_id == 99 else None
        plugin._resolve_total_episode_for_cleanup = lambda _history, _event_data: 13
        plugin._resolve_subscribe_completed_for_cleanup = lambda _history, _event_data, _total: True
        plugin._load_transfer_histories_for_cleanup = lambda _history: []
        plugin._ensure_season_pack_full_download = lambda item, event_data: calls.append(
            (item.id, event_data.get("download_hash"))
        ) or {"ok": True, "file_count": 13}
        plugin._delete_transfer_history_for_cleanup = lambda *_args, **_kwargs: calls.append("delete")
        plugin._notify_season_cleanup = lambda *args, **kwargs: notifications.append((args, kwargs))

        plugin._handle_transfer_complete_cleanup(
            SimpleNamespace(event_data={"transfer_history_id": 99, "download_hash": "season-pack"})
        )

        self.assertEqual(calls, [(99, "season-pack")])
        self.assertEqual(len(notifications), 1)

    def test_full_download_selects_all_qbittorrent_files(self):
        plugin = SubscribePlus()
        calls = []

        class FakeQBittorrent:
            def get_files(self, torrent_hash):
                calls.append(("get_files", torrent_hash))
                return [
                    SimpleNamespace(index=0, name="Marriage Toxin S01E01.mkv"),
                    {"index": 1, "name": "Marriage Toxin S01E02.mkv"},
                    SimpleNamespace(name="Marriage Toxin S01E03.mkv"),
                ]

            def set_files(self, torrent_hash, file_ids, priority):
                calls.append(("set_files", torrent_hash, file_ids, priority))

            def start_torrents(self, ids):
                calls.append(("start_torrents", ids))

        class FakeDownloaderHelper:
            def get_service(self, name=None, type_filter=None):
                calls.append(("get_service", name, type_filter))
                return SimpleNamespace(instance=FakeQBittorrent())

        fake_modules = {
            "app": fake_module("app"),
            "app.helper": fake_module("app.helper"),
            "app.helper.downloader": fake_module("app.helper.downloader", DownloaderHelper=FakeDownloaderHelper),
        }

        with patch.dict("sys.modules", fake_modules):
            result = plugin._ensure_season_pack_full_download(
                history(download_hash="season-pack", downloader="qb-main"),
                {"download_hash": "season-pack", "downloader": "qb-main"},
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["file_count"], 3)
        self.assertEqual(
            calls,
            [
                ("get_service", "qb-main", "qbittorrent"),
                ("get_files", "season-pack"),
                ("set_files", "season-pack", "0|1|2", 1),
                ("start_torrents", "season-pack"),
            ],
        )

    def test_delete_transfer_history_uses_moviepilot_model_delete(self):
        plugin = SubscribePlus()
        calls = []

        class FakeTransferHistoryOper:
            def __init__(self):
                self._db = "db-session"

        class FakeTransferHistory:
            @classmethod
            def delete(cls, db, history_id):
                calls.append(("delete_history", db, history_id))

        fake_modules = {
            "app": fake_module("app", schemas=fake_module("app.schemas", FileItem=lambda **kwargs: SimpleNamespace(**kwargs))),
            "app.schemas": fake_module("app.schemas", FileItem=lambda **kwargs: SimpleNamespace(**kwargs)),
            "app.chain": fake_module("app.chain"),
            "app.chain.storage": fake_module("app.chain.storage", StorageChain=lambda: SimpleNamespace(delete_media_file=lambda _item: True)),
            "app.db": fake_module("app.db"),
            "app.db.models": fake_module("app.db.models"),
            "app.db.models.downloadhistory": fake_module(
                "app.db.models.downloadhistory",
                DownloadFiles=SimpleNamespace(delete_by_fullpath=lambda _db, _path: None),
            ),
            "app.db.models.transferhistory": fake_module("app.db.models.transferhistory", TransferHistory=FakeTransferHistory),
            "app.db.transferhistory_oper": fake_module(
                "app.db.transferhistory_oper",
                TransferHistoryOper=FakeTransferHistoryOper,
            ),
        }

        with patch.dict("sys.modules", fake_modules):
            with patch.object(subscribeplus_module, "eventmanager", None):
                self.assertTrue(plugin._delete_transfer_history_for_cleanup(history(id=12), delete_source=False))

        self.assertEqual(calls, [("delete_history", "db-session", 12)])

    def test_delete_transfer_history_with_source_uses_moviepilot_source_cleanup(self):
        plugin = SubscribePlus()
        calls = []

        class FakeTransferHistoryOper:
            def __init__(self):
                self._db = "db-session"

        class FakeTransferHistory:
            @classmethod
            def delete(cls, db, history_id):
                calls.append(("delete_history", db, history_id))

        class FakeStorageChain:
            def delete_media_file(self, fileitem):
                calls.append(("delete_source", fileitem.path))
                return True

        class FakeDownloadFiles:
            @classmethod
            def delete_by_fullpath(cls, db, fullpath):
                calls.append(("delete_download_file", db, fullpath))

        fake_modules = {
            "app": fake_module("app", schemas=fake_module("app.schemas", FileItem=lambda **kwargs: SimpleNamespace(**kwargs))),
            "app.schemas": fake_module("app.schemas", FileItem=lambda **kwargs: SimpleNamespace(**kwargs)),
            "app.chain": fake_module("app.chain"),
            "app.chain.storage": fake_module("app.chain.storage", StorageChain=FakeStorageChain),
            "app.db": fake_module("app.db"),
            "app.db.models": fake_module("app.db.models"),
            "app.db.models.downloadhistory": fake_module(
                "app.db.models.downloadhistory",
                DownloadFiles=FakeDownloadFiles,
            ),
            "app.db.models.transferhistory": fake_module("app.db.models.transferhistory", TransferHistory=FakeTransferHistory),
            "app.db.transferhistory_oper": fake_module(
                "app.db.transferhistory_oper",
                TransferHistoryOper=FakeTransferHistoryOper,
            ),
        }
        fake_eventmanager = SimpleNamespace(
            send_event=lambda event_type, data: calls.append(("event", event_type, data))
        )
        old_event_type = getattr(subscribeplus_module.EventType, "DownloadFileDeleted", None)
        setattr(subscribeplus_module.EventType, "DownloadFileDeleted", "download.file.deleted")
        try:
            with patch.dict("sys.modules", fake_modules):
                with patch.object(subscribeplus_module, "eventmanager", fake_eventmanager):
                    self.assertTrue(plugin._delete_transfer_history_for_cleanup(history(id=12), delete_source=True))
        finally:
            if old_event_type is None:
                delattr(subscribeplus_module.EventType, "DownloadFileDeleted")
            else:
                setattr(subscribeplus_module.EventType, "DownloadFileDeleted", old_event_type)

        self.assertEqual(
            calls,
            [
                ("delete_source", "/downloads/Marriage.Toxin.S01E01.mkv"),
                ("delete_download_file", "db-session", "/downloads/Marriage.Toxin.S01E01.mkv"),
                ("event", "download.file.deleted", {"src": "/downloads/Marriage.Toxin.S01E01.mkv", "hash": "old-hash"}),
                ("delete_history", "db-session", 12),
            ],
        )

    def test_attach_cleanup_torrent_name_reads_download_history(self):
        plugin = SubscribePlus()
        current = history(id=99, torrent_name="", download_hash="season-pack")
        calls = []

        class FakeTransferHistoryOper:
            def __init__(self):
                self._db = "db-session"

        class FakeDownloadHistory:
            @classmethod
            def get_by_hash(cls, db, download_hash):
                calls.append((db, download_hash))
                return SimpleNamespace(torrent_name="Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb")

        fake_modules = {
            "app": fake_module("app"),
            "app.db": fake_module("app.db"),
            "app.db.models": fake_module("app.db.models"),
            "app.db.models.downloadhistory": fake_module("app.db.models.downloadhistory", DownloadHistory=FakeDownloadHistory),
            "app.db.transferhistory_oper": fake_module(
                "app.db.transferhistory_oper",
                TransferHistoryOper=FakeTransferHistoryOper,
            ),
        }

        with patch.dict("sys.modules", fake_modules):
            plugin._attach_cleanup_torrent_name(current, {})

        self.assertEqual(calls, [("db-session", "season-pack")])
        self.assertEqual(
            getattr(current, "_subscribeplus_torrent_name"),
            "Marriage Toxin S01 2026 1080p CR WEB-DL x264 AAC-Nest@ADWeb",
        )


if __name__ == "__main__":
    unittest.main()
