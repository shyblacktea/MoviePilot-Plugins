# 手动订阅助手

`ManualSubscribeAssistantShy` 是仅面向 MoviePilot V3 的插件：抓取多来源媒体候选，由用户确认后手动创建 MoviePilot 订阅，并在主页侧栏提供入口。

## 主要功能

- 抓取 Mikan、豆瓣、猫眼、热门媒体和 Netflix 等来源的候选。
- 支持候选筛选、TMDB/Bangumi 跳转和用户确认后的手动订阅。
- 支持手动订阅记录的暂停、恢复和退订。
- “订阅管理”显示抓取候选，“订阅历史”显示本插件创建的 MoviePilot 订阅。

## 更新日志

### 0.1.2

- 新增主页侧栏入口，可从主页直接打开插件。
- 插件显示名称统一为“手动订阅助手”，移除“魔改版”字样。

### 0.1.1

- 修复“订阅配置 → 全局设置 → 清空历史记录”误指向旧版 `history` 数据的问题。
- 该选项现在明确为“清空订阅管理候选”，只清空 `candidates`，不删除 MoviePilot 实际订阅，也不影响订阅历史。
- 保存配置后一次性开关仍会自动复位。

### 0.1.0

- 重做多来源抓取、动态配置、过滤器、运行状态、候选筛选和订阅管理界面。
- 抓取只保存候选，改为用户确认后手动创建 MoviePilot 订阅。

## 发布信息

- 插件 ID：`ManualSubscribeAssistantShy`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 插件目录：`plugins.v3/manualsubscribeassistantshy/`
- 当前版本：`0.1.2`
- Release Tag：`ManualSubscribeAssistantShy_v0.1.2`
- Release 资产：`manualsubscribeassistantshy_v0.1.2.zip`
- 本插件本次仅发布 V3，不提供 V2 兼容版本。
