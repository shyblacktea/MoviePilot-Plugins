import sys
import types
import unittest
from types import SimpleNamespace

from subscribeplus import SubscribePlus


class PluginLoadSubscribesTest(unittest.TestCase):
    def test_load_subscribes_reads_all_states(self):
        class FakeSubscribeOper:
            calls = []

            def list(self, state=None):
                self.calls.append(state)
                if state is not None:
                    return [SimpleNamespace(state=state)]
                return [SimpleNamespace(state="R"), SimpleNamespace(state="P")]

        fake_app = types.ModuleType("app")
        fake_db = types.ModuleType("app.db")
        fake_module = types.ModuleType("app.db.subscribe_oper")
        fake_module.SubscribeOper = FakeSubscribeOper

        previous = {name: sys.modules.get(name) for name in ("app", "app.db", "app.db.subscribe_oper")}
        sys.modules["app"] = fake_app
        sys.modules["app.db"] = fake_db
        sys.modules["app.db.subscribe_oper"] = fake_module
        try:
            results = SubscribePlus()._load_subscribes()
        finally:
            for name, module in previous.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

        self.assertEqual(FakeSubscribeOper.calls, [None])
        self.assertEqual([item.state for item in results], ["R", "P"])

    def test_episode_download_check_accepts_zero_padded_transfer_season(self):
        class FakeMediaServerOper:
            def exists(self, **_kwargs):
                return None

        class FakeTransferHistoryOper:
            calls = []

            def get_by(self, **kwargs):
                self.calls.append(kwargs)
                if kwargs.get("season") == "S01" or kwargs.get("season") is None:
                    return [
                        SimpleNamespace(
                            tmdbid=299365,
                            seasons="S01",
                            episodes="E11",
                            status=True,
                        )
                    ]
                return []

        fake_app = types.ModuleType("app")
        fake_db = types.ModuleType("app.db")
        fake_media_module = types.ModuleType("app.db.mediaserver_oper")
        fake_transfer_module = types.ModuleType("app.db.transferhistory_oper")
        fake_media_module.MediaServerOper = FakeMediaServerOper
        fake_transfer_module.TransferHistoryOper = FakeTransferHistoryOper

        previous = {
            name: sys.modules.get(name)
            for name in (
                "app",
                "app.db",
                "app.db.mediaserver_oper",
                "app.db.transferhistory_oper",
            )
        }
        sys.modules["app"] = fake_app
        sys.modules["app.db"] = fake_db
        sys.modules["app.db.mediaserver_oper"] = fake_media_module
        sys.modules["app.db.transferhistory_oper"] = fake_transfer_module
        try:
            downloaded, evidence = SubscribePlus()._is_episode_downloaded(299365, 1, 11)
        finally:
            for name, module in previous.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

        self.assertTrue(downloaded)
        self.assertIn("整理历史", evidence)


if __name__ == "__main__":
    unittest.main()
