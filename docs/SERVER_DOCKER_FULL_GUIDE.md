## TheProjectYin - 服务器 Docker 全过程部署指南

本指南提供从零到上线的完整 Docker/Compose 部署流程，覆盖镜像构建、配置挂载、MCP 工具、健康检查、反向代理与日常运维。适用于 Linux 服务器（Debian/Ubuntu/CentOS 等）。

说明：本项目“后端服务（FastAPI+WS）”与“主前端应用（frontend/Frontend-AI）”是分离的。推荐生产方案：单个 docker compose 管理多容器，由 Caddy 作为边缘代理统一提供 HTTPS 与路由（支持同时托管多个前端与后端项目）。下文优先给出“Compose + Caddy”的推荐路径，并保留“主机 Nginx”作为可选替代。

---

### 0) 前置条件与目标目录

- 服务器已安装：
  - Docker 与 Docker Compose（或 Docker Desktop，带 compose v2）
  - 可用的公网端口（默认后端监听 12393）
- 推荐把项目放在：
  - `/opt/codes/TheProjectYin`（下文以此为例）
- 必备文件：
  - `conf.yaml`（主配置）
  - `mcp_servers.json`（MCP 工具列表）
  - 资源目录：`ads/`、`videos/`
- 可选的密钥（通过环境变量注入）：
  - `OPENAI_API_KEY`（LLM/ASR）
  - `FISH_API_KEY`（Fish TTS）
  - 其他如代理等

进入项目目录：
```bash
cd /opt/codes/TheProjectYin
```

文件创建位置快速参考（路径都基于上述项目根目录）：
```text
/opt/codes/TheProjectYin/
  ├── Dockerfile                       # 后端镜像用（本文件第 2 节给出内容）
  ├── docker-compose.yml               # 编排文件（第 3/8.2 节给出示例）
  ├── conf.yaml                        # 你的后端配置
  ├── mcp_servers.json                 # MCP 列表
  ├── caddy/
  │   └── Caddyfile                    # Caddy 反代配置（第 8.2 节）
  └── frontend/Frontend-AI/
      ├── Dockerfile                   # 前端多阶段构建（第 9.1 节）
      └── nginx.conf                   # 前端容器内 Nginx（第 9.1 节）
```
如需先创建目录与空文件：
```bash
mkdir -p /opt/codes/TheProjectYin/caddy /opt/codes/TheProjectYin/frontend/Frontend-AI
touch /opt/codes/TheProjectYin/Dockerfile \
      /opt/codes/TheProjectYin/docker-compose.yml \
      /opt/codes/TheProjectYin/caddy/Caddyfile \
      /opt/codes/TheProjectYin/frontend/Frontend-AI/Dockerfile \
      /opt/codes/TheProjectYin/frontend/Frontend-AI/nginx.conf
```

---

### 1) 准备配置文件

1.1 `conf.yaml`（关键片段）
```yaml
system_config:
  host: 0.0.0.0         # 容器内监听所有网卡
  port: 12393
  media_server:
    use_absolute_paths: true
    base_directory: '/app'   # 容器内项目工作目录

character_config:
  agent_config:
    agent_settings:
      basic_memory_agent:
        use_mcpp: true
        mcp_enabled_servers: ["laundry-assistant", "advertisement-server", "time", "weather-server"]
```

1.2 `mcp_servers.json`（容器内用 `python` 执行工具模块）
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

---

### 2) 编写 Dockerfile（后端/生产版）

保存位置：`/opt/codes/TheProjectYin/Dockerfile`

将以下内容保存为项目根目录 `Dockerfile`（使用完整依赖 requirements.linux.txt，构建即“最终版”）：
```Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app \
    PYTHONPATH=/app

WORKDIR ${APP_HOME}

# 常用运行依赖（证书、ffmpeg 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖清单以利用缓存
COPY requirements.linux.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝项目代码
COPY . ${APP_HOME}

EXPOSE 12393

# 健康检查（可被 compose 覆盖）
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:12393/web-tool', timeout=3)" || exit 1

# 后端入口
CMD ["python", "run_server.py"]
```

