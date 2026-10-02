# CTMDbA 魔改版

`CureTMDbAnimeShy` 用于修正 TMDB 将部分番剧合并为一季时产生的季信息问题，并通过独立的 CureTMDb 服务提供元数据修正能力。

- 插件 ID：`CureTMDbAnimeShy`
- 当前版本：`0.0.4`
- 插件目录：`plugins.v3/curetmdbanimeshy/`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 作者：`Attente, shyblacktea`

## 工作流程

```text
读取配置 → 启动独立 CureTMDb 服务 → 优先匹配 CureTMDb 规则 → 默认依次尝试 TVDB、Bangumi → 未命中时使用 TMDB 原始数据
```

## 主要功能

### 季信息修正

- 处理 TMDB 将多季番剧合并为一季的场景。
- 优先使用 TVDB 作为拆分依据，提升多季番剧的季号判断准确性。
- 支持按播出窗口推断季号。
- 支持集数越界宽限和改写阈值控制。
- 通过独立插件 ID 与原版 `CureTMDbAnime` 区分。

### 独立服务

- 可配置服务监听端口，默认 `8632`。
- 支持配置 Bangumi API 地址及是否使用 MoviePilot 代理。
- 支持配置修正数据源。
- 服务由插件生命周期负责启动和停止。

## 配置说明

- `启用插件`：是否启用插件及其后台服务，默认关闭。
- `端口`：独立服务监听端口，默认 `8632`。
- `启用元数据修正`：是否执行季信息修正，默认开启。
- `按播出窗口推断季号`：是否在缺少明确季信息时按播出窗口推断。
- `集数越界宽限`：允许的集数偏差范围，默认 `2`。
- `改写阈值`：触发元数据改写的阈值，默认 `16`。
- `Bangumi API URL`：Bangumi API 地址，默认 `https://api.bgm.tv`。
- `Bangumi 使用代理`：是否使用 MoviePilot 网络代理，默认开启。
- `来源`：修正数据源地址。

## 数据和安全边界

- 插件配置通过 MoviePilot 插件配置接口保存。
- 服务端口必须避免与其他进程冲突。
- 外部数据源不可用时不应把不完整结果当作可靠季信息。
- 修改范围限于媒体元数据修正，不负责下载、订阅或文件整理。
- 插件停止或重载时应释放独立服务和相关进程。

## 版本记录

### v0.0.4

- 同步、异步识别结束后显式调用季集修正，不再依赖旧分类方法和调用栈局部变量。
- 兼容当前宿主结构化季信息、下一集信息，保留旧版字典支持。
- 异步识别中的同步网络修正在线程执行，避免阻塞事件循环。

### v0.0.3

- 普通 API 请求、分季尝试、无需拆分和逐季明细降为 DEBUG，保留错误、警告、数据源选中和实际季集修正结果。
- 移除配套服务的 debug 启动参数，查询 URL 中的凭据参数在转发日志前自动脱敏。
- 保留上游已有的分季逻辑、TVDB/Bangumi/TMDB 缓存策略，不改变媒体识别行为。

### v0.0.2

- 适配上游 CureTMDbAnime `2.4.0` 的 TVDB 拆分逻辑。
- 内置二进制版本更新至 `1.4.0`。

### v0.0.1

- 迁移到 MoviePilot V3 专用实现。
- 使用 `app.sdk.*` 体系接入配置、媒体、网络和日志能力。
- 使用独立插件 ID，避免与原版插件冲突。

## 说明

本插件适合已经确认存在 TMDB 季信息合并问题的番剧。首次启用前请确认端口、Bangumi API 和修正数据源配置。

## 发布信息

- 插件 ID：`CureTMDbAnimeShy`
- 插件目录：`curetmdbanimeshy`
- 当前版本：`0.0.4`
- Release 标签：`CureTMDbAnimeShy_v0.0.4`
- Release 安装包：`curetmdbanimeshy_v0.0.4.zip`
- [下载发布版本](https://github.com/shyblacktea/MoviePilot-Plugins/releases/tag/CureTMDbAnimeShy_v0.0.4)

## 致谢

感谢原作者 Attente 及 [wikrin/MoviePilot-Plugins](https://github.com/wikrin/MoviePilot-Plugins)、[wikrin/CureTMDbAnime](https://github.com/wikrin/CureTMDbAnime) 提供的插件和分季代理服务，以及 MoviePilot 社区提供的插件机制。