# Plex MediaInfo Helper 部署说明

在 **Plex 所在机器（192.168.0.122）** 上运行的本地写库小服务。PlexToolbox 插件负责计算媒体流信息，通过 HTTP 发送到本服务，由本服务在 **数据库文件本地** 安全写入，避免跨网络写 SQLite 损库。

## 前置：找到 Plex 数据库路径

数据库文件名为 `com.plexapp.plugins.library.db`，通常在 Plex 配置目录下：

```
.../Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db
```

Docker 版 Plex 一般把配置目录挂在宿主机某处（如 `/path/to/plex/config`）。找到后，数据库就在该目录下的 `Library/Application Support/.../Databases/`。

## 方式 A：Docker 运行（推荐）

在 192.168.0.122 上，把 Plex 的 **配置目录** 挂进 helper 容器（只需能读写到数据库文件即可）。

### 1. 构建镜像

把 `helper/` 目录（含 `plex_mediainfo_helper.py` 和 `Dockerfile`）拷到 122 机器，然后：

```bash
cd helper
docker build -t plex-mediainfo-helper:latest .
```

### 2. 运行容器

```bash
docker run -d --name plex-mediainfo-helper \
  --restart unless-stopped \
  -p 9001:9001 \
  -v "/path/to/plex/config/Library/Application Support/Plex Media Server/Plug-in Support/Databases":"/db" \
  -e PTH_DB_PATH="/db/com.plexapp.plugins.library.db" \
  -e PTH_TOKEN="换成一个自定义密码" \
  -e PTH_PLEX_URL="http://192.168.0.122:32400" \
  -e PTH_PLEX_TOKEN="你的PlexToken" \
  plex-mediainfo-helper:latest
```

> 把 `/path/to/plex/config` 换成 122 上 Plex 实际的配置目录。
> `PTH_TOKEN` 自定义一个密码，稍后填进插件。
> `PTH_PLEX_TOKEN` 用于「Plex 繁忙时拒绝写入」的检测，可留空则跳过检测。

### 方式 A2：docker compose（更省事）

`helper/` 目录内已提供 `docker-compose.yml`。改好里面的挂载路径与 token 后：

```bash
cd helper
docker compose up -d
```

需要修改的地方：`volumes` 左侧换成 122 上 Plex 实际的 `Databases` 目录，`PTH_TOKEN` 自定义密码，`PTH_PLEX_TOKEN` 填你的 Plex token（留空则跳过繁忙检测）。

### 3. 验证

```bash
# 健康检查（无需 token）
curl http://192.168.0.122:9001/health

# 确认找到数据库（需 token）
curl -H "X-PTH-Token: 换成一个自定义密码" http://192.168.0.122:9001/dbinfo
```

`/dbinfo` 返回 `"success": true` 且 `db_path` 正确即部署成功。

## 方式 B：直接跑 Python（无 Docker）

在能访问数据库文件的那层（LXC 或宿主）：

```bash
PTH_DB_PATH="/实际路径/com.plexapp.plugins.library.db" \
PTH_TOKEN="换成一个自定义密码" \
PTH_PLEX_URL="http://127.0.0.1:32400" \
PTH_PLEX_TOKEN="你的PlexToken" \
python3 plex_mediainfo_helper.py
```

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PTH_HOST` | `0.0.0.0` | 监听地址 |
| `PTH_PORT` | `9001` | 监听端口 |
| `PTH_TOKEN` | 空 | 访问令牌，插件请求需带 `X-PTH-Token`；留空不校验 |
| `PTH_DB_PATH` | 空 | 数据库路径；留空则自动探测 |
| `PTH_BACKUP_KEEP` | `10` | 数据库备份保留份数 |
| `PTH_PLEX_URL` | `http://127.0.0.1:32400` | 本地 Plex 地址（繁忙检测用） |
| `PTH_PLEX_TOKEN` | 空 | Plex token（繁忙检测用）；留空跳过检测 |
| `PTH_REFUSE_WHEN_PLAYING` | `1` | 有播放会话时拒绝写入 |

## 安全说明

- **每次写入前自动备份** 数据库到同目录 `pth_backups/`，保留最近 N 份。
- 写入前检测 Plex 是否在播放/扫描，繁忙则拒绝（可用 `force` 覆盖）。
- 只写 Plex 数据库中 **实际存在的列**，不改表结构。
- 写 Plex 库属于非官方操作，Plex 大版本升级可能改表结构；升级后先用 `/dbinfo` 验证。

## 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（无需 token） |
| GET | `/dbinfo` | 返回数据库路径与候选 |
| GET | `/busy` | 返回 Plex 是否繁忙 |
| POST | `/write` | 写入单个 part 的媒体信息 |
| POST | `/write_batch` | 批量写入 |
