# 屏幕贴码实例管理方案（QR → 直达实例管理页）

目标：为每一块屏幕（本程序运行的实例）生成一个二维码，贴在屏幕上。用户扫码后，直接打开该屏幕对应的“远程管理页面”（能力与本地 `Ctrl + Space` 弹出的设置面板一致或超集），用于远程查看状态与下发控制指令。

---

## TL;DR 流程
1) 设备实例启动 → 后端注册设备（获取 `device_id` 与短期 `admin_token`）
2) 设备向后端汇报自身 `device_id` 与当前活跃 `client_uid`（WS 会话）
3) 设备向后端要一个“管理页 URL”，前端用该 URL 生成二维码并显示（或打印贴纸）
4) 扫码者打开管理页：`/admin/device/:deviceId?token=...` → 后端校验 `token` → 渲染管理 UI → 通过后端对指定设备下发控制
5) 后端将指令路由到对应 WS 客户端（即那块屏幕上的实例）

---

## 核心设计

### 设备标识（Device Identity）
- `device_id`：稳定标识（建议来源：首次启动时生成并写入磁盘；或使用机器指纹/树莓派序列号/网卡 MAC 的哈希）。
- `client_uid`：WS 连接临时会话 ID（已在后端生成），用于路由“当前在线实例”。
- 后端维护映射：`device_id -> { last_seen_client_uid, status, meta }`。

### 二维码内容（URL 模板）
- 示例：`https://your-domain/admin/device/<device_id>?token=<jwt>
`
- `token` 为短期 JWT/HMAC（5~15 分钟有效），仅授权访问对应 `device_id` 的管理面板。

### 安全（强制）
- 全站 HTTPS；
- `token` 短期 + 单设备作用域（payload 含 `device_id`, `scope=admin:device`）；
- 支持后台“换码”（刷新 token）与失效（撤销）逻辑；
- 管理页会话可升级为账号登录 + RBAC；
- 重要写操作要求 CSRF/二次确认；
- 扫码页限流（IP/UA）与审计（谁在何时操作了何设备）。

---

## 后端实现（Python 服务侧）

### 1) 设备注册与配对
- 新增：`POST /api/devices/register`
  - 入参：`machine_fingerprint`（可选）、`display_name`（可选）
  - 返回：`device_id`, `admin_url`, `admin_token(expiry)`
- 设备启动时调用一次；失败时重试与退避。

### 2) 会话映射与心跳
- 设备 WS 连接建立后，立即上报：`{ type: "device-online", device_id }`
- 服务端记录：`device_id -> client_uid`（覆盖旧值）
- 定期心跳/last_seen 时间戳。

### 3) 管理页入口
- 新增：`GET /admin/device/:deviceId`
  - 校验 `token`（query/header/cookie）
  - 返回管理页 HTML（或重定向到前端 React 管理页）
- 新增：`POST /api/devices/:deviceId/actions/*`
  - 将动作转发到对应 `client_uid`（如：`interrupt`, `toggle_mic`, `update_config`, `switch_character`, `fetch_logs`）
  - 与本地 `Ctrl + Space` 的设置项能力保持一致；必要时扩展（只读/只写权限可分级）

### 4) Token 管理
- 新增：`POST /api/devices/:deviceId/token/refresh`（生成新短 token 与新二维码 URL）
- 新增：`POST /api/devices/:deviceId/revoke`（撤销现有 token，强制重新扫码）

### 5) 设备删除 / 退役
- `DELETE /api/devices/:deviceId`
  - 软删除（保留历史操作审计）或硬删除（连同映射与元数据）
  - 下发 “注销/恢复出厂” 指令（可选）

---

## 设备侧（树莓派/Electron 前端）

### 1) 启动展示二维码
- 启动后请求 `admin_url`；缓存于本地；
- 使用前端 QR 组件生成并显示（可叠加在设置入口页、或打印物理贴纸）。

### 2) 与本地 `Ctrl + Space` 的一致性
- `Ctrl + Space` 弹出的设置与远程管理页对应同一组配置项；
- 封装统一的设置 API（local + remote 复用），减少两套逻辑的偏差。

---

## 管理前端（React Admin）
- 路由：`/admin/device/:deviceId`
- 鉴权：短 token → 可选升级为登录态；
- 能力：状态看板、配置表单（带 diff / 回滚）、指令按钮、实时日志；
- WS：订阅该设备的状态流（在线/离线、VAD、TTS、播放状态、错误告警）。

---

## 多实例与并发
- 多实例并发管理：无问题，关键是以 `device_id` 精确路由；
- 指令串行化：对同一设备的关键写操作进行乐观锁/队列化（避免竞态）；
- 会话冲突策略：优先最近一次扫码或登录者（可配置），或采用会话锁（占用/释放）。

---

## 删除/退役与风险点
- 删除：`DELETE /api/devices/:deviceId` 清理映射/令牌；确保设备端自动回到未配对状态；
- 风险：
  - 二维码泄露 → 使用短期 token + 过期后强制刷新；
  - 设备换人/换屏 → 退役操作 & 清除本地缓存；
  - 离线设备 → 设置进入队列，待上线后下发或超时丢弃；
  - 跨网络/NAT → 所有控制经后端 WS 转发，不要求直连。

---

## 与现有代码对接建议
- 复用：
  - 现有 `/client-ws`、`client_uid` 映射为路由目标；
  - `useFooter`/`control-panel` 里的控制指令抽成后端 API 与设备命令（即“本地与远程”同一套语义）。
- 新增：
  - `device_id` 获取与持久化（本地文件如 `device.json`）；
  - 后端 `devices` 控制器（REST + WS 转发）；
  - 简易 JWT/HMAC 签名工具与中间件；
  - React Admin 页面（可放在现有前端工程或单独 admin 工程）。

---

## 快速任务清单（落地）
- [ ] 设备注册 API + `device_id` 落盘
- [ ] 设备上线上报 + 映射维护（`device_id -> client_uid`）
- [ ] 管理页 URL 与短 token 签发（二维码）
- [ ] 远程动作 API（转发到设备 WS）
- [ ] 管理页 React UI（状态/表单/日志/指令）
- [ ] Token 刷新与撤销；设备退役
- [ ] 审计与告警

---

## 难点评估
- 难点适中：
  - 安全边界（短期 token、RBAC、HTTPS）需到位；
  - 配置多端一致性（本地与远程）需抽象统一接口；
  - 并发写与回滚（表单 diff/版本）需要一些工程化；
- 现有基础良好（有 WS、会话映射、设置面板），整体实现成本可控。

---

## 示例二维码生成（前端）
- Web/Electron 前端：`qrcode.react` 或 Canvas 生成；
- 设备显示：在欢迎/设置页露出二维码；也可导出 PNG 供打印贴纸。

---

如需我直接在后端加 `devices` 控制器与签名中间件、前端加“远程管理页”样板，请告知你期望的 token 有效期与权限边界；我可按以上文档快速落地首版。
