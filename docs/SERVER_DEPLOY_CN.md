## TheProjectYin 服务器部署步骤（Linux）

适用对象：Ubuntu/Debian/CentOS 等常见 Linux 服务器，将本项目在服务端常驻运行并通过 HTTPS 提供给前端访问。

---

### 1) 前置条件
- 已将项目放置到：`/opt/codes/TheProjectYin`
- 系统已具备：
  - Python ≥ 3.10（含 `venv`）
  - Node.js ≥ 18（仅在需要构建 Web 前端时）
  - Nginx（用于 HTTPS 与反向代理）

安装参考（Debian/Ubuntu）：
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
# 可选：安装 Node.js 18+（若需构建 Web 前端）
# 使用 nvm 或发行版源/NodeSource 安装，略
```

---

### 2) 配置后端（conf.yaml）
编辑根目录下 `conf.yaml`：
- `system_config.host` 改为 `0.0.0.0`（允许外网访问）。
- 媒体目录建议使用绝对路径：
  - `system_config.media_server.use_absolute_paths: true`
  - `system_config.media_server.base_directory: '/opt/codes/TheProjectYin'`
- 建议将敏感密钥改为环境变量（生产）：
  - `OPENAI_API_KEY`（用于 LLM/ASR）
  - `FISH_API_KEY`（Fish TTS）

示意（仅展示关键段）：
```yaml
system_config:
  host: 0.0.0.0
  port: 12393
  media_server:
    use_absolute_paths: true
    base_directory: '/opt/codes/TheProjectYin'
```

如使用 MCP（已内置）：编辑 `mcp_servers.json` 将命令改为虚拟环境里的 Python 绝对路径（下一步会创建）：
```json
{
  "mcp_servers": {
    "laundry-assistant": {
      "command": "/opt/codes/TheProjectYin/ai-env/bin/python",
      "args": ["-m", "src.solvia_for_chat.mcpp.laundry_server", "--videos-dir=videos"],
      "env": {"PYTHONPATH": "."},
      "timeout": 30
    },
    "advertisement-server": {
      "command": "/opt/codes/TheProjectYin/ai-env/bin/python",
      "args": ["-m", "src.solvia_for_chat.mcpp.advertisement_server", "--ads-dir=ads"],
      "env": {"PYTHONPATH": "."},
      "timeout": 30
    }
  }
}
```

---

### 3) 创建虚拟环境并安装依赖
```bash
cd /opt/codes/TheProjectYin
python3 -m venv ai-env
source ai-env/bin/activate
pip install -U pip wheel
pip install -r requirements.linux.txt
# 国内可选：
# pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
# 或临时：pip install -r requirements.linux.txt -i https://mirrors.aliyun.com/pypi/simple/
```

生产环境建议使用环境变量提供密钥：
```bash
export OPENAI_API_KEY="<你的OpenAI密钥>"
export FISH_API_KEY="<你的Fish API密钥>"
# 可选：模型缓存目录（已在代码中默认指向项目 models）
export HF_HOME=/opt/codes/TheProjectYin/models
export MODELSCOPE_CACHE=/opt/codes/TheProjectYin/models
```

---

### 4) 启动后端（前台/临时）
```bash
cd /opt/codes/TheProjectYin
source ai-env/bin/activate
python run_server.py --verbose
```
看到日志出现 `Starting server on 0.0.0.0:12393` 即表示启动成功。

常用自检（本机）：
```bash
# 工具页 302 跳转：应返回 302 到 /web_tool/index.html
curl -I http://127.0.0.1:12393/web-tool

# 业务接口：列出视频/广告
curl http://127.0.0.1:12393/api/videos
curl http://127.0.0.1:12393/api/ads

