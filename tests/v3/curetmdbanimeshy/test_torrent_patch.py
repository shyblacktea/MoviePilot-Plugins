"""资源匹配兼容回归：隔离宿主、配置和网络，执行实际插件包装逻辑。"""

import ast
import inspect
import sys
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from types import SimpleNamespace

import pytest


SOURCE = Path(__file__).resolve().parents[3] / "plugins.v3/curetmdbanimeshy/patch.py"


@contextmanager
def patched_matcher(original, correct):
    """为每个用例建立独立宿主替身，并确保方法描述符在退出时恢复。"""

    class TorrentMatcher:
        """仅提供资源和季集匹配入口的无网络宿主。"""

        match_torrent = staticmethod(original)

        @staticmethod
        def match_season_episodes(torrent, meta, season_episodes):
            """提供插件安装补丁所需的季集匹配入口。"""
            return True

    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    manager_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "MonkeyPatchManager"
    )
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")], level=0
            ),
            manager_node,
        ],
        type_ignores=[],
    )
    namespace = {
        "inspect": inspect,
        "sys": sys,
        "wraps": wraps,
        "TorrentHelper": TorrentMatcher,
        "logger": SimpleNamespace(debug=lambda *args: None, info=lambda *args: None),
    }
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
    manager = object.__new__(namespace["MonkeyPatchManager"])
    manager._original_methods = {}
    manager._is_patched = False
    manager._no_proxy_urls = []
    descriptors = {
        name: inspect.getattr_static(TorrentMatcher, name)
        for name in ("match_torrent", "match_season_episodes")
    }
    manager.patch_torrent_helper(correct)
    try:
        yield TorrentMatcher, manager
    finally:
        manager.unpatch_all()
        for name, descriptor in descriptors.items():
            assert inspect.getattr_static(TorrentMatcher, name) is descriptor


@pytest.mark.parametrize("scope", [None, {}, {1: [2, 3]}])
def test_explicit_episode_scope_reaches_original_unchanged(scope):
    """新宿主的季集范围必须原样进入核心判断，不能接收后丢弃。"""
    calls = []
    corrections = []
    media, meta, torrent = object(), object(), object()

    def original(mediainfo, torrent_meta, torrent, *, season_episodes=None):
        """记录核心实际收到的对象。"""
        calls.append((mediainfo, torrent_meta, torrent, season_episodes))
        return True

    with patched_matcher(original, lambda *args: corrections.append(args)) as (helper, _):
        assert helper.match_torrent(
            mediainfo=media, torrent_meta=meta, torrent=torrent, season_episodes=scope
        ) is True
        assert calls == [(media, meta, torrent, scope)]
        assert calls[0][3] is scope
        assert corrections == [(meta, media)]


@pytest.mark.parametrize("use_keywords", [False, True])
def test_legacy_three_argument_host_still_works(use_keywords):
    """旧核心没有季集参数时，不应由包装函数注入额外参数。"""
    calls = []
    media, meta, torrent = object(), object(), object()

    def original(mediainfo, torrent_meta, torrent):
        """模拟仅接受旧版三个参数的核心。"""
        calls.append((mediainfo, torrent_meta, torrent))
        return True

    with patched_matcher(original, lambda *args: None) as (helper, _):
        if use_keywords:
            result = helper.match_torrent(
                mediainfo=media, torrent_meta=meta, torrent=torrent
            )
        else:
            result = helper.match_torrent(media, meta, torrent)
        assert result is True
        assert calls == [(media, meta, torrent)]


def test_extension_arguments_reach_original_unchanged():
    """后续核心新增位置参数或关键字参数时，包装层不改变其值和顺序。"""
    calls = []
    media, meta, torrent, extension, policy = (object() for _ in range(5))

    def original(mediainfo, torrent_meta, torrent, *args, **kwargs):
        """模拟带扩展参数的核心。"""
        calls.append((mediainfo, torrent_meta, torrent, args, kwargs))
        return True

    with patched_matcher(original, lambda *args: None) as (helper, _):
        assert helper.match_torrent(media, meta, torrent, extension, policy=policy) is True
        assert calls == [(media, meta, torrent, (extension,), {"policy": policy})]
        assert calls[0][3][0] is extension
        assert calls[0][4]["policy"] is policy


@pytest.mark.parametrize("matched", [False, True])
def test_result_and_correction_order_are_preserved(matched):
    """只在核心匹配成功后修正元数据，并保留核心返回值。"""
    events = []
    media, meta, torrent = object(), object(), object()

    def original(mediainfo, torrent_meta, torrent):
        """记录核心判断在修正回调之前执行。"""
        events.append("match")
        return matched

    def correct(torrent_meta, mediainfo):
        """记录修正收到原始元数据对象。"""
        events.append(("correct", torrent_meta, mediainfo))

    with patched_matcher(original, correct) as (helper, _):
        assert helper.match_torrent(media, meta, torrent) is matched
        assert events == (["match", ("correct", meta, media)] if matched else ["match"])


def test_original_exception_propagates_without_correction():
    """核心失败必须对搜索调用者可见，且不能进入修正回调。"""
    failure = RuntimeError("core matching failed")
    corrections = []

    def original(mediainfo, torrent_meta, torrent):
        """模拟核心匹配异常。"""
        raise failure

    with patched_matcher(original, lambda *args: corrections.append(args)) as (helper, _):
        with pytest.raises(RuntimeError) as raised:
            helper.match_torrent(object(), object(), object())
        assert raised.value is failure
        assert corrections == []


def test_correction_exception_propagates():
    """修正失败不应被包装成匹配成功或静默忽略。"""
    failure = ValueError("metadata correction failed")

    def original(mediainfo, torrent_meta, torrent):
        """提供成功的核心匹配。"""
        return True

    def correct(torrent_meta, mediainfo):
        """模拟元数据修正异常。"""
        raise failure

    with patched_matcher(original, correct) as (helper, _):
        with pytest.raises(ValueError) as raised:
            helper.match_torrent(object(), object(), object())
        assert raised.value is failure


def test_repeated_patch_does_not_duplicate_correction_and_unpatch_restores():
    """重复安装不叠加回调，停用后调用恢复为未包装的核心方法。"""
    matches = []
    corrections = []
    media, meta, torrent = object(), object(), object()

    def original(mediainfo, torrent_meta, torrent):
        """统计每次实际核心调用。"""
        matches.append((mediainfo, torrent_meta, torrent))
        return True

    with patched_matcher(original, lambda *args: corrections.append(args)) as (helper, manager):
        manager.patch_torrent_helper(lambda *args: corrections.append("duplicate"))
        assert helper.match_torrent(media, meta, torrent) is True
        assert matches == [(media, meta, torrent)]
        assert corrections == [(meta, media)]
        manager.unpatch_all()
        assert helper.match_torrent is original
        assert helper.match_torrent(media, meta, torrent) is True
        assert matches == [(media, meta, torrent), (media, meta, torrent)]
        assert corrections == [(meta, media)]
