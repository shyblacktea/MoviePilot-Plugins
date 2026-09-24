# 手动订阅助手

`ManualSubscribeAssistantShy` 是面向 MoviePilot 的手动订阅插件：抓取多来源媒体候选，由用户确认后手动创建 MoviePilot 订阅。

- 插件 ID：`ManualSubscribeAssistantShy`
- 当前版本：`0.1.1`
- 插件目录：`plugins.v3/manualsubscribeassistantshy/`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 作者：`shyblacktea`

## 工作流程

```text
抓取多来源候选 → 去重和筛选 → 用户确认媒体 → 创建订阅 → 管理暂停、恢复或退订
```

抓取阶段只保存候选，不会因为抓取到媒体就自动创建订阅。


## 主要功能

### 多来源候选

- 支持 Mikan、豆瓣、猫眼、热门媒体和 Netflix 等来源。
- 支持来源级配置、定时抓取和手动立即运行。
- 支持候选去重、过滤、状态筛选和运行状态查看。
- 支持跳转 TMDB / Bangumi 进行媒体确认。

### 手动订阅管理

- 用户确认后创建 MoviePilot 订阅。
- 支持查看待确认、已订阅、被过滤和未识别候选。
- 支持暂停、恢复和退订本插件创建的订阅。
- 清空候选不会删除 MoviePilot 实际订阅，也不会清空订阅历史。

## 配置说明

- `来源配置`：设置各媒体来源的启用状态和抓取参数。
- `过滤器`：限制候选类型、分类、年份或其他来源字段。
- `定时任务`：设置自动抓取周期；非法 Cron 会被拒绝或回退默认值。
- `立即运行一次`：提交一次性抓取任务，执行后自动复位开关。
- `清空订阅管理候选`：只清空候选数据，不修改真实订阅。

具体字段由 Vue 页面根据来源定义动态展示。

## 数据和安全边界

- 插件抓取结果首先进入自身候选数据，不等同于 MoviePilot 订阅。
- 创建订阅必须经过用户确认。
- 退订、暂停和恢复会影响 MoviePilot 实际订阅状态，请确认目标后操作。
- 来源接口、代理和 Cookie 等配置应按来源要求填写，不在日志中输出敏感值。
- 插件停止时应释放调度任务和来源客户端。

## 版本记录

### v0.1.1

- 修复清空历史误指向旧版 `history` 数据的问题。
- 清空操作现在只处理订阅管理候选。
- 候选状态筛选改为互斥单选。

### v0.1.0

- 重做多来源抓取、动态配置、过滤器、候选筛选和订阅管理界面。
- 抓取只保存候选，改为用户确认后手动创建订阅。

### v0.0.1

- 支持 Mikan 季番抓取、Bangumi/TMDB 跳转和手动创建订阅。

## 说明

本插件负责“发现候选并协助人工订阅”，不替代 MoviePilot 原生订阅搜索和下载流程。

## 发布信息

- 插件 ID：`ManualSubscribeAssistantShy`
- 插件目录：`plugins.v3/manualsubscribeassistantshy/`
- 当前版本：`0.1.1`
- 适用版本：MoviePilot V3（`>=3.0.0`）

## 致谢

- 原作者：[Aqr-K](https://github.com/Aqr-K)
- 原仓库：[Aqr-K/MoviePilot-Plugins](https://github.com/Aqr-K/MoviePilot-Plugins)

本版本基于原作者的自动订阅助手改造，感谢原作者和 MoviePilot 社区。