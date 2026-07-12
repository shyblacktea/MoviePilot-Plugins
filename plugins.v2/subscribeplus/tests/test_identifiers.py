import unittest

from subscribeplus.identifiers import (
    build_exact_identifier_rule,
    build_identifier_lines,
    normalize_identifier_line,
    refresh_identifier_runtime_cache,
    validate_identifier_rule,
)


class IdentifierRulesTest(unittest.TestCase):
    def test_exact_identifier_rule_binds_title_to_tmdb_tv_episode(self):
        rule = build_exact_identifier_rule(
            "A.Will.Eternal.S01E08.2020.1080p.WEB-DL.ADWeb",
            {
                "name": "一念永恒",
                "year": "2020",
                "media_type": "tv",
                "tmdbid": 107371,
                "season": 1,
                "episode": 8,
            },
        )

        self.assertIn(" => ", rule)
        self.assertIn("一念永恒.2020{[tmdbid=107371;type=tv;s=1;e=8]}", rule)
        self.assertTrue(validate_identifier_rule(rule))

    def test_identifier_rule_normalization_keeps_required_operator_spaces(self):
        rule = normalize_identifier_line("  Foo\\.S01E01   =>   Bar{[tmdbid=1;type=tv;s=1;e=1]}  ")

        self.assertEqual(rule, "Foo\\.S01E01 => Bar{[tmdbid=1;type=tv;s=1;e=1]}")

    def test_identifier_lines_only_add_one_rule_without_comment(self):
        lines = build_identifier_lines(
            "A.Will.Eternal.S01E08.2020.1080p.WEB-DL.ADWeb",
            {
                "name": "一念永恒",
                "year": "2020",
                "media_type": "tv",
                "tmdbid": 107371,
                "season": 1,
                "episode": 8,
            },
            comment="订阅下载增强",
        )

        self.assertEqual(len(lines), 1)
        self.assertFalse(lines[0].startswith("#"))
        self.assertIn("=> 一念永恒.2020{[tmdbid=107371;type=tv;s=1;e=8]}", lines[0])

    def test_comment_only_is_not_a_valid_identifier_rule(self):
        self.assertFalse(validate_identifier_rule("# comment"))

    def test_refresh_identifier_runtime_cache_clears_moviepilot_parse_cache(self):
        calls = []

        class FakeMetainfo:
            @staticmethod
            def clear_rust_parse_options_cache():
                calls.append("rust")

        def fake_import(name):
            if name == "app.core.metainfo":
                return FakeMetainfo
            raise ImportError(name)

        refresh_identifier_runtime_cache(import_module=fake_import)

        self.assertEqual(calls, ["rust"])


if __name__ == "__main__":
    unittest.main()
