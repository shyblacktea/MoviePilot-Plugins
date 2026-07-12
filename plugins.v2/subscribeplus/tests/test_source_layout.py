import unittest
import re
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SourceLayoutTest(unittest.TestCase):
    def test_diagnosis_cards_are_after_record_sections_in_dom(self):
        source = (PLUGIN_ROOT / "src" / "components" / "Page.vue").read_text(encoding="utf-8")

        identifier_index = source.index("自定义识别词")
        rule_record_index = source.index("规则修改记录")
        result_card_index = source.index('class="rounded border mb-3 result-card"')

        self.assertLess(identifier_index, result_card_index)
        self.assertLess(rule_record_index, result_card_index)
        self.assertNotRegex(source, re.compile(r"\.scroll-content\s*\{[^}]*display:\s*flex", re.S))
        self.assertNotRegex(source, re.compile(r"\.result-card\s*\{[^}]*order\s*:", re.S))

    def test_notification_sender_has_single_definition(self):
        source = (PLUGIN_ROOT / "__init__.py").read_text(encoding="utf-8")

        self.assertEqual(source.count("def _notify_each_show"), 1)


if __name__ == "__main__":
    unittest.main()
