import sys
import types
import unittest
from pathlib import Path

from subscribeplus import SubscribePlus
from subscribeplus.storage import JsonStore


TEST_TMP_ROOT = Path.cwd() / ".codex_tmp_tests"


class IdentifierToolPlugin(SubscribePlus):
    def __init__(self, tmpdir: Path):
        self._store = JsonStore(tmpdir)
        self.appended = []
        self.ai_target = {
            "media_type": "tv",
            "tmdbid": 107371,
            "season": 1,
        }

    def _identify_target_by_ai(self, title):
        return dict(self.ai_target)

    def _load_tmdb_target_summary(self, target):
        return {"success": True, "name": "一念永恒", "year": "2020"}

    def _append_custom_identifiers(self, lines):
        self.appended.extend(lines)
        return {"added": list(lines), "total_count": len(lines)}

    def _recognize_identifier_title(self, title, target):
        return {
            "success": True,
            "message": "再次识别成功",
            "recognized_title": target.get("name"),
            "tmdbid": target.get("tmdbid"),
        }


class IdentifierApiTest(unittest.TestCase):
    def setUp(self):
        TEST_TMP_ROOT.mkdir(exist_ok=True)

    def test_manual_identifier_adds_one_rule_and_records_result(self):
        tmpdir = TEST_TMP_ROOT / "identifier_manual"
        tmpdir.mkdir(exist_ok=True)
        plugin = IdentifierToolPlugin(tmpdir)

        result = plugin._identifier_manual(
            {
                "title": "A.Will.Eternal.S01E08.2020.1080p.WEB-DL.ADWeb",
                "media_type": "tv",
                "tmdbid": 107371,
                "season": 1,
                "episode": 8,
            },
            source="vue",
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(plugin.appended), 1)
        self.assertFalse(plugin.appended[0].startswith("#"))
        self.assertIn("=> 一念永恒.2020{[tmdbid=107371;type=tv;s=1;e=8]}", plugin.appended[0])
        record = plugin._ensure_store().load_identifier_records()[0]
        self.assertEqual(record["mode"], "manual")
        self.assertEqual(record["source"], "vue")

    def test_auto_identifier_uses_ai_target_then_writes_one_rule(self):
        tmpdir = TEST_TMP_ROOT / "identifier_auto"
        tmpdir.mkdir(exist_ok=True)
        plugin = IdentifierToolPlugin(tmpdir)

        result = plugin._identifier_auto({"title": "A.Will.Eternal.S01E08.2020.1080p.WEB-DL.ADWeb"}, source="telegram")

        self.assertTrue(result["success"])
        self.assertEqual(len(plugin.appended), 1)
        self.assertIn("tmdbid=107371;type=tv;s=1", plugin.appended[0])
        record = plugin._ensure_store().load_identifier_records()[0]
        self.assertEqual(record["mode"], "auto")
        self.assertEqual(record["candidate_title"], "A.Will.Eternal.S01E08.2020.1080p.WEB-DL.ADWeb")

    def test_append_custom_identifiers_inserts_new_rule_at_top_and_clears_cache(self):
        calls = []

        class FakeSystemConfigOper:
            value = ["Old\\.Show => Old{[tmdbid=1;type=tv]}"]

            def get(self, key):
                return list(self.__class__.value)

            def set(self, key, value):
                self.__class__.value = list(value)

        def clear_rust_parse_options_cache():
            calls.append("clear")

        modules = {
            "app": types.ModuleType("app"),
            "app.db": types.ModuleType("app.db"),
            "app.db.systemconfig_oper": types.ModuleType("app.db.systemconfig_oper"),
            "app.core": types.ModuleType("app.core"),
            "app.core.metainfo": types.ModuleType("app.core.metainfo"),
        }
        modules["app.db.systemconfig_oper"].SystemConfigOper = FakeSystemConfigOper
        modules["app.core.metainfo"].clear_rust_parse_options_cache = clear_rust_parse_options_cache
        old_modules = {name: sys.modules.get(name) for name in modules}
        sys.modules.update(modules)
        self.addCleanup(lambda: self._restore_modules(old_modules, modules))

        plugin = SubscribePlus()
        result = plugin._append_custom_identifiers(
            [
                "# 注释不应写入",
                "New\\.Show => New{[tmdbid=2;type=tv]}",
                "Old\\.Show => Old{[tmdbid=1;type=tv]}",
            ]
        )

        self.assertEqual(result["added"], ["New\\.Show => New{[tmdbid=2;type=tv]}"])
        self.assertEqual(
            FakeSystemConfigOper.value,
            ["New\\.Show => New{[tmdbid=2;type=tv]}", "Old\\.Show => Old{[tmdbid=1;type=tv]}"],
        )
        self.assertEqual(calls, ["clear"])

    @staticmethod
    def _restore_modules(old_modules, new_modules):
        for name in new_modules:
            if old_modules[name] is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_modules[name]


if __name__ == "__main__":
    unittest.main()
