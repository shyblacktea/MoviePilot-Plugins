import unittest

from subscribeplus.diagnosis import (
    TorrentDiagnoser,
    classify_results,
    extract_season_episode,
    normalize_search_result,
)
from subscribeplus.models import DiagnosisInput, StaleEpisode


class DiagnosisTest(unittest.TestCase):
    def test_no_result_is_no_pt_resource(self):
        self.assertEqual(classify_results([], season=1, episode=3, include_pattern="").reason, "no_pt_resource")

    def test_matching_result_without_rule_hit_is_rule_blocked(self):
        results = [{"title": "Show.S01E03.1080p.CR", "site": "cr", "recognized": True, "season": 1, "episode": 3}]

        self.assertEqual(classify_results(results, season=1, episode=3, include_pattern="baha").reason, "rule_blocked")

    def test_unrecognized_episode_hit_is_recognition_issue(self):
        results = [{"title": "Show.S01E03.1080p", "recognized": False, "season": 1, "episode": 3}]

        self.assertEqual(classify_results(results, season=1, episode=3, include_pattern="").reason, "recognition_issue")

    def test_normalize_search_result_keeps_moviepilot_resource_fields(self):
        result = normalize_search_result(
            {
                "title": "Show.S01E03.2026.1080p.Baha.WEB-DL.H264-FROGWeb",
                "site": "13",
                "site_name": "MT",
                "seeders": 101,
                "size": 123456789,
                "description": "Episode 3",
                "pubdate": "2026-07-04 00:00:00",
                "freedate": "2026-11-25 00:00:00",
                "freedate_diff": "4月21天",
                "volume_factor": "50%",
                "uploadvolumefactor": 1.0,
                "downloadvolumefactor": 0.5,
                "labels": ["Baha", "WEB-DL"],
                "quality": "WEB-DL",
                "resolution": "1080p",
                "video_codec": "H264",
                "platforms": ["Baha"],
                "release_groups": ["FROGWeb"],
            }
        )

        self.assertEqual(result["volume_factor"], "50%")
        self.assertEqual(result["freedate_diff"], "4月21天")
        self.assertEqual(result["quality"], "WEB-DL")
        self.assertEqual(result["resolution"], "1080p")
        self.assertEqual(result["video_codec"], "H264")
        self.assertEqual(result["platforms"], ["Baha"])
        self.assertEqual(result["release_groups"], ["FROGWeb"])
        self.assertEqual(result["labels"], ["Baha", "WEB-DL"])

    def test_extract_season_episode_from_title(self):
        self.assertEqual(extract_season_episode("Some.Show.S02E04.1080p"), (2, 4))
        self.assertEqual(extract_season_episode("Some Show 第3集"), (None, 3))
        self.assertEqual(extract_season_episode("Some Show 04话"), (None, 4))

    def test_diagnoser_keeps_only_missing_episode_candidates(self):
        def search(_item):
            return [
                {"title": "Show.S01E07.1080p", "recognized": True, "season": 1, "episode": 7},
                {"title": "Show.S01E08.1080p", "recognized": True, "season": 1, "episode": 8},
                {"title": "Show.S01E09.1080p", "recognized": True, "season": 1, "episode": 9},
            ]

        item = DiagnosisInput(
            subscribe_id=1,
            title="Show",
            tmdbid=100,
            season=1,
            category="日番",
            episodes=[
                StaleEpisode(season=1, episode=8, air_date="2026-07-01"),
                StaleEpisode(season=1, episode=9, air_date="2026-07-02"),
            ],
        )

        diagnosis = TorrentDiagnoser(search).diagnose(item)

        self.assertEqual(diagnosis.reason, "downloadable")
        self.assertEqual([candidate["episode"] for candidate in diagnosis.candidates], [8, 9])

    def test_diagnoser_keeps_multi_episode_candidate_when_it_covers_missing_episode(self):
        def search(_item):
            return [
                {
                    "title": "Show.S01E01-E10.1080p",
                    "recognized": True,
                    "season": 1,
                    "episode": 1,
                    "episodes": list(range(1, 11)),
                }
            ]

        item = DiagnosisInput(
            subscribe_id=1,
            title="Show",
            tmdbid=100,
            season=1,
            category="日番",
            episodes=[StaleEpisode(season=1, episode=8, air_date="2026-07-01")],
        )

        diagnosis = TorrentDiagnoser(search).diagnose(item)

        self.assertEqual(diagnosis.reason, "downloadable")
        self.assertEqual(diagnosis.candidates[0]["episodes"], list(range(1, 11)))


if __name__ == "__main__":
    unittest.main()
