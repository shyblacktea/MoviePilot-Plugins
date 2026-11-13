# 手动订阅助手（ManualSubscribeAssistantShy）

完整保留自动订阅助手的多来源抓取、配置和筛选界面，改为用户确认后手动订阅。（小k自用版）

- 版本：`v0.1.2`
- 作者：shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vue 联邦组件（`dist/assets`）

## 目录

```
plugins.v3/manualsubscribeassistantshy/
    README.md
    __init__.py
    core
    dist
    index.html
    node_modules
    package-lock.json
    package.json
    providers
    src
    vite.config.js
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
