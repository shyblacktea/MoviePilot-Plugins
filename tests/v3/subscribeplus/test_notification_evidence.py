"""通知证据、下载撤销和交互安全边界的离线回归测试。"""
import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


@contextmanager
def plugin_modules():
    """以唯一 app.plugins 命名空间隔离加载本地源码并恢复模块状态。"""
    root = Path(__file__).resolve().parents[3] / "plugins.v3" / "subscribeplus"
    prefix = "app.plugins.subscribeplus"
    previous = {key: value for key, value in sys.modules.items() if key == prefix or key.startswith(prefix + ".")}
    for key in previous:
        del sys.modules[key]
    spec = importlib.util.spec_from_file_location(prefix, root / "__init__.py", submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[prefix] = module
    try:
        spec.loader.exec_module(module)
        yield module, sys.modules[prefix + ".storage"], sys.modules[prefix + ".telegram"]
    finally:
        for key in list(sys.modules):
            if key == prefix or key.startswith(prefix + "."):
                del sys.modules[key]
        sys.modules.update(previous)


def diagnosis():
    """构造缺十集但只有一集候选的大魔王诊断。"""
    return {"subscribe_id": 350, "title": "大魔王", "media_source": "themoviedb", "media_id": "280042",
            "season": 2, "reason": "rule_blocked", "message": "包含规则拦截",
            "episodes": [{"episode": ep} for ep in range(1, 11)],
            "candidates": [{"season": 2, "episode": 1, "title": "Show S02E01 CR"}]}


def test_summary_separates_target_and_candidate_coverage():
    """汇总标注截断总数并只展示实际候选覆盖集。"""
    with plugin_modules() as (_, _, telegram):
        text = telegram.render_scan_summary_text([diagnosis()])
        assert "需确认" in text and "等，共 10 集" in text
        assert "候选覆盖：E01（不代表全部可下载）" in text
        assert "包含规则拦截" in text


def test_download_invalidates_old_candidate_and_buttons():
    """下载唯一命中集后移除旧诊断，而非继续提示其他九集可补。"""
    with plugin_modules() as (_, storage, _), TemporaryDirectory() as directory:
        store = storage.JsonStore(Path(directory))
        item = diagnosis()
        store.save_scan_results([item])
        store.save_interaction("detail", {"diagnosis": item})
        store.save_interaction("summary", {"view": "scan_summary", "items": [item]})
        store.save_interaction("ci", {"view": "ci_tool"})
        store.invalidate_downloaded_candidates("themoviedb", "280042", 2, {1})
        assert store.load_scan_results() == []
        assert store.load_interaction("detail") is None
        assert store.load_interaction("summary") is None
        assert store.load_interaction("ci") == {"view": "ci_tool"}


def test_download_preserves_other_identity_season_and_unknown_coverage():
    """错误来源、季号或没有明确集数不得撤销诊断。"""
    with plugin_modules() as (_, storage, _), TemporaryDirectory() as directory:
        store = storage.JsonStore(Path(directory))
        store.save_scan_results([diagnosis()])
        for source, season, episodes in [("bangumi", 2, {1}), ("themoviedb", 1, {1}), ("themoviedb", 2, set())]:
            store.invalidate_downloaded_candidates(source, "280042", season, episodes)
            assert len(store.load_scan_results()) == 1


def test_partial_download_keeps_remaining_candidates():
    """部分下载保留尚未覆盖的候选，不影响其他剧。"""
    with plugin_modules() as (_, storage, _), TemporaryDirectory() as directory:
        store = storage.JsonStore(Path(directory))
        item = diagnosis()
        item["candidates"].append({"season": 2, "episodes": [2], "title": "Show S02E02"})
        other = {**diagnosis(), "media_id": "other", "subscribe_id": 351}
        store.save_scan_results([item, other])
        store.invalidate_downloaded_candidates("themoviedb", "280042", 2, {1})
        rows = store.load_scan_results()
        assert rows[0]["episodes"][0]["episode"] == 2
        assert len(rows[0]["candidates"]) == 1
        assert rows[1]["media_id"] == "other"


def test_other_site_result_is_unconfirmed_not_absence():
    """其他站点命中不得把一次空搜索判定成订阅站点没有资源。"""
    from types import SimpleNamespace
    with plugin_modules() as (plugin, _, _):
        item = plugin.DiagnosisInput(subscribe_id=351, title="死神", tmdbid=30984, season=2,
                                     category="日番", sites=["12"], episodes=[], include="")
        result = SimpleNamespace(candidates=[{}], reason="downloadable", message="", search_stats={})
        instance = object.__new__(plugin.SubscribePlus)
        instance._plugin_config = plugin.PluginConfig.from_dict({})
        instance._ensure_site_resolver = lambda: SimpleNamespace(resolve_for_category=lambda *_: ["12", "27"], names_for=lambda sites: sites)
        instance._build_subscription_site_progress = lambda *_: []
        original = plugin.TorrentDiagnoser
        try:
            plugin.TorrentDiagnoser = lambda *_: SimpleNamespace(diagnose=lambda _: result)
            instance._search_torrents = lambda *_: []
            actual = instance._diagnose_other_sites_when_subscription_scope_missing(item, {}, SimpleNamespace(sites=["12"]))
            assert actual.reason == "search_unconfirmed"
            assert "不代表订阅站点没有资源" in actual.message
        finally:
            plugin.TorrentDiagnoser = original


def test_download_event_passes_explicit_identity_and_episodes():
    """下载事件使用识别后的季集事实，不从原始种子名推断。"""
    from types import SimpleNamespace
    with plugin_modules() as (plugin, _, _):
        instance = object.__new__(plugin.SubscribePlus)
        instance._plugin_config = plugin.PluginConfig.from_dict({"enabled": True})
        calls = []
        instance._ensure_store = lambda: SimpleNamespace(invalidate_downloaded_candidates=lambda *args: calls.append(args))
        event = SimpleNamespace(event_data={"episodes": [41, 42], "context": SimpleNamespace(
            media_info=SimpleNamespace(media_source="themoviedb", media_id="30984"),
            meta_info=SimpleNamespace(begin_season=2))})
        instance._invalidate_downloaded_diagnosis(event)
        assert calls == [("themoviedb", "30984", 2, {41, 42})]


def test_cache_prune_has_timedelta_dependency():
    """按缓存天数清理实际执行 timedelta 分支，避免运行时 NameError。"""
    with plugin_modules() as (_, storage, _), TemporaryDirectory() as directory:
        store = storage.JsonStore(Path(directory))
        store._write("candidate_cache.json", {"old": {"cached_at": "2020-01-01T00:00:00"}})
        assert store.prune_candidate_cache(1) == 1


def test_scan_results_are_refreshed_before_save_or_notify():
    """诊断阶段带回已入库集时，保存前复核必须将其剔除。"""
    with plugin_modules() as (plugin, _, _):
        instance = object.__new__(plugin.SubscribePlus)
        calls = []
        instance._refresh_scan_result_item = lambda item: calls.append(item) or (
            {**item, "episodes": [{"episode": 195}]}
        )
        result = instance._refresh_scan_results([{"episodes": [{"episode": 194}, {"episode": 195}]}])
        assert calls
        assert result == [{"episodes": [{"episode": 195}]}]


def test_scan_results_drop_item_when_fresh_library_check_finds_all():
    """当前媒体库覆盖全部缺集时，不应产生保存或通知项目。"""
    with plugin_modules() as (plugin, _, _):
        instance = object.__new__(plugin.SubscribePlus)
        instance._refresh_scan_result_item = lambda _item: None
        assert instance._refresh_scan_results([{"subscribe_id": 284}]) == []
