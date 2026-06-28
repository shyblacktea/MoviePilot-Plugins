# shyblacktea MoviePilot-Plugins

基于 MoviePilot 插件市场社区的二次修复与增强版插件集合。

## 插件列表

### P115StrmHelper — 115网盘STRM助手

- **版本**: v2.8.49
- **原作者**: [DDSRem](https://github.com/DDSRem)
- **原仓库**: [DDSRem-Dev/MoviePilot-Plugins](https://github.com/DDSRem-Dev/MoviePilot-Plugins)
- **说明**: 115网盘STRM生成一条龙服务（小k自用版）。

修复内容：
- 修复扫码登录 — 绕过 `login_qrcode()` 直接请求带 uid 的官方二维码地址
- 修复全量同步 — 切换 Python 模式，解决 Rust Core v0.1.5 过滤 bug
- 修复 syntax error — `full/__init__.py` 括号不匹配

---

### CleanInvalidPlugin — 清理无效插件

- **版本**: v1.1
- **原作者**: [cddjr](https://github.com/cddjr)
- **原仓库**: [jxxghp/MoviePilot-Plugins](https://github.com/jxxghp/MoviePilot-Plugins)
- **说明**: 删除或重新安装数据库中无法安装的插件记录。（小k自用版）

新增功能：
- 新增重新安装功能，可选择清理或从市场重装无效插件

---

## 致谢

感谢以上所有原作者的杰出贡献，本仓库仅在其基础上进行本地修复和功能增强。
