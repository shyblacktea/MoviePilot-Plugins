# 下载目录滤镜（DownloadDirFilter）

根据自定义格式修改MP下载种子的保存路径、种子名称。（小k自用版）

- 版本：`v0.0.2`
- 作者：shyblacktea
- 要求 MoviePilot：`>=3.0.0`
- 页面渲染：Vue 联邦组件（`dist/assets`）

## 目录

```
plugins.v3/downloaddirfilter/
    __init__.py
    dist
```

## 说明

- 插件主类与全部运行逻辑位于 `__init__.py`，遵循 MoviePilot V3 插件约定（`app.sdk.*` 稳定接口）。
- 需要调试时把本目录用 `PLUGIN_LOCAL_REPO_PATHS` 指给宿主，并开启 `PLUGIN_AUTO_RELOAD=true`。
- 发布时 `plugin_version`、`package.v3.json` 的 `version` 与 `history` 置顶条目必须一致。