# WebSocket 路径（客户端连接用）
# ws://<域名或IP>:12393/client-ws
# ws://<域名或IP>:12393/tts-ws
```

---

### 5) 构建前端（Web 版，可选）
如果希望用浏览器直接访问 Web UI（非 Electron）：
```bash
cd /opt/codes/TheProjectYin/frontend/Frontend-AI
npm ci
npm run build:web
# 产物目录：/opt/codes/TheProjectYin/frontend/Frontend-AI/dist/web
```

---

### 6) 配置 Nginx（HTTPS + 反向代理 + 缓存）
示例域名：`example.com`，请替换为你的域名。

新建 `/etc/nginx/sites-available/theprojectyin.conf`：
```nginx
server {
  listen 80;
  server_name example.com;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name example.com;

  # 证书（用 certbot 自动签发后会自动填充）
  ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

  # 前端静态文件（可选：使用第 5 步构建的 web 版）
  root /opt/codes/TheProjectYin/frontend/Frontend-AI/dist/web;
  index index.html;

  # 前端路由：根与 HTML 禁缓存，避免旧包
  location = /index.html { add_header Cache-Control "no-store"; }
  location = / { try_files $uri /index.html; add_header Cache-Control "no-store"; }

  # 前端静态资源：强缓存
  location ^~ /assets/ { expires 30d; add_header Cache-Control "public, max-age=2592000, immutable"; try_files $uri =404; }
  location ^~ /libs/   { expires 30d; add_header Cache-Control "public, max-age=2592000, immutable"; try_files $uri =404; }

  # 反向代理到 Python 后端（HTTP 与 WebSocket）
  set $backend http://127.0.0.1:12393;

  # WebSocket 端点
  location /client-ws {
    proxy_pass $backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
  location /tts-ws {
    proxy_pass $backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }

  # 其余 API/静态资源交由后端
  location /api/   { proxy_pass $backend; }
  location /videos { proxy_pass $backend; }
  location /ads    { proxy_pass $backend; }
  location /cache  { proxy_pass $backend; }
  location /web-tool { proxy_pass $backend; }
  location /web_tool { proxy_pass $backend; }
}
```
启用并测试：
```bash
sudo ln -s /etc/nginx/sites-available/theprojectyin.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```
签发免费证书（可选）：
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com
```

---

### 7) 用 systemd 托管（生产推荐）
创建服务文件 `/etc/systemd/system/theprojectyin.service`：
```ini
[Unit]
Description=TheProjectYin Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/codes/TheProjectYin
ExecStart=/opt/codes/TheProjectYin/ai-env/bin/python /opt/codes/TheProjectYin/run_server.py
Restart=always
RestartSec=5
Environment=HF_HOME=/opt/codes/TheProjectYin/models
Environment=MODELSCOPE_CACHE=/opt/codes/TheProjectYin/models
# 建议把密钥放到环境变量（不要写到 conf）：
# Environment=OPENAI_API_KEY=xxxxxxxx
# Environment=FISH_API_KEY=xxxxxxxx

[Install]
WantedBy=multi-user.target
```
启用与管理：
```bash
sudo systemctl daemon-reload
sudo systemctl enable theprojectyin
sudo systemctl start theprojectyin
systemctl status theprojectyin -n 50 --no-pager
journalctl -u theprojectyin -f
```

---

### 8) 防火墙与端口
- 对外仅开放 80/443（有 Nginx 反代即可）。
- 如需直连调试，可临时开放 12393：`sudo ufw allow 12393/tcp`。

---

### 9) 升级与回滚
```bash
cd /opt/codes/TheProjectYin
git pull
source ai-env/bin/activate
pip install -r requirements.linux.txt
sudo systemctl restart theprojectyin
```
如升级失败，可回滚到某个 tag/commit 后重启服务。

---

### 10) 常见问题
- 端口被占用：`sudo lsof -i:12393` 找到占用进程并处理。
- 前端空白/加载失败：检查前端 `index.html` 缓存策略；清浏览器缓存或确保 Nginx 对根与 HTML 使用 `no-store`。
- WebSocket 断开：确认 Nginx `Upgrade/Connection` 头已按示例配置；确认后端运行中。
- 静态资源 404：确认 `ads/`、`videos/` 目录存在且 Nginx 相关 location 正确代理到后端。
- API 密钥泄露风险：不要把密钥硬编码到 `conf.yaml`，改用环境变量或 Secrets 管理。

---

完成以上步骤后，即可通过 `https://example.com` 访问前端页面，并由 Nginx 反向代理到后端服务（WebSocket 与 API）。如不使用前端 Web 版，也可直接通过 Electron 客户端或其他客户端接入 `wss://example.com/client-ws`。
