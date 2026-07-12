import unittest

from types import SimpleNamespace

from subscribeplus.rules import (
    apply_include_preview,
    apply_rule_preview,
    build_include_preview,
    build_rule_preview,
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

    def test_numeric_site_id_does_not_create_rule_suggestion(self):
        candidates = [{"title": "Show S04E12 1080p CR WEB-DL H264-HHWEB", "site": "20", "site_name": "憨憨"}]
        suggestions = build_rule_suggestions(candidates)

        self.assertNotIn("20", {item["pattern"] for item in suggestions})
        self.assertIn("添加平台：CR", {item["text"] for item in suggestions})
        self.assertIn("添加官组：HHWeb", {item["text"] for item in suggestions})

    def test_numeric_site_id_creates_site_field_suggestion(self):
        candidates = [{"title": "Show S04E12 1080p WEB-DL", "site": "20", "site_name": "Spring"}]
        suggestions = build_rule_suggestions(candidates)

        site_suggestions = [item for item in suggestions if item["kind"] == "site"]
        self.assertEqual(site_suggestions[0]["value"], "20")
        self.assertEqual(site_suggestions[0]["text"], "添加PT站点：Spring")
        self.assertIn('"site_id": "20"', site_suggestions[0]["pattern"])

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

    def test_include_preview_rejects_numeric_site_id_pattern(self):
        subscribe = SimpleNamespace(
            id=7,
            include=".*(LINETV|Crunchyroll|\\bCR\\b).*(HHWEB|ADWeb)",
        )

        with self.assertRaises(ValueError):
            build_include_preview(subscribe, "20", source="vue")

    def test_site_preview_appends_subscribe_sites(self):
        subscribe = SimpleNamespace(id=7, include="", sites=[3])

        preview = build_rule_preview(subscribe, '{"site_id": "20", "site_name": "Spring"}', source="vue")

        self.assertEqual(preview["field"], "sites")
        self.assertEqual(preview["old_sites"], [3])
        self.assertEqual(preview["new_sites"], [3, 20])
        self.assertEqual(preview["new_site_names"], ["3", "Spring"])

    def test_apply_include_preview_appends_old_and_new_record(self):
        preview = {"subscribe_id": 7, "old_include": "CR", "new_include": "CR|Baha", "source": "telegram"}
        record = apply_include_preview(preview, update_subscribe=lambda sid, data: {"id": sid, **data})

        self.assertEqual(record["old_value"], "CR")
        self.assertEqual(record["new_value"], "CR|Baha")

    def test_apply_rule_preview_updates_subscribe_sites(self):
        preview = {
            "subscribe_id": 7,
            "field": "sites",
            "old_sites": [3],
            "new_sites": [3, 20],
            "old_site_names": ["3"],
            "new_site_names": ["3", "Spring"],
            "source": "vue",
        }
        updates = []

        record = apply_rule_preview(preview, update_subscribe=lambda sid, data: updates.append((sid, data)) or {})

        self.assertEqual(updates, [(7, {"sites": [3, 20]})])
        self.assertEqual(record["field"], "sites")
        self.assertEqual(record["new_value"], "3, Spring")

    def test_merge_include_deduplicates_patterns(self):
        self.assertEqual(merge_include("CR", "(?i)baha"), "CR|(?i)baha")
        self.assertEqual(merge_include("CR|(?i)baha", "(?i)baha"), "CR|(?i)baha")

    def test_compile_include_rejects_invalid_regex(self):
        with self.assertRaises(ValueError):
            compile_include("[")


if __name__ == "__main__":
    unittest.main()
