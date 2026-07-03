import unittest

from subscribeplus import SubscribePlus
from subscribeplus.telegram import (
    build_ci_done_menu,
    build_ci_manual_type_menu,
    build_ci_mode_menu,
    build_main_menu,
    build_resource_menu,
    build_rule_confirm_menu,
    build_rule_done_menu,
    build_rule_menu,
    make_callback,
    render_identifier_fix_result_text,
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

    def test_ci_command_is_registered(self):
        commands = SubscribePlus.get_command()
        command = next(item for item in commands if item["cmd"] == "/ci")

        self.assertEqual(command["data"]["action"], "subscribeplus_ci")
        self.assertEqual(command["desc"], "自定义识别词修正")

    def test_resource_menu_has_back_button(self):
        menu = build_resource_menu("tok", [{"site_name": "PT-A", "seeders": 10, "title": "Show"}])

        self.assertEqual(menu[-1][0]["text"], "返回")
        self.assertEqual(menu[-1][1]["text"], "结束")

    def test_ci_mode_menu_has_auto_manual_and_end(self):
        menu = build_ci_mode_menu("tok")

        texts = [button["text"] for row in menu for button in row]
        self.assertEqual(texts, ["自动处理", "手动处理", "结束"])

    def test_ci_manual_type_menu_has_movie_tv_back_and_end(self):
        menu = build_ci_manual_type_menu("tok")

        texts = [button["text"] for row in menu for button in row]
        self.assertEqual(texts, ["TV", "Movie", "返回", "结束"])

    def test_ci_done_menu_has_retry_back_and_end(self):
        menu = build_ci_done_menu("tok")

        texts = [button["text"] for row in menu for button in row]
        self.assertEqual(texts, ["再次识别", "返回", "结束"])

    def test_identifier_fix_result_text_shows_added_rules_or_failure_reason(self):
        success_text = render_identifier_fix_result_text(
            {
                "success": True,
                "message": "已识别并写入自定义识别词",
                "data": {
                    "added": ["#一念永恒【订阅下载增强】", "Foo => 一念永恒{[tmdbid=107371;type=tv;s=1]}"],
                },
            }
        )
        failure_text = render_identifier_fix_result_text(
            {"success": False, "message": "AI 未配置或调用失败", "reason": "ai_unavailable"}
        )

        self.assertIn("已写入识别词", success_text)
        self.assertIn("Foo => 一念永恒", success_text)
        self.assertIn("失败原因：AI 未配置或调用失败", failure_text)

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

    def test_close_callback_deletes_message_even_when_interaction_expired(self):
        class FakeStore:
            def __init__(self):
                self.deleted = []

            def load_interaction(self, _token):
                return None

            def delete_interaction(self, token):
                self.deleted.append(token)

        plugin = SubscribePlus()
        plugin._store = FakeStore()
        deleted = []
        posts = []
        plugin._delete_callback_message = lambda event_data: deleted.append(event_data) or True
        plugin._post_callback_message = lambda *args, **kwargs: posts.append(kwargs)

        plugin._handle_callback("[PLUGIN]SubscribePlus|close:missing", {"original_message_id": 1, "original_chat_id": 2})

        self.assertEqual(plugin._store.deleted, ["missing"])
        self.assertEqual(len(deleted), 1)
        self.assertEqual(posts, [])


if __name__ == "__main__":
    unittest.main()
