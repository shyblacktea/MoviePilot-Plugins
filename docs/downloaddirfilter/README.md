# 下载目录滤镜

`DownloadDirFilter` 是面向 MoviePilot 的下载目录整理插件：根据自定义格式修改 MP 下载种子的保存路径与种子名称。（小k自用版）

## 主要功能

- 按自定义格式修改下载种子的保存路径与种子名称。
- 支持 TMDB 识别信息参与路径与名称格式化。
- 首次加载自动迁移原「路径名称格式化」插件的配置与全部处理记录。

## 更新日志

### 0.0.1

- 由路径名称格式化（FormatDownPath）改造为独立插件「下载目录滤镜」。
- 适配 MoviePilot V3 媒体身份 API，修复 `DownloadHistory.tmdbid` 与 `TransferHistoryOper.get_by_type_tmdbid` 报错。
- 首次加载自动迁移原插件配置与全部处理记录。

## 发布信息

- 插件 ID：`DownloadDirFilter`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 插件目录：`plugins.v3/downloaddirfilter/`
- 当前版本：`0.0.1`
- Release Tag：`DownloadDirFilter_v0.0.1`
- Release 资产：`downloaddirfilter_v0.0.1.zip`

## 致谢

- 原作者：[Attente](https://github.com/wikrin)
- 原仓库：[wikrin/MoviePilot-Plugins](https://github.com/wikrin/MoviePilot-Plugins)

本版本基于原作者的路径名称格式化插件改造，感谢原作者和 MoviePilot 社区。
