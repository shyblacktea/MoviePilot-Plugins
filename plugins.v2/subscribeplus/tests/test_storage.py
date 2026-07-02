import unittest
from datetime import datetime, timedelta
from pathlib import Path

from subscribeplus.storage import JsonStore


TEST_TMP_ROOT = Path.cwd() / ".codex_tmp_tests"


class JsonStoreTest(unittest.TestCase):
    def test_store_keeps_recent_rule_records(self):
        TEST_TMP_ROOT.mkdir(exist_ok=True)
        tmpdir = TEST_TMP_ROOT / "storage_rules"
        tmpdir.mkdir(exist_ok=True)
        records_file = tmpdir / "rule_records.json"
        if records_file.exists():
            records_file.unlink()
        store = JsonStore(tmpdir, max_rule_records=2)
        store.append_rule_record({"id": "1"})
        store.append_rule_record({"id": "2"})
        store.append_rule_record({"id": "3"})

        self.assertEqual([item["id"] for item in store.load_rule_records()], ["3", "2"])

    def test_store_expires_interaction_tokens(self):
        TEST_TMP_ROOT.mkdir(exist_ok=True)
        tmpdir = TEST_TMP_ROOT / "storage_interactions"
        tmpdir.mkdir(exist_ok=True)
        interactions_file = tmpdir / "interactions.json"
        if interactions_file.exists():
            interactions_file.unlink()
        store = JsonStore(tmpdir)
        expired = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
        fresh = (datetime.now() + timedelta(hours=1)).isoformat(timespec="seconds")
        store.save_interaction("old", {"expires_at": expired})
        store.save_interaction("fresh", {"expires_at": fresh})

        self.assertIsNone(store.load_interaction("old"))
        self.assertEqual(store.load_interaction("fresh")["expires_at"], fresh)

    def test_clear_scan_results_removes_results_and_meta(self):
        TEST_TMP_ROOT.mkdir(exist_ok=True)
        tmpdir = TEST_TMP_ROOT / "storage_clear"
        tmpdir.mkdir(exist_ok=True)
        store = JsonStore(tmpdir)
        store.save_scan_results([{"title": "Show"}])

        store.clear_scan_results()

        self.assertEqual(store.load_scan_results(), [])
        self.assertEqual(store.load_scan_meta(), {})


if __name__ == "__main__":
    unittest.main()
