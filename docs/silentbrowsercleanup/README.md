# 静默清理残留浏览器

`SilentBrowserCleanup` 由 MoviePilot 内部调度器清理过期的 Playwright/Chromium 进程，不发送 Telegram 或其他通知。

- 插件 ID：`SilentBrowserCleanup`
- 当前版本：`1.0.0`
- 插件目录：`plugins.v3/silentbrowsercleanup/`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 作者：`shyblacktea`

## 工作流程

```text
Cron 触发 → 识别过期浏览器进程 → 按进程树安全终止 → 记录结果 → 不发送通知
```

## 主要功能

- 定时清理残留 Chromium / Playwright 进程。
- 识别父子进程关系，尽量避免留下孤儿进程。
- 通过 MoviePilot 内部调度器执行，不依赖 Agent 广播链路。
- 关闭插件后停止自身调度服务。

## 配置说明

- `启用插件`：是否启用清理服务，默认开启。
- `Cron`：清理周期，默认 `0 * * * *`，即每小时执行。

插件无独立前端配置页，配置通过插件默认表单模型提供。

## 数据和安全边界

- 只应处理可确认属于 Playwright/Chromium 的过期残留进程。
- 不应终止正在被有效浏览器任务使用的进程。
- 插件不发送通知，不负责清理下载任务、媒体文件或 MoviePilot 历史。
- 修改 Cron 前应确认不会与其他浏览器维护任务形成并发高峰。

## 版本记录

### v1.0.0

- 新增基于 MoviePilot 内部调度器的残留 Chromium 进程清理。
- 绕过 Agent 广播链路，执行时不发送 Telegram 通知。

## 说明

这是后台资源维护插件。若浏览器任务异常频繁退出，应先排查调用方和系统资源，不要仅靠提高清理频率解决。

## 发布信息

- 插件 ID：`SilentBrowserCleanup`
- 插件目录：`plugins.v3/silentbrowsercleanup/`
- 当前版本：`1.0.0`

## 致谢

感谢 MoviePilot 社区提供调度器和插件生命周期能力。