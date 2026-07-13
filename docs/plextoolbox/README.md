# PLEX 工具箱

`PlexToolbox` 是 Plex 综合工具插件：302 反向代理 + STRM 媒体流信息补全（Emby 数据源写入 Plex 库）+ 刮削辅助工具。由 `Plex302ReverseProxy` 改造扩展而来。

## 主要功能

### 302 反向代理

- 播放/下载请求按 STRM 内容或顶置路径规则 302 重定向到直链，避免 Plex 中转流量。
- 转码决策强制 DirectPlay，避免转码使 302 失效。
- 元数据响应自动缓存 Part 路径，单集详情页预热 STRM 解析，加快起播。
- 并发相同请求单飞合并，只触发一次上游解析。
- WebSocket 通知双向代理。

### STRM 媒体流信息补全

- Plex 自身无法探测 STRM 直链的媒体流信息（编码/分辨率/音轨/字幕/时长），本功能从 Emby 读取同名文件的 MediaStreams，经部署在 Plex 所在机器上的 helper 小服务直接写入 Plex 数据库。
- 支持手动全量、定时全量、播放停止后增量补全（本集 + 后 N 集，已补全自动跳过）。
- 播放停止触发来源：反代嗅探 `/:/timeline?state=stopped` 或 Plex Webhook。
- 数据页展示最近一次补全结果与播放补全历史，支持一键清理。

### 刮削辅助

- 一键取消匹配（重读 NFO），支持 dry-run 预览与执行后自动 rematch。
- 扫描缺封面条目并调用 MoviePilot 刮削生成 NFO + 封面。
- 缺 poster.jpg 补全：电影从 TMDB 取海报（原产语言 → zh → 无字 → 任意），剧集优先复制季内 `Season X/poster.jpg` 到剧根，无则回退 TMDB，修复后自动 refresh。

## helper 部署

写库 helper（`helper/plex_mediainfo_helper.py`，纯标准库）需部署在 Plex 所在机器，提供 `/health`、`/dbinfo`、`/busy`、`/write`、`/write_batch` 接口，token 用 `X-PTH-Token` 头校验。详见 [helper/README.md](../../plugins.v2/plextoolbox/helper/README.md)。

## 更新日志

### v0.7.1

- 配置页和数据页统一为五个功能 Tab，并增加常驻运行节奏与运行概况表盘。
- 媒体流信息在播放前补全当前条目及设置的后续集，不再使用播放停止补全和 Cron 全库补全。
- 播前去重窗口由界面配置控制，并仅处理用户已选择的 Plex 媒体库。
- 每 5 分钟检查 Helper，连续失败 3 次后发送一次插件通知，恢复后自动重置。

### v0.7.0

- 新增播前补全：反代拦截 `playQueues` 创建（覆盖「继续观看」点击即播、不经过详情页的场景），起播前同步补全该条目媒体流信息。3 秒等待预算，超时自动放行播放、补全转后台继续；同条目 10 分钟冷却去重。播前仅补当前条目（最快路径），后续集数仍由播放停止后的增量补全接管。

### v0.6.0

- 数据页新增「最近一次补全 / 补全历史」一键清理按钮（后端 `/clear_completion_data` API）。
- 反代稳定性优化：非关键路径（图片转码 / 推荐位等高频轮询）连接失败降为 DEBUG 日志，不再刷屏；连接失败日志不再输出完整堆栈；httpx 连接池 keepalive 上限 20 → 50，过期 30s → 60s。

### v0.5.0

- 新增「目录匹配/刮削」栏：一键对指定 Plex 库取消匹配重读 NFO（支持 dry-run 预览与执行后自动 rematch）；扫描缺封面条目（Plex 无封面或目录仅含 strm）并调用 MoviePilot 刮削生成 NFO + 封面，可选刮削后自动取消匹配让 Plex 重读。

### v0.4.0

- 新增媒体流信息补全自动触发：启用后自动全量、定时全量、播放停止后针对本次条目补全（反代嗅探 / Plex Webhook），带去重窗口与「本集 + 后 N 集」增量窗口。

### v0.3.0

- 由 Plex302ReverseProxy 改造为 PLEX 工具箱：302 反代作为子功能保留，新增 STRM 媒体流信息补全（Emby 数据源 + helper 写库），Vue 联邦前端配置页与数据页。

-------

## 致谢

本插件的 302 直链跳转思路与实现参考了以下项目，特此感谢：

- [chen3861229/embyExternalUrl](https://github.com/chen3861229/embyExternalUrl/blob/main/README.zh-Hans.md) — Emby/Plex 直链重定向方案的先行实现
- [thsrite/MediaLinker](https://github.com/thsrite/MediaLinker/blob/main/README.md) — 媒体服务器直链代理方案
- [DDSRem-Dev/MoviePilot-Plugins](https://github.com/DDSRem-Dev/MoviePilot-Plugins) — MoviePilot 插件生态与 115 直链相关实现

本版本为小 k 自用维护版，感谢以上作者和 MoviePilot 社区。
