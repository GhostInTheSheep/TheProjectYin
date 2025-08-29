## TheProjectYin 生产环境重新部署指南（每一步都有目的说明）

本指南覆盖从环境准备、后端部署、前端构建与发布、Nginx 配置、到上线验证与回滚的完整流程。命令以 Debian/Ubuntu 为例，路径请按你的服务器实际情况调整：
- 如果你使用的是 `/opt/server_codes/TheProjectYin`（你线上当前路径），请将文档中的路径替换为该前缀。
- 如果你使用的是仓库本机路径 `/opt/codes/TheProjectYin`，同理替换。

### 0) 前置准备（只需一次）
- 目的：安装系统依赖，准备部署目录。

```bash
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git nginx
# Node 推荐用 nvm 或 NodeSource 安装，确保 Node>=18（建议20+）
# 例如（Node 20）：
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt-get install -y nodejs

# 创建部署根目录（如使用 /opt/server_codes）
sudo mkdir -p /opt/server_codes
sudo chown -R $USER:$USER /opt/server_codes
```

### 1) 获取/更新代码
- 目的：拿到最新代码，用于构建与部署。

```bash
cd /opt/server_codes
[ -d TheProjectYin ] || git clone https://github.com/your_org/TheProjectYin.git
cd TheProjectYin
git fetch --all
git checkout main
git pull --rebase
```

### 2) 创建 Python 虚拟环境并安装后端依赖
- 目的：隔离后端运行环境，避免系统 Python 污染。

```bash
cd /opt/server_codes/TheProjectYin
python3 -m venv ai-env
source ai-env/bin/activate
pip install --upgrade pip
# 选择合适的 requirements（常用 requirements.linux.txt）
pip install -r requirements.linux.txt
# 或
# pip install -r requirements.linux.min.txt
```

### 3) 校验配置文件
- 目的：确保端口、主机与功能配置正确（如是否启用代理等）。
- 文件：`conf.yaml`（在项目根目录）。后端服务端口/主机由 `system_config` 控制，默认会被 `run_server.py` 读取。
- 模型缓存目录在 `run_server.py` 已设为项目根下的 `models`，无需额外配置。

### 4) 以 Systemd 管理后端（建议）
- 目的：后台常驻、开机自启、崩溃自动重启、统一日志。

创建 `/etc/systemd/system/theprojectyin.service`：

```ini
[Unit]
Description=TheProjectYin Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/server_codes/TheProjectYin
ExecStart=/opt/server_codes/TheProjectYin/ai-env/bin/python /opt/server_codes/TheProjectYin/run_server.py
Restart=always
RestartSec=5
Environment=HF_HOME=/opt/server_codes/TheProjectYin/models
Environment=MODELSCOPE_CACHE=/opt/server_codes/TheProjectYin/models

[Install]
WantedBy=multi-user.target
```

