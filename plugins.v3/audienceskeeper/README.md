# 人人人守护者（AudiencesKeeper）

人人人自动模拟过 CF 盾、更新 Cookie 并洗白搜索防刷计数。

- 版本：`v0.0.10`
- 作者：shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vuetify JSON

## 目录

```
plugins.v3/audienceskeeper/
    __init__.py
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
