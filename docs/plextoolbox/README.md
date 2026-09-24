# PLEX 工具箱

`PlexToolbox` 是 Plex 综合维护插件，整合 302 反向代理、STRM 媒体流信息补全、刮削辅助、缺海报修复和 TMDB 重复条目合并。

- 插件 ID：`PlexToolbox`
- 当前 V3 版本：`1.0.0`
- V2 版本线：`0.7.3`
- V2 源码目录：`plugins.v2/plextoolbox/`
- V3 源码目录：`plugins.v3/plextoolbox/`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 作者：`shyblacktea`

## 工作流程

```text
读取 Plex / Emby / helper 配置 → 执行代理、补全、刮削或媒体维护 → 展示结果和历史 → 用户确认高影响操作
```

各功能区相对独立，未配置对应服务时不会执行该功能。


## 主要功能

### 302 反向代理

- 播放和下载请求按 STRM 内容或路径规则返回 302 直链。
- 可强制 DirectPlay，减少转码导致的直链失效。
- 缓存 Part 路径，合并相同起播请求，并代理 WebSocket 事件。

### STRM 媒体流信息补全

- 从 Emby 读取同名媒体的编码、分辨率、音轨、字幕和时长信息。
- 通过部署在 Plex 所在机器的 helper 写入 Plex 数据库。
- 支持手动全量、定时全量、播放停止后增量和播前补全。
- 支持查看最近结果和补全历史。

### 刮削和媒体维护

- 对指定媒体库执行取消匹配、重读 NFO 和重新匹配。
- 扫描缺海报条目，并按配置调用 TMDB 或 MoviePilot 刮削。
- 支持缺 `poster.jpg` 补全。
- 支持扫描 TMDB ID 相同的重复条目并合并处理。

## helper 部署

写库 helper 位于 `helper/plex_mediainfo_helper.py`，提供 `/health`、`/dbinfo`、`/busy`、`/write` 和 `/write_batch` 接口。helper 需要部署在 Plex 所在机器，并使用 `X-PTH-Token` 校验请求。

详细部署说明见 [helper/README.md](../../plugins.v2/plextoolbox/helper/README.md)。

## 配置说明

- `302 反向代理`：Plex 地址、Token、监听地址、监听端口、DirectPlay 和路径规则。
- `媒体流补全`：Emby 地址、媒体库范围、helper 地址、Token、补全触发方式和后续集数窗口。
- `刮削辅助`：媒体库、dry-run、重匹配和封面补全策略。
- `数据页`：查看运行状态、最近结果、播放补全历史和清理入口。

反代配置变化可能重启独立代理；补全配置变化不会无条件重启代理。

## 数据和安全边界

- Plex Token、Emby 凭据和 helper Token 属于敏感配置，不应写入日志或提交到仓库。
- helper 具备写入 Plex 数据库的能力，必须限制监听地址并配置强 Token。
- 取消匹配、重匹配、写库、合并重复条目和清理历史均可能改变媒体库状态。
- dry-run 只用于预览，不等同于实际执行。
- 302 代理、媒体流补全和刮削辅助可单独使用，互不替代。

## 版本记录

### V3 v1.0.0

- 新增 TMDB ID 相同重复条目的扫描和合并功能。
- 将 V2 功能整理为 V3 独立插件，保留 302 代理、媒体流补全和刮削辅助。
- 使用 Vue 联邦配置页和数据页。

### V2 v0.7.3 及更早版本

- 保留 V2 版本的播前补全、播放停止增量补全、Helper 健康检查、刮削辅助、缺封面修复和播放历史功能。
- V2 与 V3 版本线并行维护，具体变更以对应 package 和 Release 为准。

## 说明

这是 Plex 综合维护工具，不是 Plex 本体或 Emby 本体。涉及写库、重匹配和批量维护前，请先备份相关数据库和媒体元数据。

## 发布信息

- 插件 ID：`PlexToolbox`
- V2 源码目录：`plugins.v2/plextoolbox/`
- V3 源码目录：`plugins.v3/plextoolbox/`
- 当前版本：`V2 0.7.3；V3 1.0.0`

## 致谢

感谢相关媒体直链代理项目、MoviePilot 插件生态和 Plex/Emby 社区提供思路与基础能力。