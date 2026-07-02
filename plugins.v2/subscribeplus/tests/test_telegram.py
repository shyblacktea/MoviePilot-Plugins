import unittest

from subscribeplus.telegram import build_main_menu, build_resource_menu, build_rule_confirm_menu, make_callback


class TelegramTest(unittest.TestCase):
    def test_callback_uses_short_token_and_plugin_prefix(self):
        callback = make_callback("download", "abc123")

        self.assertEqual(callback, "[PLUGIN]SubscribePlus|download:abc123")
        self.assertLessEqual(len(callback.encode("utf-8")), 64)

    def test_each_show_gets_own_token(self):
        first = build_main_menu(token="show1", allow_rule_update=True)
        second = build_main_menu(token="show2", allow_rule_update=True)

        self.assertNotEqual(first, second)

    def test_resource_menu_has_back_button(self):
        menu = build_resource_menu("tok", [{"site_name": "PT-A", "seeders": 10, "title": "Show"}])

        self.assertEqual(menu[-1][0]["text"], "返回")

    def test_rule_confirm_menu_has_confirm_and_back(self):
        menu = build_rule_confirm_menu("confirm", "main")

        self.assertEqual(menu[0][0]["text"], "确认修改")
        self.assertEqual(menu[1][0]["text"], "返回")


if __name__ == "__main__":
    unittest.main()
