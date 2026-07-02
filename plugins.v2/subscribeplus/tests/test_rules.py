import unittest

from subscribeplus.rules import apply_include_preview, build_rule_suggestions, compile_include, merge_include


class RulesTest(unittest.TestCase):
    def test_rule_suggestions_extract_platform_keyword(self):
        candidates = [{"title": "Show S01E03 1080p Baha WEB-DL", "site": "baha"}]
        suggestions = build_rule_suggestions(candidates)

        self.assertIn({"kind": "platform", "value": "baha", "pattern": "(?i)baha"}, suggestions)

    def test_apply_include_preview_appends_old_and_new_record(self):
        preview = {"subscribe_id": 7, "old_include": "CR", "new_include": "CR|Baha", "source": "telegram"}
        record = apply_include_preview(preview, update_subscribe=lambda sid, data: {"id": sid, **data})

        self.assertEqual(record["old_value"], "CR")
        self.assertEqual(record["new_value"], "CR|Baha")

    def test_merge_include_deduplicates_patterns(self):
        self.assertEqual(merge_include("CR", "(?i)baha"), "CR|(?i)baha")
        self.assertEqual(merge_include("CR|(?i)baha", "(?i)baha"), "CR|(?i)baha")

    def test_compile_include_rejects_invalid_regex(self):
        with self.assertRaises(ValueError):
            compile_include("[")


if __name__ == "__main__":
    unittest.main()
