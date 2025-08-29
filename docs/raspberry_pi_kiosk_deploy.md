### 树莓派竖屏LED部署运行手册（320×1280 竖屏 + 远程后端）

#### 0. 架构与目标
- 前端：树莓派 Chromium 全屏（kiosk）运行，访问后端 Web API/WS
- 后端：服务器（FastAPI + WebSocket，端口 12393，含 ASR/TTS/静态资源/MCP）
- 显示器：320×1280 竖屏 LED（需旋转/不休眠/自动启动）
- 麦克风：树莓派本地采集（浏览器 getUserMedia），或回退仅上传录音给后端 ASR

---

### 1. 前置准备（树莓派）
- 树莓派 OS（Bullseye/Bookworm），开启音频/网络/SSH
- 安装组件：
```bash
sudo apt-get update
sudo apt-get install -y git curl nginx pulseaudio pavucontrol \
  chromium-browser xdotool unclutter x11-xserver-utils
```
- 竖屏显示&不休眠（LXDE 环境，开机自启）：编辑 `/etc/xdg/lxsession/LXDE-pi/autostart` 追加
```
@xrandr -o right
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.5 -root
```

---

### 2. 后端服务器（远程）
- 监听与访问
  - `conf.yaml` → `system_config.host: 0.0.0.0`，`port: 12393`
  - 反代（推荐 Nginx/Caddy）：TLS/wss、gzip、缓存、静态资源 Range 支持
- 启用 MCP 执行器（已在仓库中配置）
  - `conf.yaml`（片段）
    ```yaml
    use_mcpp: True
    mcp_enabled_servers: ["laundry-assistant", "advertisement-server"]
    ```
  - `mcp_servers.json`（使用虚拟环境绝对 python）
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
- （可选）systemd 管理示例
  - `sudo nano /etc/systemd/system/ai-backend.service`
    ```ini
    [Unit]
    Description=AI Backend (uvicorn)
    After=network.target

    [Service]
    WorkingDirectory=/opt/codes/TheProjectYin
    Environment=PYTHONUNBUFFERED=1
    ExecStart=/opt/codes/TheProjectYin/ai-env/bin/python /opt/codes/TheProjectYin/run_server.py --verbose
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
  - MCP 两个进程同理（分别指向 laundry/advertisement 模块），`systemctl enable --now ...`

---

### 3. 前端打包与发布（树莓派）
- 进入前端目录并安装：
```bash
cd /opt/codes/TheProjectYin/frontend/Frontend-AI
npm ci
```
- 生产构建（Nginx 静态托管）：
```bash
npm run build:web
# 产物目录：dist/web
```
- Nginx 站点（/etc/nginx/sites-available/ai-frontend）：
```nginx
server {
  listen 80;
  server_name _;

  root /opt/codes/TheProjectYin/frontend/Frontend-AI/dist/web;
  index index.html;

  # 关键：为 wasm/onnx 设置 MIME，避免 VAD wasm 报错
  types {
    application/wasm wasm;
    model/onnx onnx;
    application/javascript js;
    text/css css;
  }

  location / {
    try_files $uri $uri/ /index.html;
  }

  # 可选：/libs 强缓存
  location /libs/ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    try_files $uri =404;
  }
}
```
启用并重载：
```bash
sudo ln -sf /etc/nginx/sites-available/ai-frontend /etc/nginx/sites-enabled/ai-frontend
sudo nginx -t && sudo systemctl reload nginx
```

---

### 4. 浏览器（Chromium）kiosk 启动
- 临时（HTTP 场景，内网演示）：
```bash
chromium-browser \
  --kiosk --app="http://<树莓派IP>" \
  --autoplay-policy=no-user-gesture-required \
  --enable-features=UseOzonePlatform \
  --ozone-platform=wayland \
  --use-gl=egl \
  --disable-infobars --noerrdialogs --disable-session-crashed-bubble \
  --unsafely-treat-insecure-origin-as-secure="http://<树莓派IP>,http://<后端域名或IP>:12393"
```
- 开机自启（LXDE autostart）在 `/etc/xdg/lxsession/LXDE-pi/autostart` 追加：
```
@sleep 2 && chromium-browser --kiosk --app=http://<树莓派IP>
```
> 生产推荐为前后端都使用 HTTPS + wss，避免浏览器权限限制。

---

### 5. 音频与麦克风（树莓派）
- 选择输入设备：
```bash
pactl list short sources
arecord -l
pavucontrol   # GUI 选择“输入设备/应用权限”
```
- 录放测试：
```bash
arecord -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay test.wav
```
- 浏览器权限：进入页面后先点击一次页面（解锁 AudioContext），并允许站点访问麦克风。

---

### 6. VAD（浏览器端）与资源校验
- 构建后页面应从 `/libs/` 加载 VAD 所需文件：
  - onnxruntime-web 的 `*.wasm`
  - `@ricky0123/vad-web` 的 `silero_vad_v5.onnx`、`vad.worklet.bundle.min.js`
- 直接打开以下地址必须 200 且类型正确：
  - `http://<树莓派IP>/libs/ort-wasm-simd.wasm`（或 `ort-wasm.wasm`）
  - `http://<树莓派IP>/libs/silero_vad_v5.onnx`
- 若仍报 “wasm magic number/unsupported MIME”：
  - 确认 Nginx types 中包含 `application/wasm wasm;` `model/onnx onnx;`
  - 清缓存刷新，并确保先有用户交互再启麦克风
  - 树莓派不兼容时，可在前端设置中关闭 VAD（仅录音上传后端 ASR）

---

### 7. 竖屏/小宽度 UI 建议（320×1280）
- 隐藏/折叠侧栏，主区域显示聊天/Live2D
- 按钮/字体加大（触控友好），使用 `100dvh` 避免抖动
- Live2D 设置：≤30fps、antialias=false、resolution=1、低分辨率贴图（1024/512）

---

### 8. 性能与稳定性
- 前端：生产构建+Nginx 静态托管，移除开发工具/调试日志
- 后端：Nginx 反代，/ads /videos 用 Nginx 静态服务（支持 Range）；ASR/TTS/WS 由应用提供
- MCP：用 systemd 管理两个进程（自动重启）；首连失败可重试
- 广告素材：H.264+AAC，竖屏 360×1280/720×1280，1–2 Mbps；首个广告预加载

---

### 9. 故障排查速查
- VAD wasm 报错：检查 `/libs/*.wasm` 是否 200 + `application/wasm`；MIME 配置；刷新后先交互
- 麦克风无输入：`arecord` 能否录音→浏览器权限→pavucontrol 输入源
- WS 不稳：后端监听 `0.0.0.0`；前端 URL 指向 12393（wss/https）；反代超时/CORS/TLS
- MCP 提示不可用：确认两个 MCP 进程在运行；稍等冷启动后刷新

---

### 10. 验收清单
- [ ] 树莓派开机：竖屏、无休眠、自动进入 kiosk
- [ ] 前端页面可访问（<2s）
- [ ] 麦克风录放正常、浏览器授权
- [ ] VAD 正常（或已切换后端策略）
- [ ] 广告视频流畅播放，有声策略符合
- [ ] 与后端 WS 稳定、API 200、ASR/TTS 正常
- [ ] MCP 工具可用（广告播放列表等）
