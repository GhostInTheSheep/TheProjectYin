# Go + React 管理平台方案（树莓派浏览器前端 + 服务器 Docker 后端）

本文档给出一个面向本项目的管理平台方案：
- 前端：React（在树莓派上用浏览器访问，可选 Kiosk 模式）
- 后端：Golang（REST + WebSocket），部署在服务器，通过 Docker/Compose 管理
- 目的：统一配置、状态监控、素材管理、工具编排与运维操作，降低维护成本

---

## 1. 架构总览

- 树莓派（前端）：
  - 运行 Chromium/Firefox，访问 `https://<domain>/admin`
  - 可配置自启动、全屏、断线重连（Kiosk 场景）
- 服务器（后端）：
  - Go Admin API（REST/WS）
  - 反向代理（Caddy/Nginx），终止 TLS，反代 Admin API/静态前端
  - 现有 Python 后端（本项目）与 MCP 子进程，继续容器化托管
  - 可选数据库：PostgreSQL/SQLite（存储账号、审计、资产索引）

拓扑：
```
[Pi Browser] --https--> [Reverse Proxy] --http--> [Go Admin API]
                                          ├─http--> [Python Core Backend]
                                          └─stdio--> [MCP Servers]
```

---

## 2. 职责划分

- React Admin 前端：仪表盘（健康/状态）、配置编辑与对比、素材（广告/视频）管理、MCP 工具调用测试、用户管理与审计。
- Go Admin 后端：
  - 暴露统一 API；
  - 读取/校验/写入 `conf.yaml`、`mcp_servers.json`（带备份与回滚点）；
  - 触发 Python 后端热重载/优雅重启；
  - 素材上传/分片/转储/索引；
  - 代理调用 Python/MCP（同步/异步）；
  - 审计、鉴权、RBAC。
- Python 后端：保留核心业务（AI/媒体/WS/MCP 管理），管理平台只做“控制面”。

---

## 3. 模块设计

### 3.1 React 前端（Vite + React + TS + UI 库）
- Pages：Dashboard / Config / Assets / MCP / Users / Logs
- 能力：
  - 表单校验、编辑前后 diff 与影响范围提示；
  - WebSocket 订阅状态与日志（健康、任务、MCP 链接、告警）；
  - PWA/离线提示（可选）；
  - 按角色展示菜单（RBAC）。

### 3.2 Go Admin API（Gin/Fiber/Echo 其一）
- 建议目录：
```
admin-backend/
  cmd/admin-api/main.go
  internal/
    api/       # handlers（REST/WS）
    core/      # config manager / compose ctl / proxy
    ws/        # hubs/clients（推送健康、日志、事件）
    auth/      # JWT/OAuth/RBAC
    repo/      # sqlite/postgres 存储
    mcp/       # 调用 MCP 客户端
```
- 关键接口（示例）：
  - 健康：GET `/api/health`
  - 配置：GET/PUT `/api/config/conf`，GET/PUT `/api/config/mcp-servers`（含 JSON Schema 校验、备份/回滚）
  - 运行：POST `/api/runtime/reload`（触发 Python 后端热重载）、POST `/api/runtime/restart`（优雅重启）
  - 素材：`/api/assets/ads`、`/api/assets/videos`（列表/上传/删除/预览签名 URL）
  - MCP：GET `/api/mcp/servers`（状态），POST `/api/mcp/tools/:name/call`（调用）
  - Auth/RBAC：`/api/auth/login`、`/api/users/*`、角色策略
  - WS：`/ws/admin`（推送运行指标/日志/事件）

- 与 Python 后端：
  - HTTP/WS（沿用现有路由），或 Unix Socket/gRPC（可选）
  - 文件层直写 `conf.yaml` / `mcp_servers.json` / 资源目录（通过容器卷）

---

## 4. 部署方案（Docker/Compose）

### 4.1 Admin 前端
- `npm run build` 产物以 Nginx/Caddy 托管，反代 `/api/*`、`/ws/*` 到 Go Admin API。

### 4.2 Admin 后端（Go）
- 多阶段构建：`golang:alpine` → 最小运行镜像（`scratch`/`alpine`）。
- 暴露 8080（或自定义）。

### 4.3 Compose 示例
```yaml
version: "3.9"
services:
  proxy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./admin-frontend/dist:/srv/admin:ro
    depends_on: [admin-api]

  admin-api:
    build: ./admin-backend
    environment:
      - PYTHON_BACKEND_URL=http://python-backend:12393
      - CONF_PATH=/app/conf.yaml
      - MCP_SERVERS_PATH=/app/mcp_servers.json
    volumes:
      - ./conf.yaml:/app/conf.yaml
      - ./mcp_servers.json:/app/mcp_servers.json
      - ./ads:/app/ads
      - ./videos:/app/videos
    depends_on: [python-backend]

  python-backend:
    build: .
    ports: ["12393:12393"]
    volumes:
      - ./conf.yaml:/app/conf.yaml
      - ./mcp_servers.json:/app/mcp_servers.json
      - ./ads:/app/ads
      - ./videos:/app/videos
```

### 4.4 Caddyfile（示例）
```
admin.example.com {
  encode zstd gzip
  handle_path /admin* {
    root * /srv/admin
    try_files {path} /index.html
    file_server
  }
  reverse_proxy /api/* admin-api:8080
  reverse_proxy /ws/*  admin-api:8080
}
```

---

## 5. 安全与权限
- JWT + Refresh（短期访问令牌 + 长期刷新），HttpOnly/SameSite Cookie；
- RBAC（viewer/operator/admin），最小权限原则；
- CORS 仅允许受信域名；
- CSRF：关键写操作校验；
- 审计：配置变更/MCP/登录登出落日志；
- 机密与凭据：环境变量/Secrets（Vault/SOPS）。

---

## 6. 可观测性与稳定性
- 日志：JSON + Loki/ELK；
- 指标：Prometheus + Grafana（QPS/延时/错误率/WS 连接数）；
- 健康探针：依赖探测（Python 后端/MCP/媒体路径/数据库）；
- 弹性：自动重连、失败重试、接口幂等、回滚点。

---

## 7. 树莓派端建议
- 浏览器：Chromium Kiosk 模式自启、断线重连；
- UI 优化：懒加载/代码分割/降低动画，图像与视频降分辨率；
- 网络：与后端低 RTT（首选内网/VPN），WS 心跳保活。

---

## 8. 迭代路线
- P1：只读（健康/配置查看）
- P2：受控写（配置变更/素材上传），开启审计
- P3：运维动作（热重载/重启/滚动更新），发布流程规范化
- P4：CI/CD 接入（Docker 多阶段 + GitHub Actions），灰度/回滚

---

## 9. Checklist（验收）
- [ ] Admin 前端可登录，Dashboard 指标正常
- [ ] 配置读写与回滚可用，校验/备份生效
- [ ] 与 Python 后端通信正常（调用、热重载）
- [ ] WS 实时更新（健康/日志/事件）
- [ ] RBAC 生效与审计可查
- [ ] Compose 启停顺畅，TLS 有效

---

## 10. 价值与理由
- 分层清晰：控制面（Go+React）与数据面（Python/MCP）解耦；
- 安全稳健：权限、审计、回滚；
- 易扩展：新增 MCP/服务仅需注册与反代；
- 易迁移：可逐步替换脚本化人工运维为可视化自动化运维。

> 需要我输出可直接用的 Go 模板（Gin + JWT + WS + Swagger）与 React 模板（Vite + Chakra/AntD + RTK Query），以及 CI/CD（Actions + 多阶段构建），告诉我你的偏好即可。