说明：
- 使用完整的 `requirements.linux.txt`，与开发环境一致，避免漏依赖；镜像更大但更稳定。
- 若你的场景不需要本地推理，可改为 `requirements.linux.notorch.txt` 以缩小镜像体积。

---

### 3) 编写 docker-compose.yml（后端）

保存位置：`/opt/codes/TheProjectYin/docker-compose.yml`

将以下内容保存为项目根目录 `docker-compose.yml`：
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
      # 根据需要启用以下密钥
      # OPENAI_API_KEY: "sk-xxx"
      # FISH_API_KEY: "xxx"
    volumes:
      - ./conf.yaml:/app/conf.yaml:ro
      - ./mcp_servers.json:/app/mcp_servers.json:ro
      - ./ads:/app/ads:ro
      - ./videos:/app/videos:ro
      # 可选：持久化服务运行中产生的音频等缓存
      - ./cache:/app/cache
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS -o /dev/null http://localhost:12393/web-tool || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 15s
```

说明：
- 健康检查访问 `/web-tool`（该路由会 302 重定向至内置 Web 工具页面），2xx/3xx 视为正常。
- `ads/`、`videos/` 建议挂载为只读；`cache/` 可持久化（便于分析/排障/节省二次生成代价）。

---

### 4) 构建与启动（后端）

```bash
cd /opt/codes/TheProjectYin
docker compose up -d --build
docker compose logs -f backend
```

预期日志关键点：
- 出现 `Server context initialized successfully.`（服务初始化成功）
- 如启用 MCP，会看到：
  - `Starting and connecting to server 'xxx'...`
  - `Successfully connected to server 'xxx'.`

访问：
- API/WS：`ws://<服务器IP或域名>:12393/client-ws`
- 内置 Web 工具演示：`http://<服务器IP或域名>:12393/web-tool`

---

### 5) 日常运维（后端）

- 查看日志：
```bash
docker compose logs -f backend
```

- 重启服务：
```bash
docker compose restart backend
```

- 停止/移除：
```bash
docker compose down
```

- 进入容器：
```bash
docker compose exec backend bash
```

- 升级部署（拉代码、重建镜像、滚动替换）：
```bash
git pull
docker compose up -d --build
```

- 备份（最关键的是配置与媒体）：
  - `conf.yaml`、`mcp_servers.json`
  - `ads/`、`videos/`
  - 如有需要，备份 `cache/`

---

### 6) 常见问题排查（后端 FAQ）

- 端口冲突：修改映射为 `8080:12393`。
- 无法访问媒体：确认 `conf.yaml.system_config.media_server.base_directory` 为 `/app`，并且 `ads/`、`videos/` 已正确挂载。
- MCP 未加载：
  - `conf.yaml` 的 `use_mcpp: true` 且 `mcp_enabled_servers` 包含目标服务器；
  - `mcp_servers.json` 的 `command` 使用 `python` 且 `env.PYTHONPATH: "."`；
  - 查看日志是否有超时或命令错误。
- 无外网环境：`weather-server` 依赖外部 API，离线环境可去掉该 MCP 服务。
- 看到异步关闭告警（anyio/mcp 清理阶段）：
  - 不影响功能，可忽略；或升级依赖：`pip install -U mcp anyio sniffio`。

---

### 7) 可选加固与优化（后端）

---

### 8) 前端部署（Frontend-AI）

主前端在 `frontend/Frontend-AI`，建议“前后端分离、两个容器”部署。

优先推荐：使用 Caddy 统一反向代理与自动 HTTPS（见 8.2）。如不使用 Caddy，可在前端容器内使用 Nginx 反代到后端（见 8.1），或在主机层使用 Nginx（见第 10 节）。

