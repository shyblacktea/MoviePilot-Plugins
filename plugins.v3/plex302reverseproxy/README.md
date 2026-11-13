# PLEX 302 反向代理（Plex302ReverseProxy）

Plex 302 反向代理 + 纯响应式媒体流信息投影。在 Plex 响应里补 Media/Part/Stream 字段，完全不写 Plex 数据库，用于对照验证「不写库能否达到效果」。（小k自用版）

- 版本：`v1.0.0`
- 作者：shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vuetify JSON

## 目录

```
plugins.v3/plex302reverseproxy/
    __init__.py
    projection.py
    proxy_app.py
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
