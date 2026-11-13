# 续作跟进魔改版（FollowUpShy）

续作跟进的独立 V3 适配版，修复媒体身份字段兼容。（小k自用版）

- 版本：`v0.0.5`
- 作者：Attente,shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vuetify JSON

## 目录

```
plugins.v3/followupshy/
    __init__.py
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
