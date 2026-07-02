import unittest

from subscribeplus.diagnosis import classify_results, extract_season_episode


class DiagnosisTest(unittest.TestCase):
    def test_no_result_is_no_pt_resource(self):
        self.assertEqual(classify_results([], season=1, episode=3, include_pattern="").reason, "no_pt_resource")

    def test_matching_result_without_rule_hit_is_rule_blocked(self):
        results = [{"title": "Show.S01E03.1080p.CR", "site": "cr", "recognized": True, "season": 1, "episode": 3}]

        self.assertEqual(classify_results(results, season=1, episode=3, include_pattern="baha").reason, "rule_blocked")

    def test_unrecognized_episode_hit_is_recognition_issue(self):
        results = [{"title": "Show.S01E03.1080p", "recognized": False, "season": 1, "episode": 3}]

        self.assertEqual(classify_results(results, season=1, episode=3, include_pattern="").reason, "recognition_issue")

    def test_extract_season_episode_from_title(self):
        self.assertEqual(extract_season_episode("Some.Show.S02E04.1080p"), (2, 4))
        self.assertEqual(extract_season_episode("Some Show 第3集"), (None, 3))
        self.assertEqual(extract_season_episode("Some Show 04话"), (None, 4))


if __name__ == "__main__":
    unittest.main()