8.1 多阶段前端 Dockerfile（保存到 `frontend/Frontend-AI/Dockerfile`）
保存位置：`/opt/codes/TheProjectYin/frontend/Frontend-AI/Dockerfile`
```Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build:web

FROM nginx:alpine
# 静态文件
COPY --from=build /app/dist/web /usr/share/nginx/html

# 可选：覆盖默认 Nginx 配置，反代后端 API/WS（容器名 backend:12393）
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

示例 `nginx.conf`（可选，使用前端容器内 Nginx 反代）
保存位置：`/opt/codes/TheProjectYin/frontend/Frontend-AI/nginx.conf`
```nginx
server {
  listen 80;

  # 静态站点
  root   /usr/share/nginx/html;
  index  index.html;

  # SPA 路由
  location /assets/ {
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    try_files $uri =404;
  }
  location = /index.html { add_header Cache-Control "no-store" always; }
  location / { add_header Cache-Control "no-store" always; try_files $uri $uri/ /index.html; }

  # 反向代理到后端容器（compose 内服务名为 backend）
  set $backend http://backend:12393;
  location /client-ws { proxy_pass $backend; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; }
  location /tts-ws    { proxy_pass $backend; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; }
  location /api/      { proxy_pass $backend; }
  location /videos/   {
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    proxy_pass $backend;
  }
  location /ads/      {
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    proxy_pass $backend;
  }
}
```

8.2 推荐（首选）：单 compose + Caddy 统一反代（支持多项目单机共存）
含义：Caddy 自动签发与续期证书（Let's Encrypt），以域名将前端/后端路由到对应容器。你可以在同一台机器上用不同子域托管多个项目。

新增 `caddy/Caddyfile`（项目根相对路径 `./caddy/Caddyfile`）：
保存位置：`/opt/codes/TheProjectYin/caddy/Caddyfile`
```caddy
jtlai.top {
  encode zstd gzip

  # 为媒体与广告提供长缓存（可按需调整 TTL）
  @media path /videos/* /ads/* /live2d-models/* /avatars/* /bg/* /assets/*
  header @media Cache-Control "public, max-age=31536000, immutable"

  @backend path /client-ws /tts-ws /api/* /videos/* /ads/* /web-tool* /web_tool* /live2d-models/* /avatars/* /bg/* /cache/*
  reverse_proxy @backend backend:12393

  reverse_proxy frontend:80
}
```

更新根 `docker-compose.yml`（加入 caddy 服务）：
```yaml
version: "3.9"

services:
  backend:
    build: .
    container_name: theprojectyin-backend
    restart: unless-stopped
    environment:
      PYTHONPATH: "."
      # OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "12393:12393"   # 可选暴露，便于本机调试；生产可去掉，仅供 caddy 内部访问
    volumes:
      - ./conf.yaml:/app/conf.yaml:ro
      - ./mcp_servers.json:/app/mcp_servers.json:ro
      - ./ads:/app/ads
      - ./videos:/app/videos
      - ./models:/app/models
      - ./web_tool:/app/web_tool:ro

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: theprojectyin-frontend
    restart: unless-stopped

  caddy:
    image: caddy:2-alpine
    container_name: edge-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend
      - backend

volumes:
  caddy_data:
  caddy_config:
```

含义：
- Caddy 监听 80/443，自动 HTTPS，按路径反代给 `frontend` 与 `backend` 容器。
- 多项目时，按域名加块即可，无需在主机层重复装/配 Nginx。
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
      # OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./conf.yaml:/app/conf.yaml:ro
      - ./mcp_servers.json:/app/mcp_servers.json:ro
      - ./ads:/app/ads
      - ./videos:/app/videos
      - ./models:/app/models
      - ./web_tool:/app/web_tool:ro

  frontend:
    build:
      context: ./frontend/Frontend-AI
      dockerfile: Dockerfile
    container_name: theprojectyin-frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "8080:80"   # 如需主机 Nginx 做 HTTPS，建议改为 8080:80，避免与主机 80 冲突
```

访问方式：浏览器访问 `https://your.domain.com`（Caddy 自动签发证书）；前端/后端路径由 Caddy 自动路由。

验证缓存头（示例）：
```bash
curl -I https://your.domain.com/ads/your_ad.mp4 | grep -i cache-control
curl -I https://your.domain.com/videos/your_video.mp4 | grep -i cache-control
```

8.3 前端构建/更新
```bash
cd frontend/Frontend-AI
docker build -t theprojectyin-frontend:latest .
cd -
docker compose up -d --build frontend
```

8.4 关于“一容器同时托管前端和后端”
- 可行但不推荐：将 `frontend/Frontend-AI/dist/web` 复制进后端容器并由后端 `server.py` 挂载 `frontend/` 作为根静态目录。
- 缺点：耦合发布与回滚、静态缓存策略受限。生产建议分离两个容器或使用外部 Nginx/CDN 托管静态资源。

---

### 8.5 Live2D 零形变显示参数（前端已内置支持）

目的：在不同 LED 物理分辨率下，确保 Live2D 画面“0 形变”。通过 URL 查询参数控制“设计分辨率舞台”和等比策略：

- 参数：
  - `dw, dh`：设计分辨率（建议等于该屏物理像素，例如竖屏 320×880）
  - `fit`：`contain`（等比完整不裁切，可能黑边）或 `cover`（等比铺满无黑边，居中裁切）

- 示例（竖屏 320×880）：
  - `https://your.domain.com/?dw=320&dh=880&fit=cover`

- 其它常用分辨率：
  - P2 室内：`320x600`、`320x880`、`320x960`
  - P3 室外：`213x400`、`213x586`、`213x640`

提示：树莓派 kiosk 启动时建议附加 `--force-device-scale-factor=1 --high-dpi-support=1 --disable-pinch`，并用 `xrandr -o right` 竖屏输出，以保证 1 CSS 像素≈1 物理像素，避免额外缩放干扰。

---

### 8.6 Caddy 静态资源/MIME 小贴士（WASM/ONNX）

如前端静态由 Caddy 直接托管，默认会根据扩展名提供正确的 `Content-Type`。若通过反代访问后端静态，遇到 VAD/ONNX 资源 MIME 报错，可在 Caddyfile 中补充：

```caddyfile
@wasm path *.wasm
header @wasm Content-Type application/wasm

@onnx path *.onnx
header @onnx Content-Type model/onnx
```

WebSocket 透传：Caddy 对 `Upgrade`/`Connection` 头自动处理，一般无需额外配置；只需将 `/client-ws`、`/tts-ws` 路由至后端即可。

---

### 9) 启动步骤（后端 + 前端）

9.1 首次启动（两容器）
```bash
# 在项目根目录
docker compose up -d --build backend
docker compose logs -f backend | sed -n '1,120p'

# 验证后端健康
curl -I http://127.0.0.1:12393/web-tool
curl -I http://127.0.0.1:12393/api/ads

# 启动前端容器（如采用上面的前端 Dockerfile）
docker compose up -d --build frontend
docker compose logs -f frontend | sed -n '1,80p'

# 浏览器访问前端（容器80口）
echo "Open: http://<服务器IP或域名>/"
```

9.2 常用命令
```bash
# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启
docker compose restart backend
docker compose restart frontend

# 停止/删除
docker compose down

# 仅后端热更新（重新构建并起）
docker compose up -d --build backend
```

9.3 验证要点
- 后端日志应包含：`Server context initialized successfully.`、`Starting server on ...`。
- 启用 MCP 时，会看到 `Starting and connecting to server 'xxx'...` 与 `Successfully connected ...`。
- 前端打开后，网络面板中 `/client-ws`、`/tts-ws` 应连接到后端（若采用前端容器内 Nginx 反代，则目标为 `backend:12393`）。

9.4 故障排查
- 容器马上退出且退出码 0：多数是入口脚本没跑到主循环，检查 `PYTHONPATH` 与 `conf.yaml` 挂载路径。
- 健康检查失败：确认端口映射与服务启动成功；尝试 `docker compose run --rm backend bash -lc "python run_server.py --verbose"` 查看详细异常。
- 前端打不开或空白：检查前端容器 Nginx 日志、`nginx.conf` 路由与反代目标服务名是否为 `backend:12393`。

---

### 10) HTTPS 部署（可选替代：主机 Nginx + Let's Encrypt）

目的：对外只开放 443（和 80 用于证书校验/跳转），由主机 Nginx 终止 TLS，再反代到前端容器 8080。外部世界完全通过 HTTPS 访问，前端容器继续与后端容器通信。

前提：第 8.2 已将前端容器映射为 `8080:80`。

10.1 安装 Nginx 与 Certbot（示例命令，按你的发行版调整）
```bash
sudo dnf -y install nginx certbot python3-certbot-nginx || \
sudo apt-get update -y && sudo apt-get install -y nginx certbot python3-certbot-nginx
sudo systemctl enable --now nginx
```
含义：安装并启动主机 Nginx，为后续签发证书与反向代理做准备。

10.2 配置主机 Nginx（HTTPS 反代到前端容器 8080）
创建 `/etc/nginx/sites-available/theprojectyin.conf`（不同发行版路径可能是 `/etc/nginx/conf.d/`）：
```nginx
server {
  listen 80;
  server_name your.domain.com;
  # 先给 80 放通，便于 ACME 校验；后续签好证书再自动跳转
  location /.well-known/acme-challenge/ { root /var/www/html; }
  location / { return 301 https://$host$request_uri; }
}

server {
  listen 443 ssl http2;
  server_name your.domain.com;

  ssl_certificate     /etc/letsencrypt/live/your.domain.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/your.domain.com/privkey.pem;

  # 直接反代到“前端容器”的 8080（该容器再反代后端）
  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;   # 透传 WebSocket（如前端内继续反代 /client-ws）
    proxy_set_header Connection "upgrade";
  }
}
```
然后启用并校验：
```bash
sudo ln -sf /etc/nginx/sites-available/theprojectyin.conf /etc/nginx/sites-enabled/theprojectyin.conf || true
sudo nginx -t && sudo systemctl reload nginx
```
含义：主机 Nginx 接管 80/443；所有请求转发给前端容器的 8080；WebSocket 头已透传，确保后端 WS 可用。

10.3 签发/续期证书（Let's Encrypt）
```bash
sudo certbot --nginx -d your.domain.com --register-unsafely-without-email --agree-tos
# 或使用已有证书，将上面 ssl_certificate/ssl_certificate_key 指向你的证书路径
```
含义：一键签证并改写 Nginx 配置。证书默认 90 天自动续期，可用 `sudo certbot renew --dry-run` 验证计划任务。

10.4 验证 HTTPS
```bash
curl -I https://your.domain.com/
# 预期 200/302；浏览器访问 https://your.domain.com 应展示前端页面
```
含义：确保 TLS 可用，前端能被正确代理；前端内对 `/client-ws` 等路径的 WS 将由前端容器继续反代到后端容器。

可选：如不使用前端容器 Nginx，而是让主机 Nginx 直接代理后端
- 将主机 Nginx 的 `location /` 指向 `http://127.0.0.1:12393/`，并在主机 Nginx 配置对应的静态资源与 WS 反代；这种方式减少一层代理，但需要在主机 Nginx 内配置更多路径规则。一般推荐仍然代理到前端容器的 8080，由前端容器内的 Nginx 处理静态与后端路径分发。

- 以非 root 身份运行：在 Compose `backend:` 下添加
```yaml
user: "1000:1000"
```
（需确保挂载目录属主/权限允许）
- 限制容器资源：
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```
- 只读根文件系统（若无写入需求）：
```yaml
read_only: true
tmpfs:
  - /tmp
```

---

如需我为你的实际 `conf.yaml` 与 `mcp_servers.json` 做一次“生产检查清单”（端口、密钥、安全项、监控项），把文件贴出来即可，我会给出差异化建议。


