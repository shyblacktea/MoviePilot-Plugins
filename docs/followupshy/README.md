# 续作跟进魔改版

`FollowUpShy` 是原版 `FollowUp` 的独立 V3 适配版，用于检查媒体库和订阅历史中的电影、电视剧是否有即将上映的续作，并通过通知按钮追加订阅。

- 插件 ID：`FollowUpShy`
- 当前版本：`0.0.2`
- 插件目录：`plugins.v3/followupshy/`
- 适用版本：MoviePilot V3（`>=3.0.0`）
- 作者：`Attente, shyblacktea`

## 主要功能

- 保留原版 JSON 配置页和续作跟进流程。
- 支持媒体库条目、订阅列表和订阅历史检查。
- 使用 `media_source + media_id` 适配 MoviePilot V3 数据模型。
- 仅处理 TMDB 媒体身份，避免把其他来源 ID 当作 TMDB ID。
- 通过通知按钮追加订阅或忽略后续提醒。
- 已存在订阅的续作不再发送重复通知，仅提醒尚未订阅的媒体。

## 配置说明

- `启用插件`：启用续作跟进。
- `执行周期`：使用 Cron 表达式定期检查。
- `立即运行一次`：保存配置后立即执行一次。
- `检查订阅历史`：将订阅历史纳入检查范围。
- `媒体库`：选择需要检查的媒体库。
- `提前提醒天数`：上映或播出前的提醒范围。
- `系列检查年限`：超过年限的系列不再跟进。

## 兼容修复

- `Subscribe.tmdbid` 改为 `Subscribe.media_id`，并校验 `media_source=TMDB`。
- `SubscribeHistory.tmdbid` 改为 `SubscribeHistory.media_id`。
- `MediaServerItem.tmdb_id/tmdbid` 改为 `media_id`，并校验 `media_source=TMDB`。
- 识别调用改为 V3 的 `media_source + media_id` 参数。

## 安全边界

- 本插件使用独立配置前缀 `followupshy_`，不覆盖原版 `FollowUp` 配置。
- 本地改造阶段不卸载、不停用原版插件。
- 插件不会自动下载资源，只有用户点击通知按钮后才追加订阅。

## 版本记录

### v0.0.2

- 已存在订阅的电视剧、电影续作不再发送重复通知。
- 按 TMDB `media_source + media_id + 类型` 精确判断订阅状态。
- 仅向尚未订阅的系列发送“是否订阅该系列的最新作品？”通知。

### v0.0.1

- 从原版 `FollowUp` 独立改造为 `FollowUpShy`。
- 保留 JSON 配置页和原有续作跟进功能。
- 适配 MoviePilot V3 的媒体身份字段和识别接口。
