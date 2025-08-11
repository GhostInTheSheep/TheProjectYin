# 🎯 相对路径解决方案 - 彻底解决硬编码问题

## 💡 **核心思路**

既然前端和后端都在同一个项目 `TheProjectYin` 中，后端已经挂载了静态文件服务，前端直接使用相对路径即可：

```
TheProjectYin/
├── frontend/Frontend-AI/     # 前端应用
├── ads/                      # 广告视频
├── videos/                   # 教程视频
└── src/solvia_for_chat/      # 后端服务
```

## ✅ **解决方案架构**

### **后端静态文件挂载**
```python
# src/solvia_for_chat/server.py
self.app.mount("/ads", CORSStaticFiles(directory="ads"), name="advertisements")
self.app.mount("/videos", CORSStaticFiles(directory="videos"), name="videos")
```

### **后端生成相对路径**
```python
# src/solvia_for_chat/mcpp/advertisement_server.py
"url_path": f"/ads/{file_path.name}",  # ✅ 相对路径

# src/solvia_for_chat/mcpp/laundry_server.py  
web_video_path = f"/videos/{Path(video_info['path']).name}"  # ✅ 相对路径
```

### **前端自动解析**
```javascript
// 后端返回: "/ads/Phantom.mp4"
// 用户访问: https://your-server.com
// 浏览器自动解析为: https://your-server.com/ads/Phantom.mp4
```

## 🚀 **工作原理**

### **本地开发环境**
```
用户访问: http://127.0.0.1:12393
视频路径: /ads/video.mp4
实际地址: http://127.0.0.1:12393/ads/video.mp4 ✅
```

### **生产服务器环境**
```
用户访问: https://your-server.com
视频路径: /ads/video.mp4
实际地址: https://your-server.com/ads/video.mp4 ✅
```

### **Docker部署环境**
```
用户访问: http://localhost:8080
视频路径: /ads/video.mp4
实际地址: http://localhost:8080/ads/video.mp4 ✅
```

## 🔧 **技术实现**

### **1. 前端地址检测**
```javascript
// frontend/Frontend-AI/src/renderer/src/utils/env-config.ts
export function getCurrentBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const currentUrl = new URL(window.location.href);
    return `${currentUrl.protocol}//${currentUrl.host}`;
  }
  return 'http://127.0.0.1:12393';
}
```

### **2. WebSocket连接**
```javascript
// frontend/Frontend-AI/src/renderer/src/context/websocket-context.tsx
function getDefaultUrls() {
  const baseUrl = getCurrentBaseUrl();           // 自动检测当前域名
  const wsUrl = baseUrl.replace(/^http/, 'ws') + '/client-ws';
  return { baseUrl, wsUrl };
}
```

### **3. 媒体文件访问**
```javascript
// 后端返回的广告数据
{
  "name": "Phantom",
  "filename": "Phantom.mp4", 
  "url_path": "/ads/Phantom.mp4"  // ← 相对路径，自动适应任何域名
}

// 前端直接使用
<video src="/ads/Phantom.mp4" />  // 浏览器自动解析为完整URL
```

## 🎉 **优势**

### **✅ 完全无硬编码**
- 前端：自动从页面URL检测服务器地址
- 后端：生成相对路径，适应任何域名
- 部署：无需修改任何配置

### **✅ 自动适应环境**
| 环境 | 用户访问 | WebSocket | 视频地址 |
|------|----------|-----------|----------|
| 本地开发 | `http://127.0.0.1:12393` | `ws://127.0.0.1:12393/client-ws` | `http://127.0.0.1:12393/ads/video.mp4` |
| 生产服务器 | `https://your-server.com` | `wss://your-server.com/client-ws` | `https://your-server.com/ads/video.mp4` |
| Docker | `http://localhost:8080` | `ws://localhost:8080/client-ws` | `http://localhost:8080/ads/video.mp4` |

### **✅ 简化维护**
- 不需要修改 `conf.yaml` 中的地址配置
- 不需要创建环境变量文件  
- 不需要复杂的服务器发现逻辑

## 📋 **部署验证**

### **测试步骤**
1. **本地测试**：
   ```bash
   python -m src.solvia_for_chat.server
   # 访问 http://127.0.0.1:12393
   # 检查广告视频是否正常播放
   ```

2. **服务器测试**：
   ```bash
   # 部署到服务器，无需修改任何配置
   python -m src.solvia_for_chat.server
   # 用户访问 https://your-server.com
   # 检查广告视频是否正常播放
   ```

3. **跨域测试**：
   ```bash
   # 检查控制台是否有CORS错误
   # 确认视频文件可以正常加载
   ```

## 🔍 **故障排除**

### **如果视频无法播放**
1. 检查控制台网络请求：
   ```
   GET /ads/video.mp4  → 应该返回200
   ```

2. 检查后端日志：
   ```
   Advertisement server initialized: X ads found
   ```

3. 检查文件权限：
   ```bash
   ls -la ads/
   # 确保文件可读
   ```

## 🎯 **总结**

这个方案彻底解决了硬编码地址问题：

- ✅ **零配置**：无需手动设置任何地址
- ✅ **自适应**：自动适应任何部署环境  
- ✅ **简洁**：基于Web标准的相对路径机制
- ✅ **稳定**：不依赖复杂的地址检测逻辑

**核心原理**：利用浏览器的相对路径解析机制 + 后端的静态文件服务 = 完美的跨环境兼容性！ 🚀