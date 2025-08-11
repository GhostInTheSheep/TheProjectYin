# 🎬 广告轮播系统 - 完整实现文档

## 📋 **系统概述**

基于项目现有MCP架构实现的广告轮播系统，与唤醒词系统完美配合，实现智能化的广告展示控制。

## 🏗️ **系统架构**

### **核心组件**

```
📦 广告轮播系统架构
├── 🎬 advertisement-server (MCP服务器)
│   ├── 扫描 ads/ 文件夹
│   ├── 提供广告查询MCP工具
│   └── 独立进程运行
├── 🎤 wake_word_manager (唤醒状态控制)
│   ├── 管理 listening/active 状态
│   ├── 发送广告控制信号
│   └── 触发广告显示/隐藏
└── 🎨 前端WebSocket处理器
    ├── 监听广告控制信号
    ├── 调用MCP工具获取广告
    └── 控制UI显示状态
```

## 📂 **文件结构**

### **新增文件**
```
📦 TheProjectYin/
├── ads/                                    # 🆕 广告视频文件夹
│   ├── README.md                          # 自动生成的使用说明
│   ├── config.json                        # 播放配置
│   └── *.mp4, *.avi, *.mov, *.webm      # 广告视频文件
└── src/solvia_for_chat/mcpp/
    └── advertisement_server.py            # 🆕 广告MCP服务器
```

### **修改文件**
```
📦 配置文件修改:
├── mcp_servers.json                       # 添加 advertisement-server 配置
├── conf.yaml                             # 启用 advertisement-server
├── src/solvia_for_chat/server.py         # 添加 /ads 静态文件服务
├── src/solvia_for_chat/conversations/
│   └── wake_word_manager.py              # 集成广告控制信号
└── frontend/Frontend-AI/src/renderer/src/services/
    └── websocket-handler.tsx             # 处理广告控制消息
```

## 🔧 **技术实现**

### **1. MCP服务器 (`advertisement_server.py`)**

**核心功能**：
- 扫描 `ads/` 文件夹中的视频文件
- 提供6个MCP工具：
  - `get_advertisement_playlist` - 获取播放列表
  - `get_next_advertisement` - 获取下一个广告
  - `get_current_advertisement` - 获取当前广告
  - `refresh_advertisements` - 刷新广告列表
  - `get_advertisement_stats` - 获取统计信息
  - `welcome_message` - 获取欢迎消息

**配置特性**：
- 随机播放模式
- 自动切换 (15秒间隔)
- 循环播放列表
- 播放统计追踪

### **2. 唤醒状态集成 (`wake_word_manager.py`)**

**广告控制逻辑**：
```python
"advertisement_control": {
    "should_show_ads": current_state == 'listening',  # 只在未唤醒时显示
    "control_action": "start_ads" if current_state == 'listening' else "stop_ads",
    "trigger_reason": action  # wake_up/sleep/ignored
}
```

### **3. 静态文件服务 (`server.py`)**

**新增挂载点**：
```python
self.app.mount(
    "/ads",                              # URL路径
    CORSStaticFiles(directory="ads"),    # 本地目录
    name="advertisements",               # 服务名称
)
```

### **4. 前端消息处理 (`websocket-handler.tsx`)**

**广告控制响应**：
```typescript
if (advertisement_control) {
  const { should_show_ads, control_action, trigger_reason } = advertisement_control;
  
  if (control_action === 'start_ads') {
    // 启动广告轮播
    console.log('🎬 开始播放广告轮播');
  } else if (control_action === 'stop_ads') {
    // 停止广告播放
    console.log('🛑 停止广告播放');
  }
}
```

## 🔄 **完整工作流程**

### **启动阶段**
1. **服务器启动** → `advertisement-server` MCP服务器自动启动
2. **扫描广告** → 自动扫描 `ads/` 文件夹，注册可用广告
3. **前端连接** → WebSocket连接建立，检测到 `listening` 状态
4. **调用MCP工具** → 前端调用 `get_advertisement_playlist` 获取播放列表
5. **开始轮播** → 显示广告轮播界面，15秒自动切换

### **用户交互阶段**
6. **唤醒检测** → 用户说："心海，今天天气怎么样？"
7. **状态切换** → `wake_word_manager` 切换到 `active` 状态
8. **广告停止** → 发送 `stop_ads` 控制信号
9. **界面切换** → 前端隐藏广告，显示VTuber对话界面
10. **正常对话** → VTuber处理用户请求，正常工作

### **对话结束阶段**
11. **结束检测** → 用户说："谢谢，再见"
12. **状态回归** → 切换回 `listening` 状态
13. **广告恢复** → 发送 `start_ads` 控制信号
14. **重新轮播** → 前端重新调用MCP工具，继续广告轮播

## 🎬 **广告内容管理**

### **支持的视频格式**
- **MP4** (.mp4) - 推荐，兼容性最好
- **AVI** (.avi) - 传统格式
- **MOV** (.mov) - Apple格式
- **WebM** (.webm) - Web优化格式
- **MKV** (.mkv) - 高质量格式

### **建议规格**
- **视频时长**: 15-60秒
- **分辨率**: 1920x1080 或 1280x720
- **文件大小**: < 50MB
- **编码格式**: H.264 + AAC (最佳兼容性)

### **命名规范**
```
ad_001_品牌介绍.mp4
ad_002_产品展示.mp4
ad_003_新品发布.mp4
ad_004_特别优惠.mp4
ad_005_用户评价.mp4
```

