# 📺 媒体服务器配置指南

## 📋 **概述**

媒体服务器配置现已完全集成到 `conf.yaml` 中，无需单独的配置文件，支持跨平台部署。

## ⚙️ **配置选项**

在 `conf.yaml` 的 `system_config` 部分已添加 `media_server` 配置：

```yaml
system_config:
  # ... 其他配置 ...
  
  # 媒体服务器配置 - 用于广告视频和洗衣机教程视频
  media_server:
    host: 127.0.0.1 # 媒体服务器主机 (生产环境可改为 0.0.0.0)
    port: 12393     # 媒体服务器端口 (与主服务器端口一致)
    ads_directory: 'ads'        # 广告视频目录
    videos_directory: 'videos'  # 洗衣机教程视频目录
    # 跨平台兼容配置
    use_absolute_paths: false   # 是否使用绝对路径 (Linux服务器建议设为true)
    base_directory: null        # 基础目录 (null表示使用当前工作目录)
```

## 🌍 **不同环境配置**

### **本地开发环境**
```yaml
media_server:
  host: 127.0.0.1
  port: 12393
  ads_directory: 'ads'
  videos_directory: 'videos'
  use_absolute_paths: false
  base_directory: null
```

### **Linux服务器部署**
```yaml
media_server:
  host: 0.0.0.0  # 允许外部访问
  port: 12393
  ads_directory: 'ads'
  videos_directory: 'videos'
  use_absolute_paths: true
  base_directory: '/opt/theprojectyin'
```

### **Windows服务器部署**
```yaml
media_server:
  host: 0.0.0.0
  port: 12393
  ads_directory: 'ads'
  videos_directory: 'videos'
  use_absolute_paths: true
  base_directory: 'D:\Projects\TheProjectYin'
```

## 🔧 **配置参数说明**

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `host` | 媒体服务器主机地址 | `127.0.0.1` | `0.0.0.0` |
| `port` | 媒体服务器端口 | `12393` | `8080` |
| `ads_directory` | 广告视频目录 | `ads` | `/opt/app/ads` |
| `videos_directory` | 洗衣机教程目录 | `videos` | `/opt/app/videos` |
| `use_absolute_paths` | 是否使用绝对路径 | `false` | `true` |
| `base_directory` | 基础目录 | `null` | `/opt/theprojectyin` |

## 🚀 **自动功能**

### ✅ **跨平台兼容**
- 自动处理 Windows `\` 和 Linux `/` 路径分隔符
- 支持相对路径和绝对路径
- 智能路径解析

### ✅ **错误恢复**
- 配置加载失败时自动使用默认值
- 目录不存在时fallback到参数指定目录
- 完善的错误处理和日志记录

### ✅ **URL生成**
- 自动生成正确的视频URL
- 支持自定义主机和端口
- 跨平台URL格式化

## 📂 **目录结构示例**

### **开发环境**
```
TheProjectYin/
├── ads/                    # 广告视频
│   ├── Phantom.mp4
│   └── Hokkaido.mp4
├── videos/                 # 洗衣机教程
│   ├── machine_1.mp4
│   └── machine_2.mp4
└── conf.yaml              # 统一配置文件
```

### **生产服务器**
```
/opt/theprojectyin/        # Linux服务器
├── ads/
├── videos/
└── conf.yaml

D:\WebApps\TheProjectYin\  # Windows服务器
├── ads\
├── videos\
└── conf.yaml
```

## 🔍 **验证配置**

启动服务器后，检查日志输出：
```
✅ Loaded advertisement: Phantom
✅ Loaded advertisement: Hokkaido
✅ 发现 2 个洗衣机教程视频
  - 1: machine_1
  - 2: machine_2
```

## 🐛 **故障排除**

### **视频无法播放**
1. 检查 `ads_directory` 和 `videos_directory` 路径是否正确
2. 确认视频文件存在且格式支持
3. 验证 `host` 和 `port` 配置

### **路径错误**
1. Windows服务器设置 `use_absolute_paths: true`
2. 检查 `base_directory` 是否正确
3. 确认目录权限

### **跨域问题**
1. 生产环境设置 `host: 0.0.0.0`
2. 检查防火墙端口开放
3. 验证CORS配置

## 🎯 **最佳实践**

1. **开发环境**：使用默认配置即可
2. **生产环境**：设置绝对路径和外部访问
3. **Docker部署**：使用容器内路径
4. **负载均衡**：配置统一的媒体服务器

---

**现在你的媒体配置完全集成在 `conf.yaml` 中，支持任意平台部署！** 🎉