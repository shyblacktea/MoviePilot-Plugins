import unittest

from subscribeplus import SubscribePlus
from subscribeplus.telegram import (
    build_main_menu,
    build_resource_menu,
    build_rule_confirm_menu,
    build_rule_done_menu,
    build_rule_menu,
    make_callback,
    render_rule_preview_text,
)


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
        self.assertEqual(menu[-1][1]["text"], "结束")

    def test_rule_menu_has_back_and_end_button(self):
        menu = build_rule_menu("tok", [{"text": "添加官组：ADWeb"}])

        self.assertEqual(menu[-1][0]["text"], "返回")
        self.assertEqual(menu[-1][1]["text"], "结束")

    def test_rule_confirm_menu_has_confirm_and_back(self):
        menu = build_rule_confirm_menu("confirm", "main")

        self.assertEqual(menu[0][0]["text"], "确认添加")
        self.assertEqual(menu[1][0]["text"], "返回")
        self.assertEqual(menu[1][1]["text"], "结束")

    def test_rule_done_menu_has_back_and_end(self):
        menu = build_rule_done_menu("main")

        self.assertEqual(menu[0][0]["text"], "返回")
        self.assertEqual(menu[0][1]["text"], "结束")

    def test_rule_preview_text_asks_before_adding_rule(self):
        text = render_rule_preview_text(
            {
                "old_include": "(?=.*HHWeb|MWeb|ADWeb)(?=.*Viu|friDay)",
                "new_include": "(?=.*HHWeb|MWeb|ADWeb|cctc)(?=.*Viu|friDay|Baha)",
            },
            "添加官组：cctc",
        )

        self.assertIn("已选择：添加官组：cctc", text)
        self.assertIn("是否添加到订阅包含规则？", text)
        self.assertIn("添加前：(?=.*HHWeb|MWeb|ADWeb)(?=.*Viu|friDay)", text)
        self.assertIn("添加后：(?=.*HHWeb|MWeb|ADWeb|cctc)(?=.*Viu|friDay|Baha)", text)

    def test_close_action_can_delete_original_message(self):
        class FakeChain:
            def __init__(self):
                self.calls = []

            def delete_message(self, channel, source, message_id, chat_id):
                self.calls.append((channel, source, message_id, chat_id))

        plugin = SubscribePlus()
        plugin.chain = FakeChain()

        deleted = plugin._delete_callback_message(
            {
                "channel": "telegram",
                "source": "bot",
                "original_message_id": 123,
                "original_chat_id": 456,
            }
        )

        self.assertTrue(deleted)
        self.assertEqual(plugin.chain.calls, [("telegram", "bot", 123, 456)])


if __name__ == "__main__":
    unittest.main()
