# 订阅下载增强（SubscribePlus）

按订阅目标集数检测电视剧缺集，并分析 PT 资源、识别和订阅规则原因。（小k自用版）

- 版本：`v1.1.14`
- 作者：shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vue 联邦组件（`dist/assets`）

## 目录

```
plugins.v3/subscribeplus/
    .gitignore
    __init__.py
    diagnosis.py
    diagnosis_service.py
    dist
    download_service.py
    identifiers.py
    index.html
    models.py
    package-lock.json
    package.json
    pnpm-lock.yaml
    pnpm-workspace.yaml
    romaji.py
    rules.py
    scanner.py
    search_service.py
    season_cleanup.py
    sites.py
    src
    storage.py
    subscription_log.py
    telegram.py
    vite.config.js
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
