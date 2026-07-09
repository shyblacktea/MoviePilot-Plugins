# PLEX 工具箱（PlexToolbox）

Plex 302 反向代理 + STRM 媒体流信息补全。由「PLEX 302 反向代理」升级而来，保留原 302 反代能力，新增媒体流信息补全模块。

## 功能

### 1. 302 反向代理

代理 Plex 播放/下载流，自动跳转到最终直链，支持 STRM 与顶置路径规则、强制 DirectPlay、WebSocket 代理。

### 2. STRM 媒体流信息补全

为 Plex 中的 STRM 条目补全编码、分辨率、码率、音轨、时长等媒体流信息（Plex 自身无法为 STRM 写入这些字段）。

- **数据源①**：Emby MediaStreams（按文件名匹配同一媒体）
- **数据源②**：ffprobe 探测远程直链（仅读文件头）
- 通过部署在 Plex 主机上的 helper 写库服务，安全写入 Plex SQLite 库（写前自动备份、Plex 繁忙时拒写）

## 部署 helper

媒体信息补全需在 Plex 所在主机部署 `helper/` 下的写库服务，详见插件目录内 `helper/README.md`。

部署后需在 Plex 关闭「深度媒体分析」与定时 Analyze 任务，避免 Plex 重新分析覆盖写入的媒体信息。

## 配置

在插件 UI 分两个 Tab 配置：

- **反向代理**：Plex 地址、Token、监听端口、顶置规则等
- **媒体信息补全**：helper 地址+token、Plex 直连地址+token、Emby 地址+key、要处理的媒体库、并发数、定时 Cron 等

## 更新日志

### v0.3.0

- 由「PLEX 302 反向代理」升级为工具箱
- 新增 STRM 媒体流信息补全（Emby MediaStreams / ffprobe 探测直链，经 helper 安全写入 Plex 库）
- 保留原 302 反向代理能力