启用并启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable theprojectyin
sudo systemctl start theprojectyin
# 查看状态与日志
systemctl status theprojectyin -n 50 --no-pager
journalctl -u theprojectyin -f
```

### 5) 构建前端（Web 版本）
- 目的：产出 Nginx 可直接托管的网页构建产物，注意不是 Electron 渲染版本。

```bash
cd /opt/server_codes/TheProjectYin/frontend/Frontend-AI
npm ci
npm run build:web
# 产物输出目录：/opt/server_codes/TheProjectYin/frontend/Frontend-AI/dist/web
```

### 6) 配置 Nginx（HTTPS + 反向代理 + 缓存策略）
- 目的：为外网提供 HTTPS 服务，托管前端静态文件，代理后端 API 与 WebSocket。
- 关键点：`index.html` 与根路由必须 no-store，`/assets` 与 `/libs` 长缓存 immutable，避免新旧分块混用导致 React 初始化错误。

创建或更新 `/etc/nginx/sites-available/jtlai.top`（替换成你的域名与路径）：

```nginx
server {
  listen 443 ssl http2;
  server_name jtlai.top;

  ssl_certificate     /etc/letsencrypt/live/jtlai.top/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/jtlai.top/privkey.pem;

  root  /opt/server_codes/TheProjectYin/frontend/Frontend-AI/dist/web;
  index index.html;

  # 长缓存的静态分块（带哈希）
  location /assets/ {
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    try_files $uri =404;
  }
  # libs（含 wasm/onnx/moc3）长缓存 + 正确 MIME
  location /libs/ {
    types {
      application/wasm wasm;
      model/onnx       onnx;
      application/octet-stream moc3 moc;
    }
    add_header Cache-Control "public, max-age=31536000, immutable" always;
    try_files $uri =404;
  }

  # HTML 与 SPA 入口不缓存
  location = /index.html {
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
    try_files $uri =404;
  }
  location / {
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
    try_files $uri $uri/ /index.html;
  }

  # WebSocket 代理
  location /client-ws {
    proxy_pass         http://127.0.0.1:12393;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection "upgrade";
    proxy_read_timeout 3600s;
  }
  location /tts-ws {
    proxy_pass         http://127.0.0.1:12393;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection "upgrade";
    proxy_read_timeout 3600s;
  }

  # 后端 API/静态资源透传（按需）
  set $backend http://127.0.0.1:12393;
  location /api/           { proxy_pass $backend; add_header Access-Control-Allow-Origin "*" always; }
  location /live2d-models/ { proxy_pass $backend; add_header Cache-Control "public, max-age=31536000, immutable" always; }
  location /videos/        { proxy_pass $backend; add_header Cache-Control "public, max-age=31536000, immutable" always; }
  location /ads/           { proxy_pass $backend; add_header Cache-Control "public, max-age=31536000, immutable" always; }
  location /bg/            { proxy_pass $backend; add_header Cache-Control "public, max-age=31536000, immutable" always; }
  location /avatars/       { proxy_pass $backend; add_header Cache-Control "public, max-age=31536000, immutable" always; }
  location /cache/         { proxy_pass $backend; add_header Cache-Control "public, max-age=60" always; }
}

server {
  listen 80;
  server_name jtlai.top;
  return 301 https://$host$request_uri;
}
```

启用站点并生效：
```bash
sudo ln -sf /etc/nginx/sites-available/jtlai.top /etc/nginx/sites-enabled/jtlai.top
sudo nginx -t && sudo systemctl reload nginx
```

### 7) 原子化发布前端（避免混版）
- 目的：确保每次上线都是同一批构建产物，不留下旧 `assets`。

两种方式任选：
- 方式A：Nginx 直接指向 `dist/web`（构建完成即生效）。
- 方式B：将 `dist/web` 同步到独立对外目录（推荐带回滚能力）。

```bash
# 方式A：直接使用 dist/web，无需复制
# 构建完成后仅需 reload Nginx（一般也不需要）

# 方式B：同步到独立目录并启用 --delete 确保清理旧文件
STAMP=$(date +%Y%m%d_%H%M%S)
TARGET=/opt/deploy/jtlai.top/releases/$STAMP
mkdir -p "$TARGET"
rsync -a --delete /opt/server_codes/TheProjectYin/frontend/Frontend-AI/dist/web/ "$TARGET"/
ln -sfn "$TARGET" /opt/deploy/jtlai.top/current
# 将 Nginx root 指向 /opt/deploy/jtlai.top/current 后，仅需 reload 即可完成切换
sudo nginx -t && sudo systemctl reload nginx
```

### 8) 上线验证
- 目的：确保前端与后端都可用，且缓存策略正确。

```bash
# 后端接口健康检查
curl -I http://127.0.0.1:12393/api/ads

# 浏览器开发者工具 Network 检查：
# - /index.html 响应头应包含 Cache-Control: no-store
# - /assets/* 与 /libs/* 应为 200 且 Cache-Control: immutable
# - 无 404 的旧 vendor/react-vendor 分块请求
```

### 9) 常见问题
- Cannot access 'React' before initialization：
  - 原因：前端新旧分块混用（HTML 被缓存或未原子替换）。
  - 处理：确保 HTML no-store；使用 `rsync --delete` 或目录切换；强制刷新浏览器缓存。
- Nginx 报错 "map directive is not allowed here"：
  - 原因：`map` 只能放在 http 级别，不能放 server 内。
  - 处理：删除 `map`，在各 WS 的 `location` 中直接设置 Upgrade/Connection 头（见上面的配置）。

### 10) 回滚
- 目的：快速恢复到上一版本。

```bash
# 若使用了 releases 目录：
ls -1 /opt/deploy/jtlai.top/releases
ln -sfn /opt/deploy/jtlai.top/releases/<上一个STAMP> /opt/deploy/jtlai.top/current
sudo nginx -t && sudo systemctl reload nginx
```
