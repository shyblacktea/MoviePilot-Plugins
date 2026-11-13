# PLEX 工具箱（PlexToolbox）

Plex 302 反向代理、STRM 媒体流信息补全、缺海报修复与 TMDB 重复条目合并。（小k自用版）

- 版本：`v1.0.0`
- 作者：shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vue 联邦组件（`dist/assets`）

## 目录

```
plugins.v3/plextoolbox/
    .gitignore
    __init__.py
    dist
    emby_client.py
    helper
    helper_client.py
    index.html
    mediainfo.py
    package-lock.json
    package.json
    plex_client.py
    poster_fixer.py
    proxy_app.py
    scrape_tools.py
    src
    vite.config.js
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
