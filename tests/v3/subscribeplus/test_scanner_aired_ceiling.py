"""扫描上限收敛到「已播出集」的离线回归测试。

场景来自真实误报：斗破苍穹 S05 起始集 200，TMDB 已给到 219 集元数据，
但实际只播到 210 时，缺失判定不应把 211+ 计入。
"""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "plugins.v3" / "subscribeplus"


def load_scanner():
    """以独立包命名空间加载 scanner/models/sites，避免依赖 MoviePilot 宿主。"""
    if "sp_scanner_test" in sys.modules:
        for key in [k for k in sys.modules if k == "sp_scanner_test" or k.startswith("sp_scanner_test.")]:
            del sys.modules[key]
    pkg = types.ModuleType("sp_scanner_test")
    pkg.__path__ = [str(ROOT)]
    sys.modules["sp_scanner_test"] = pkg
    spec = importlib.util.spec_from_file_location("sp_scanner_test.scanner", ROOT / "scanner.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["sp_scanner_test.scanner"] = module
    spec.loader.exec_module(module)
    models = sys.modules["sp_scanner_test.models"]
    return module, models


def make_subscribe(**overrides):
    fields = dict(
        id=390, name="斗破苍穹", type="电视剧", season=5, total_episode=219,
        start_episode=200, state="R", media_source="themoviedb", media_id="79481",
        include="", media_category="",
    )
    fields.update(overrides)
    return types.SimpleNamespace(**fields)


def run_scan(ceiling, subscribe=None, downloaded_upto=207):
    module, models = load_scanner()
    subscribe = subscribe or make_subscribe()
    config = models.PluginConfig(selected_categories=["未分类"])
    resolver = module.SiteResolver(lambda: [{"id": "site1", "name": "站点1"}])
    scanner = module.SubscriptionScanner(
        load_subscribes=lambda: [subscribe],
        is_episode_downloaded=lambda _s, _m, _season, ep: (ep <= downloaded_upto, ""),
        load_downloaded_episodes=lambda _s, _m, _season: set(),
        aired_episode_ceiling=(lambda _s, _m, _season: ceiling),
    )
    return scanner, scanner.scan(config, resolver)


def test_ceiling_clips_future_episodes():
    """已播到 210 时只报 208-210，不把 211+ 算缺失。"""
    _, results = run_scan(ceiling=210)
    assert len(results) == 1
    assert [e.episode for e in results[0].episodes] == [208, 209, 210]


def test_unknown_ceiling_falls_back_to_total():
    """拿不到播出进度时保持旧行为（按总集数扫描）。"""
    _, results = run_scan(ceiling=None)
    assert [e.episode for e in results[0].episodes] == list(range(208, 220))


def test_no_aired_episode_skips_subscribe():
    """整季未开播时整条跳过，并记录 not_aired_yet。"""
    scanner, results = run_scan(ceiling=0)
    assert results == []
    assert scanner.last_scan_stats["not_aired_yet"] == 1


def test_start_episode_is_lower_bound():
    """起始集仍是下限：起始 210 + 已播 210 只检查 E210。"""
    _, results = run_scan(ceiling=210, subscribe=make_subscribe(start_episode=210))
    assert [e.episode for e in results[0].episodes] == [210]


def test_ceiling_cannot_exceed_total():
    """TMDB 播出进度大于总集数时以总集数为准。"""
    _, results = run_scan(
        ceiling=999,
        subscribe=make_subscribe(start_episode=218),
    )
    assert [e.episode for e in results[0].episodes] == [218, 219]


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print("PASS", name)