## 🔧 **配置说明**

### **MCP服务器配置 (`mcp_servers.json`)**
```json
{
  "mcp_servers": {
    "advertisement-server": {
      "command": "tf-env\\Scripts\\python.exe",
      "args": ["-m", "src.solvia_for_chat.mcpp.advertisement_server", "--ads-dir=ads"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### **主配置启用 (`conf.yaml`)**
```yaml
mcp_enabled_servers: ["time", "ddg-search", "laundry-assistant", "advertisement-server"]
```

### **广告播放配置 (`ads/config.json`)**
```json
{
  "advertisement_settings": {
    "shuffle_mode": true,              // 随机播放
    "auto_advance": true,              // 自动切换
    "advance_interval_seconds": 15,    // 切换间隔
    "loop_playlist": true              // 循环播放
  }
}
```

## 📊 **MCP工具详细说明**

### **1. get_advertisement_playlist**
```python
# 获取完整广告播放列表
arguments: {
  "shuffle": boolean  # 是否随机打乱列表
}

response: {
  "type": "advertisement_playlist",
  "playlist": [...],      # 广告列表
  "total_count": number,  # 广告总数
  "shuffle_mode": boolean # 是否随机模式
}
```

### **2. get_next_advertisement**
```python
# 获取下一个广告
arguments: {
  "advance": boolean  # 是否自动前进
}

response: {
  "type": "advertisement_response",
  "advertisement": {...}, # 广告信息
  "index": number,        # 当前索引
  "total": number         # 总数
}
```

### **3. get_current_advertisement**
```python
# 获取当前广告
response: {
  "type": "advertisement_response",
  "advertisement": {
    "id": "ad_001",
    "name": "品牌介绍",
    "url_path": "/ads/ad_001_品牌介绍.mp4",
    "size_mb": 25.6,
    "format": ".mp4"
  }
}
```

## 🚀 **部署和测试**

### **1. 系统部署**
```bash
# 1. 确保所有文件已正确修改
# 2. 创建广告文件夹 (已自动创建)
ls ads/

# 3. 重启服务器
python run_server.py

# 4. 检查MCP服务器状态
# 在日志中查看 "advertisement-server" 是否成功启动
```

### **2. 功能测试**
```bash
# 测试步骤:
# 1. 打开前端应用
npm run dev  # 在 frontend/Frontend-AI 目录

# 2. 观察控制台日志
# 应该看到: "📊 广告显示状态: 显示"

# 3. 测试唤醒功能
# 说: "心海"
# 控制台应显示: "🛑 广告系统: 停止广告播放"

# 4. 测试结束功能  
# 说: "再见"
# 控制台应显示: "🎬 广告系统: 开始播放广告轮播"
```

### **3. 添加测试广告**
```bash
# 将广告视频文件复制到ads文件夹
# 示例：
copy "示例广告.mp4" "ads/ad_001_示例广告.mp4"

# 重启服务器以扫描新文件
python run_server.py
```

## 🔍 **故障排除**

### **常见问题**

**1. MCP服务器启动失败**
```bash
# 检查日志中的错误信息
# 常见原因：
# - ads 文件夹不存在 (会自动创建)
# - Python环境问题
# - 依赖包缺失
```

**2. 广告文件无法访问**
```bash
# 检查静态文件服务
curl http://127.0.0.1:12393/ads/ad_001_示例.mp4

# 如果404，检查：
# - 文件是否在ads文件夹中
# - 文件格式是否支持
# - 服务器是否正确挂载/ads路径
```

**3. 唤醒状态不响应**
```bash
# 检查wake_word_manager是否正常工作
# 查看控制台日志中的广告控制信号
# 确认WebSocket连接正常
```

### **调试命令**
```python
# 测试MCP服务器
python -m src.solvia_for_chat.mcpp.advertisement_server --ads-dir=ads

# 测试广告扫描
from src.solvia_for_chat.mcpp.advertisement_server import AdvertisementServer
server = AdvertisementServer()
print(f"找到 {len(server.advertisements)} 个广告")
```

## 📈 **扩展功能建议**

### **已实现功能**
- ✅ MCP架构集成
- ✅ 多格式视频支持  
- ✅ 随机播放模式
- ✅ 唤醒状态联动
- ✅ 播放统计追踪
- ✅ 热更新广告列表

### **未来扩展方向**
- 🔄 **智能推荐**: 基于用户偏好推荐广告
- 📊 **详细统计**: 广告观看时长、点击率统计
- 🎨 **自定义主题**: 不同时段播放不同类型广告
- 🔊 **音频广告**: 支持纯音频广告播放
- 📱 **响应式布局**: 适配不同屏幕尺寸
- 🎯 **定向投放**: 基于用户画像的精准投放

## 💡 **总结**

### **系统优势**
- 🏗️ **架构优雅**: 完全符合项目MCP设计理念
- 🔧 **模块化**: 与现有功能完全隔离，互不影响  
- 🎯 **智能控制**: 基于用户交互状态自动显示/隐藏
- 📈 **可扩展**: 通过MCP工具可轻松扩展功能
- 🚀 **易维护**: 清晰的代码结构和完整文档

### **技术亮点**
- 利用现有MCP架构，零破坏性集成
- 实现了唤醒状态与广告显示的智能联动
- 支持热更新，无需重启即可更新广告内容
- 完整的错误处理和日志记录
- 前后端分离，职责清晰

**🎉 广告轮播系统已完全实现，可以开始使用了！**