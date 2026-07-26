import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class BackgroundProgressUiTest(unittest.TestCase):
    def test_config_owns_background_submission_and_progress_polling(self):
        source = (PLUGIN_ROOT / "src/components/Config.vue").read_text(encoding="utf-8")

        self.assertIn("VProgressLinear", source)
        self.assertIn("plugin/CleanInvalidPlugin/last_result", source)
        self.assertIn("props.api.put('plugin/CleanInvalidPlugin'", source)
        self.assertIn("jobRunning", source)
        self.assertIn("后台任务运行期间可以关闭页面", source)

    def test_page_does_not_replace_the_workspace_while_saving(self):
        source = (PLUGIN_ROOT / "src/components/Page.vue").read_text(encoding="utf-8")

        self.assertNotIn("async function onSave", source)
        self.assertNotIn('@save="onSave"', source)


if __name__ == "__main__":
    unittest.main()
