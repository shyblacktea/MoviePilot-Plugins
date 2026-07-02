import unittest

from types import SimpleNamespace

from subscribeplus.rules import (
    apply_include_preview,
    build_include_preview,
    build_rule_suggestions,
    compile_include,
    extract_release_groups_from_words,
    merge_include,
)


class RulesTest(unittest.TestCase):
    def test_rule_suggestions_extract_release_group_and_platform_keyword(self):
        candidates = [{"title": "Show S01E03 1080p Baha WEB-DL", "site": "cctc", "site_name": "春天"}]
        suggestions = build_rule_suggestions(candidates, release_groups=["cctc"])

        self.assertIn(
            {
                "kind": "release_group",
                "value": "cctc",
                "text": "添加官组：cctc",
                "pattern": '{"release_group": "cctc"}',
            },
            suggestions,
        )
        self.assertIn(
            {
                "kind": "platform",
                "value": "Baha",
                "text": "添加平台：Baha",
                "pattern": '{"platform": "Baha"}',
            },
            suggestions,
        )
        self.assertNotIn("release_group_platform", {item["kind"] for item in suggestions})

    def test_rule_suggestions_read_custom_release_group_words(self):
        candidates = [{"title": "Show S01E03 1080p Baha WEB-DL MoonWEB", "site": "unknown", "site_name": "未知站"}]
        suggestions = build_rule_suggestions(candidates, release_groups=["MoonWEB"])

        self.assertIn(
            {
                "kind": "release_group",
                "value": "MoonWEB",
                "text": "添加官组：MoonWEB",
                "pattern": '{"release_group": "MoonWEB"}',
            },
            suggestions,
        )

    def test_bluray_release_group_title_does_not_create_platform_suggestion(self):
        candidates = [
            {
                "title": "Alya.Sometimes.Hides.Her.Feelings.in.Russian.S01E01.2024.1080p.BluRay.x265.10bit.AVC.FLAC.2.0-ADE.mkv",
                "site": "unknown",
            }
        ]
        suggestions = build_rule_suggestions(candidates, release_groups=["ADE"])

        self.assertIn(
            {
                "kind": "release_group",
                "value": "ADE",
                "text": "添加官组：ADE",
                "pattern": '{"release_group": "ADE"}',
            },
            suggestions,
        )
        self.assertNotIn("platform", {item["kind"] for item in suggestions})

    def test_extract_release_groups_from_custom_words(self):
        groups = extract_release_groups_from_words(
            [
                "#某番【MoonWEB】",
                "Show.S01E(?=.*SkyWEB) => Show.S01E",
                "StarWEB",
            ]
        )

        self.assertEqual(groups, ["MoonWEB", "SkyWEB", "StarWEB"])

    def test_include_preview_adds_release_group_and_platform_to_lookahead_groups(self):
        subscribe = SimpleNamespace(
            id=7,
            include="(?=.*HHWeb|MWeb|ADWeb)(?=.*Viu|friDay)",
        )

        preview = build_include_preview(subscribe, '{"release_group": "cctc", "platform": "Baha"}', source="telegram")

        self.assertEqual(
            preview["new_include"],
            "(?=.*HHWeb|MWeb|ADWeb|cctc)(?=.*Viu|friDay|Baha)",
        )

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
