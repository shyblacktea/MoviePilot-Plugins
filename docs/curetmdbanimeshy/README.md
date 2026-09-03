# CTMDbA魔改版（番剧季信息分离）

`CureTMDbAnimeShy` 是面向 MoviePilot 的番剧季信息分离插件：对 TMDb 上被合并为一季的番剧进行季信息分离。（小k自用版）

## 主要功能

- 对 TMDb 上被合并为一季的番剧进行季信息分离。
- 通过本地 Go 服务代理 TheMovieDb API 请求，实现季号/集号修正。
- 支持 Bangumi API 辅助匹配，支持自定义分季数据源。

## 更新日志

### 0.0.1

- 迁移到 MoviePilot V3 专用实现（`plugins.v3` + `package.v3.json`）。
- 旧导入 `app.core.*`/`app.helper.*`/`app.utils.*`/`app.log` 统一迁移到 `app.sdk.*`。
- 独立插件 ID `CureTMDbAnimeShy`，杜绝与原版 `CureTMDbAnime` 来源冲突。

## 发布信息

- 插件 ID：`CureTMDbAnimeShy`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 插件目录：`plugins.v3/curetmdbanimeshy/`
- 当前版本：`0.0.1`
- Release Tag：`CureTMDbAnimeShy_v0.0.1`
- Release 资产：`curetmdbanimeshy_v0.0.1.zip`

## 致谢

- 原作者：[Attente](https://github.com/wikrin)
- 原插件仓库：[wikrin/MoviePilot-Plugins](https://github.com/wikrin/MoviePilot-Plugins)
- 二进制/数据源：[wikrin/CureTMDb](https://github.com/wikrin/CureTMDb)

本版本基于原作者的 CureTMDbAnime 插件改造，二进制仍由原作者 wikrin 编译分发，感谢原作者和 MoviePilot 社区。
