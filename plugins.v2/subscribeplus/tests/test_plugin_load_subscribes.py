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


if __name__ == "__main__":
    unittest.main()
