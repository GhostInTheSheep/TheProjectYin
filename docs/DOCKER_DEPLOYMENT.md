## TheProjectYin - Docker 部署指南

本指南提供使用 Docker/Compose 部署本项目后端（含 MCP 工具）的步骤与意义说明。前端 Electron/Vite 应用建议在开发机本地运行；生产环境主要容器化后端服务。

---

### 1. 前置准备
- 安装 Docker 与 Docker Compose（或 Docker Desktop，含 compose v2）
- 放行端口：默认 12393（Web/API/WebSocket/媒体）
- 关键文件：`conf.yaml`、`mcp_servers.json`、`src/solvia_for_chat/*`

- 意义：统一环境，避免“只在我机上能跑”。

---

### 2. 数据与配置挂载规划
- 宿主机目录：
  - `./ads/` 广告视频
  - `./videos/` 洗衣机教程视频
  - `./characters/` 角色/配置（可选）
  - `./conf.yaml` 主配置（挂载便于热更新）
  - `./mcp_servers.json` MCP 列表（挂载便于增删工具）
- 意义：容器无状态、数据持久化、升级回滚安全。

---

### 3. 示例 Dockerfile（后端）
将以下内容保存为项目根目录 `Dockerfile`。

```Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY . ${APP_HOME}

# 推荐提供 requirements.txt：
# RUN pip install -r requirements.txt
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] websockets loguru pydantic pyyaml anyio \
    mcp mcp-server \
    httpx

EXPOSE 12393

CMD ["python", "-m", "src.solvia_for_chat.server"]
```

- 意义：依赖随镜像分发，环境一致、发布快速。

---

### 4. 示例 docker-compose.yml
将以下内容保存为项目根目录 `docker-compose.yml`。

```yaml
version: "3.9"
services:
  backend:
    build: .
    container_name: theprojectyin-backend
    restart: unless-stopped
    ports:
      - "12393:12393"
    environment:
      PYTHONPATH: "."
    volumes:
      - ./conf.yaml:/app/conf.yaml:ro
      - ./mcp_servers.json:/app/mcp_servers.json:ro
      - ./ads:/app/ads:ro
      - ./videos:/app/videos:ro
      # 可选：自定义角色/配置
      - ./characters:/app/characters:ro
```

- 意义：一条命令完成构建与启动；配置热更无需重建镜像。

---

### 5. MCP 服务器配置要点
内置 MCP：`laundry-assistant`、`advertisement-server`、`weather-server`、`time`。
确保 `mcp_servers.json` 可在容器内执行，例如：

```json
{
  "mcp_servers": {
    "laundry-assistant": {
      "command": "python",
      "args": ["-m", "src.solvia_for_chat.mcpp.laundry_server", "--videos-dir=videos"],
      "env": { "PYTHONPATH": "." },
      "timeout": 30
    },
    "advertisement-server": {
      "command": "python",
      "args": ["-m", "src.solvia_for_chat.mcpp.advertisement_server", "--ads-dir=ads"],
      "env": { "PYTHONPATH": "." },
      "timeout": 30
    },
    "weather-server": {
      "command": "python",
      "args": ["-m", "src.solvia_for_chat.mcpp.weather_server"],
      "env": { "PYTHONPATH": "." },
      "timeout": 30
    },
    "time": {
      "command": "python",
      "args": ["-m", "src.solvia_for_chat.mcpp.time_server", "--timezone=Asia/Tokyo"],
      "env": { "PYTHONPATH": "." },
      "timeout": 30
    }
  }
}
```

同时在 `conf.yaml` 启用：

```yaml
# 片段：character_config.agent_config.agent_settings.basic_memory_agent
use_mcpp: True
mcp_enabled_servers: ["laundry-assistant", "advertisement-server", "time", "weather-server"]
```

- 意义：MCP 由后端托管为子进程，动态拉起、易扩展。

---

### 6. 启动与验证
- 构建并启动：`docker compose up -d --build`
- 查看日志：`docker compose logs -f backend`
- 验证：访问 `http://<host>:12393/`；前端/客户端连 `ws://<host>:12393/client-ws`
- 日志中应见：`Starting and connecting to server 'weather-server'...`/`Successfully connected ...`

- 意义：快速定位端口、网络、权限类问题。

---

### 7. 常见问题（FAQ）
- 端口占用：改映射为 `8080:12393` 等。
- 媒体不可访问：确认卷挂载与 `conf.yaml.system_config.media_server` 目录一致。
- MCP 未加载：
  - `conf.yaml` 的 `mcp_enabled_servers` 是否包含 `time`、`weather-server`；
  - `mcp_servers.json` 的命令能否在容器内执行（推荐 `command: python` + `PYTHONPATH`）。
- 无外网：`weather-server` 依赖 Open‑Meteo，需代理或禁用。

---

### 8. 运维操作
- 停止：`docker compose down`
- 重启：`docker compose restart backend`
- 更新镜像并重启：`docker compose pull && docker compose up -d`
- 进入容器：`docker compose exec backend bash`

- 意义：标准化运维流程，降低失误风险。

---

### 9. 部署收益
- 一致性：开发/测试/生产环境一致，减少环境差异。
- 快速恢复：镜像与 Compose 可版本化，回滚简单。
- 可移植：不同云/物理机一键启动。
- 可观测：日志/健康/端口统一管理。
- 可扩展：MCP 工具可随时增删（时间、天气等）。

---

如需生成 `requirements.txt`、健康检查、或生产型多阶段 Dockerfile（含非 root 运行、最小化攻击面），告诉我你的目标环境与限制即可。
