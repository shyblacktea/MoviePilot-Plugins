"""已播进度换算的离线回归测试（番剧合并季的分季修正）。

真实案例：药屋少女的呢喃在 TMDB 只有 S1（60 集，已播 55），
CureTMDb 分季把 S1+S2 划为 48 集，于是「S03 已播」= 55 - 48 = 7，
与媒体库里 S3 已有的 7 集一致；E08+ 未播，不该算缺失。
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "plugins.v3" / "subscribeplus"


def load_aired():
    spec = importlib.util.spec_from_file_location("sp_aired_under_test", ROOT / "aired.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episodes(*pairs):
    return [{"episode_number": number, "air_date": air_date} for number, air_date in pairs]


def test_aired_max_and_count_ignores_future_and_empty_dates():
    aired = load_aired()
    data = episodes((1, "2026-10-01"), (2, "2026-10-08"), (3, "2026-12-25"), (4, ""), (5, None))
    assert aired.aired_max_and_count(data, "2026-11-17") == (2, 2)


def test_preceding_episode_count_sums_only_earlier_seasons():
    aired = load_aired()
    counts = {1: 24, 2: 24, 3: 12}
    assert aired.preceding_episode_count(counts, 3) == 48
    assert aired.preceding_episode_count(counts, 1) == 0


def test_ceiling_from_merged_season_matches_real_case():
    """药屋：合并季已播 55 - 前置 48 = 7。"""
    aired = load_aired()
    assert aired.ceiling_from_merged_season(55, 48) == 7


def test_ceiling_without_split_data_returns_none():
    """没有分季依据时交回调用方回落旧逻辑。"""
    aired = load_aired()
    assert aired.ceiling_from_merged_season(55, 0) is None


def test_ceiling_zero_when_nothing_of_split_season_aired():
    aired = load_aired()
    assert aired.ceiling_from_merged_season(48, 48) == 0
    assert aired.ceiling_from_merged_season(40, 48) == 0


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print("PASS", name)
