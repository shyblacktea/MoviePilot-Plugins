"""识别兼容回归：隔离宿主与网络，可由 pytest 或直接运行执行。"""

import ast
import asyncio
import inspect
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[3] / "plugins.v3/curetmdbanimeshy"


def load_class(filename, name, namespace):
    """提取实际源码类，在隔离依赖下验证生产方法。"""
    tree = ast.parse((SOURCE / filename).read_text(encoding="utf-8"))
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == name)
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(SOURCE / filename), "exec"), namespace)
    return namespace[name]


def test_recognition_wrappers():
    """同步异步修正均触发，参数透传，空结果跳过，停止时恢复。"""
    media = object()
    calls = []

    class Chain:
        """无网络识别替身。"""
        def recognize_by_meta(self, metainfo, **kwargs):
            """记录同步调用。"""
            calls.append((metainfo, kwargs))
            return media if metainfo else None

        async def async_recognize_by_meta(self, metainfo, **kwargs):
            """记录异步调用。"""
            calls.append((metainfo, kwargs))
            return media if metainfo else None

    ns = {"asyncio": asyncio, "wraps": wraps, "inspect": inspect, "MediaChain": Chain,
          "logger": SimpleNamespace(debug=lambda *a: None, info=lambda *a: None)}
    manager_class = load_class("patch.py", "MonkeyPatchManager", ns)
    manager = object.__new__(manager_class)
    manager._original_methods = {}
    manager._is_patched = False
    manager._no_proxy_urls = []
    original_sync = Chain.recognize_by_meta
    original_async = Chain.async_recognize_by_meta
    corrected = []
    manager.patch_media_recognition(lambda meta, info: corrected.append((meta, info)))
    try:
        chain = Chain()
        meta = object()
        assert chain.recognize_by_meta(metainfo=meta, media_source="themoviedb") is media
        assert asyncio.run(chain.async_recognize_by_meta(meta, episode_group="group")) is media
        assert chain.recognize_by_meta(None) is None
        assert asyncio.run(chain.async_recognize_by_meta(None)) is None
        assert corrected == [(meta, media), (meta, media)]
        assert calls[:2] == [(meta, {"media_source": "themoviedb"}), (meta, {"episode_group": "group"})]
        manager.patch_media_recognition(lambda *a: corrected.append("duplicate"))
        chain.recognize_by_meta(meta)
        assert corrected[-1] == (meta, media)
    finally:
        manager.unpatch_all()
    assert Chain.recognize_by_meta is original_sync
    assert Chain.async_recognize_by_meta is original_async


def test_structured_season_context():
    """实际修正用例兼容结构化季集和旧字典，累计 1163 定位 S23E08。"""
    ns = {"date": date, "datetime": datetime, "timedelta": timedelta,
          "logger": SimpleNamespace(debug=lambda *a: None)}
    exec(compile((SOURCE / "models.py").read_text(encoding="utf-8"), str(SOURCE / "models.py"), "exec"), ns)
    use_case_class = load_class("engine.py", "MetaCorrectionUseCase", ns)
    point = ns["EpisodePoint"]
    counts = [61, 16, 14, 39, 13, 52, 33, 35, 73, 45, 26, 14, 101, 58, 62, 50, 56, 55, 74, 14, 197, 67, 25]

    class Structured:
        """模拟宿主 Pydantic 数据对象。"""
        def __init__(self, values):
            """保存对象字段。"""
            self.values = values

        def model_dump(self):
            """投影为旧版字典。"""
            return self.values

    contexts = []
    use_case = object.__new__(use_case_class)
    use_case.grace_episodes = 2
    use_case._build_release_info = lambda **kw: SimpleNamespace(title="One.Piece.S23E1163", parsed_range=SimpleNamespace(format=lambda: "S23E1163"), release_date=None, source=None, tmdb_mapping={})
    use_case.count_finalized_resolver = lambda media: False
    use_case.decision_engine = SimpleNamespace(decide=lambda **kw: contexts.append(kw["show_context"]))
    # 同时运行完整生产决策引擎，避免仅验证上下文构造。
    from dataclasses import replace
    ns["replace"] = replace
    ns["logger"].info = lambda *a: None
    ns["logger"].warning = lambda *a: None
    ns["logger"].warn = lambda *a: None
    engine_tree = ast.parse((SOURCE / "engine.py").read_text(encoding="utf-8"))
    engine_tree.body = [node for node in engine_tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    engine_tree.body.insert(0, ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0))
    exec(compile(ast.fix_missing_locations(engine_tree), str(SOURCE / "engine.py"), "exec"), ns)
    for structured in (False, True):
        convert = Structured if structured else lambda value: value
        media = SimpleNamespace(seasons={i: list(range(1, count + 1)) for i, count in enumerate(counts, 1)},
                                season_info=[convert({"season_number": i, "air_date": None}) for i in range(1, 24)],
                                tmdb_info={}, next_episode_to_air=convert({"season_number": 23, "episode_number": 26, "air_date": None}),
                                tmdb_id=37854, episode_group=None)
        use_case.correct(meta=object(), mediainfo=media, tmdb_mapping={})
        assert contexts[-1].absolute_to_point[1163] == point(23, 8)
        assert contexts[-1].next_episode == point(23, 26)
        real_use_case = ns["MetaCorrectionUseCase"](grace_episodes=2, rewrite_threshold=16)
        real_use_case.count_finalized_resolver = lambda media: False
        meta = SimpleNamespace(title="One.Piece.S23E1163.1999.1080p.CR.WEB-DL.H.264.AAC-FROGWeb.mkv", year="1999", season_list=[23], episode_list=[1163])
        media.status = "Returning Series"
        decision = real_use_case.correct(meta=meta, mediainfo=media, tmdb_mapping={})
        assert decision.changed, decision.reasons
        assert decision.final_range.begin == point(23, 8), decision.reasons


if __name__ == "__main__":
    test_recognition_wrappers()
    test_structured_season_context()
    print("PASS: sync/async recognition, argument forwarding, empty result, duplicate patch, restore, structured/dict season context")
