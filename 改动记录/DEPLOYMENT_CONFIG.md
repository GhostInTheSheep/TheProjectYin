# 🚀 部署配置指南 - 解决硬编码地址问题

## 🎯 **问题解决**

之前的硬编码 `127.0.0.1:12393` 地址在部署到服务器时会导致前端无法访问后端。现在已实现智能地址检测和配置化管理。

## ✅ **解决方案**

### **1. 前端智能地址检测**
- ✅ 自动从当前页面URL检测服务器地址
- ✅ 支持环境变量配置
- ✅ 自动服务器发现和健康检查
- ✅ 本地存储用户自定义配置

### **2. 后端配置化URL生成**
- ✅ 通过 `conf.yaml` 统一管理服务器地址
- ✅ 支持不同环境的灵活配置
- ✅ 跨平台路径兼容

## ⚙️ **配置方式**

### **方式一：自动检测（推荐）**
前端会自动从当前页面URL检测服务器地址：

```
用户访问: https://your-server.com:8080
前端自动检测到: your-server.com:8080
生成的媒体URL: https://your-server.com:8080/ads/video.mp4
```

### **方式二：环境变量配置**
创建 `frontend/Frontend-AI/.env.local`：
```bash
# 生产服务器
REACT_APP_SERVER_HOST=your-server.com
REACT_APP_SERVER_PORT=80

# 或Docker环境
REACT_APP_SERVER_HOST=localhost
REACT_APP_SERVER_PORT=8080
```

### **方式三：后端配置**
修改 `conf.yaml`：
```yaml
system_config:
  media_server:
    host: "your-server.com"  # 生产服务器IP或域名
    port: 80                 # 生产服务器端口
```

## 🌍 **部署场景**

### **本地开发环境**
```yaml
# conf.yaml
media_server:
  host: 127.0.0.1
  port: 12393
```
**前端自动检测**: `http://127.0.0.1:12393`

### **Linux生产服务器**
```yaml
# conf.yaml  
system_config:
  host: 0.0.0.0        # 监听所有接口
  port: 80
  media_server:
    host: "your-server.com"  # 实际域名
    port: 80
```
**前端自动检测**: `https://your-server.com/ads/video.mp4`

### **Docker部署**
```yaml
# conf.yaml
system_config:
  host: 0.0.0.0
  port: 8080
  media_server:
    host: "localhost"   # 或实际服务器IP
    port: 8080
```

```dockerfile
# 暴露端口
EXPOSE 8080
```

**前端访问**: `http://localhost:8080/ads/video.mp4`

### **反向代理 (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:12393;
    }
    
    location /ads/ {
        alias /opt/theprojectyin/ads/;
    }
    
    location /videos/ {
        alias /opt/theprojectyin/videos/;
    }
}
```

```yaml
# conf.yaml
media_server:
  host: "your-domain.com"
  port: 80
```

## 🔧 **智能检测流程**

```
1. 🔍 检查环境变量配置
   ↓
2. 🌐 从当前页面URL检测服务器地址
   ↓ 
3. 🏥 健康检查确认服务器可用
   ↓
4. 💾 保存到本地存储供下次使用
   ↓
5. 📺 生成正确的媒体URL
```

## 🧪 **测试验证**

### **开发环境测试**
```bash
# 启动后端
python -m src.solvia_for_chat.server

# 检查前端控制台
# 应该看到: "🌐 动态服务器配置: http://127.0.0.1:12393"
```

### **服务器部署测试**
```bash
# 1. 修改conf.yaml中的host
# 2. 启动服务器
# 3. 浏览器访问: http://your-server.com
# 4. 检查控制台: "🔄 更新服务器地址: 127.0.0.1:12393 → your-server.com:80"
# 5. 测试广告视频播放
```

## 📊 **配置优先级**

| 优先级 | 配置来源 | 示例 |
|-------|----------|------|
| **1** | 环境变量 | `REACT_APP_SERVER_HOST=prod.com` |
| **2** | 页面URL检测 | `https://your-server.com` → `your-server.com` |
| **3** | 本地存储 | 用户手动设置的地址 |
| **4** | 默认配置 | `127.0.0.1:12393` |

## 🚨 **故障排除**

### **视频无法播放**
1. 检查控制台是否显示正确的服务器地址
2. 手动访问 `http://your-server/ads/` 确认文件可访问
3. 检查防火墙和端口开放情况

### **地址检测错误**
1. 设置环境变量强制指定地址
2. 在前端设置页面手动修改服务器地址
3. 检查 `conf.yaml` 中的 `media_server.host` 配置

### **跨域问题**
1. 确认后端启动时监听 `0.0.0.0` 而不是 `127.0.0.1`
2. 检查CORS配置是否正确
3. 对于HTTPS环境，确保所有资源都使用HTTPS

## 🎉 **部署验证清单**

- [ ] 后端 `conf.yaml` 配置正确的服务器地址
- [ ] 前端能够自动检测或手动配置服务器地址  
- [ ] 广告视频能够正常播放
- [ ] 洗衣机教程视频能够正常播放
- [ ] WebSocket连接正常
- [ ] 跨域访问无问题

**现在你的系统可以自动适应任何部署环境！** 🚀