# 115网盘STRM助手 (P115StrmHelper)

> 基于 [DDSRem](https://github.com/DDSRem) 开发的 [115网盘STRM助手](https://github.com/DDSRem-Dev/MoviePilot-Plugins) 本地修复版。
>
> 感谢原作者的杰出贡献！

## 原作者

- **作者**: [DDSRem](https://github.com/DDSRem)
- **原仓库**: [https://github.com/DDSRem-Dev/MoviePilot-Plugins](https://github.com/DDSRem-Dev/MoviePilot-Plugins)
- **原插件**: 115网盘STRM助手 — 115网盘STRM生成一条龙服务

本项目在原作基础上进行了本地修复和功能增强，感谢 DDSRem 的卓越工作！

## 版本

当前版本: **v2.9.1**

### v2.9.1 更新内容
- fix: 适配 p115client 0.0.9.0.2 API 变更 — offline_iter -> clouddownload_iter, offline_add_urls -> clouddownload_task_add_urls
- fix: 补全上游 p115client 0.0.9.0.2 的 valid wheel（原文件损坏）
- fix: 补全本地安装时缺失的 core/database/db_manager/dist 目录

### v2.9.0 更新内容
- fix: 去除 pan_transfer 与 monitor_life 的关联逻辑，修复 HTTP 405 错误
- fix: 修复文件双重 base64 编码问题导致乱码

### v2.8.49 更新内容
- fix: 修复扫码登录 — 绕过 `login_qrcode()` 直接请求带 uid 的官方二维码地址
- fix: 修复全量同步 — 切换 Python 模式，解决 Rust Core v0.1.5 过滤 bug
- fix: 修复 syntax error — `full/__init__.py` 括号不匹配

## 说明

本仓库仅包含 P115StrmHelper 插件，如需完整插件市场请访问原作者仓库。