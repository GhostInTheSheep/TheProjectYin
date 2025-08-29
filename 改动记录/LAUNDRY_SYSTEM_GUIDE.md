# 🧺 洗衣店智能客服系统实现指南

本文档详细说明了为TheProjectYin AI虚拟主播系统添加的洗衣店智能客服功能的所有改动和实现细节。

## 📋 功能概述

### 核心功能
- 🎤 **语音识别洗衣机查询**：用户可以语音询问特定洗衣机的使用方法
- 🎬 **自动视频播放**：系统自动播放对应洗衣机的教程视频
- ⏰ **自动关闭**：视频播放完毕后自动关闭，返回待机状态
- 🔧 **MCP架构集成**：基于现有的MCP（Model Context Protocol）架构实现

### 用户交互流程
1. 用户语音询问："1号洗衣机怎么用？"
2. AI识别意图和机器编号
3. 系统自动播放对应的教程视频
4. 视频播放完毕后自动关闭
5. 返回待机状态，等待下一次询问

---

## 🔧 技术架构

### 系统架构图
```
用户语音输入 → 语音识别 → AI理解(MCP) → 视频播放器 → 自动关闭
     ↓                ↓           ↓            ↓            ↓
   语音API    →    OpenAI    →  洗衣店MCP   →   前端播放器  →  返回待机
```

### MCP服务器架构
- **洗衣店MCP服务器**：独立的Python服务，处理洗衣机查询和视频管理
- **工具集成**：通过MCP协议与主系统通信
- **视频管理**：自动扫描和管理教程视频文件

---

## 📁 文件改动清单

### 1. 后端改动

#### 🆕 新增文件

##### `/src/solvia_for_chat/mcpp/laundry_server.py`
**功能**：洗衣店MCP服务器主体
**关键特性**：
- 自动扫描videos目录中的教程视频
- 提供机器编号识别和匹配功能
- 通过MCP协议提供工具调用接口

**核心工具**：
- `query_machine_tutorial`: 查询特定洗衣机教程
- `list_available_machines`: 列出所有可用洗衣机
- `welcome_message`: 获取欢迎消息

```python
# 主要功能示例
def _extract_machine_number_from_text(self, text: str) -> Optional[str]:
    """从用户输入文本中提取机器编号"""
    patterns = [
        r'(\d+)[号台](?:洗衣机|机器)?',
        r'([A-Z]\d*)[号台](?:洗衣机|机器)?',
        # ... 更多模式
    ]
```

##### `/src/solvia_for_chat/conversations/laundry_handler.py`
**功能**：洗衣店对话处理器
**关键特性**：
- 识别洗衣店相关查询
- 格式化MCP工具调用
- 处理工具返回结果

```python
def is_laundry_related_query(self, user_input: str) -> bool:
    """判断是否为洗衣店相关查询"""
    laundry_keywords = [
        '洗衣机', '洗衣', 'washing', 'machine', 
        '怎么用', '如何使用', '使用方法', '教程'
    ]
```

#### 📝 修改文件

##### `/mcp_servers.json`
**改动**：添加洗衣店MCP服务器配置
```json
{
  "mcp_servers": {
    "laundry-assistant": {
      "command": "python",
      "args": ["-m", "src.solvia_for_chat.mcpp.laundry_server", "--videos-dir=videos"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

##### `/conf.yaml`
**改动**：启用MCP功能并添加洗衣店服务器
```yaml
agent_settings:
  basic_memory_agent:
    use_mcpp: True  # 从 False 改为 True
    mcp_enabled_servers: ["time", "ddg-search", "laundry-assistant"]
```

### 2. 前端改动

#### 🆕 新增文件

##### `/frontend/Frontend-AI/src/renderer/src/components/laundry/video-player.tsx`
**功能**：全屏视频播放器组件
**关键特性**：
- 全屏播放支持
- 自动播放和自动关闭
- 播放控制（播放/暂停、音量）
- 鼠标交互和控制栏自动隐藏

```tsx
export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  src,
  title = "视频教程",
  autoPlay = true,
  autoClose = true,
  onClose,
  onEnded
}) => {
  // 视频播放逻辑
}
```

##### `/frontend/Frontend-AI/src/renderer/src/context/laundry-context.tsx`
**功能**：洗衣店状态管理上下文
**关键特性**：
- 洗衣店模式状态管理
- 视频播放状态管理
- 可用洗衣机列表管理
- 自动关闭配置

```tsx
export interface LaundryContextType {
  isLaundryMode: boolean;
  currentVideo: string | null;
  videoTitle: string;
  isVideoPlaying: boolean;
  availableMachines: MachineInfo[];
  // ... 更多状态
}
```

#### 📝 修改文件

##### `/frontend/Frontend-AI/src/renderer/src/App.tsx`
**改动**：
1. 添加LaundryProvider包装
2. 集成VideoPlayer组件
3. 重构为AppContent + App结构

```tsx
function App(): JSX.Element {
  return (
    <LaundryProvider>
      <AppContent />
    </LaundryProvider>
  );
}

// 在AppContent中添加视频播放器
{currentVideo && (
  <VideoPlayer
    src={currentVideo}
    title={videoTitle}
    autoPlay={true}
    autoClose={true}
    onClose={() => setCurrentVideo(null)}
  />
)}
```

##### `/frontend/Frontend-AI/src/renderer/src/services/websocket-handler.tsx`
**改动**：
1. 导入洗衣店上下文
2. 添加洗衣店消息处理

```tsx
import { useLaundry } from '@/context/laundry-context';

// 在消息处理switch中添加
case 'laundry-video-response':
  if (isLaundryMode && message.video_path) {
    const videoTitle = message.machine_id ? 
      `${message.machine_id}号洗衣机使用教程` : 
      '洗衣机使用教程';
    setCurrentVideo(message.video_path, videoTitle);
  }
  break;
```

### 3. 配置和工具文件

#### 🆕 新增文件

##### `/videos/README.md`
**功能**：视频目录使用说明
**内容**：
- 文件命名规范
- 支持的视频格式
- 使用说明

##### `/install_laundry_features.py`
**功能**：自动安装和配置脚本
**功能**：
- 检查和安装依赖
- 创建必要目录
- 更新配置文件
- 创建systemd服务

```python
def main():
    check_dependencies()
    create_directories()
    create_sample_videos()
    update_mcp_config()
    update_main_config()
    install_frontend_dependencies()
    create_systemd_service()
```

---

## 🚀 部署指南

### 1. 安装依赖

```bash
# 安装MCP依赖
pip install mcp

# 或使用自动安装脚本
python install_laundry_features.py
```

### 2. 配置视频文件

```bash
# 创建视频目录
mkdir -p videos

# 添加教程视频（按照命名规范）
# videos/machine_1.mp4  - 1号洗衣机教程
# videos/machine_2.mp4  - 2号洗衣机教程  
# videos/machine_A.mp4  - A号洗衣机教程
```

### 3. 启动服务

```bash
# 重启主服务
sudo systemctl restart theprojectyin

# 检查状态
sudo systemctl status theprojectyin

# 查看日志
sudo journalctl -u theprojectyin -f
```

### 4. 测试功能

1. **访问Web界面**：`http://your-server-ip:12393`
2. **允许麦克风权限**
3. **语音测试**：
   - "1号洗衣机怎么用？"
   - "请问A号洗衣机如何操作？"
   - "有哪些洗衣机可以使用？"

---

## 🔍 技术细节

### MCP工具调用流程

1. **用户输入识别**
   ```
   用户："1号洗衣机怎么用？"
   ↓
   语音识别：文本转换
   ↓
   AI处理：OpenAI GPT-4o
   ```

2. **MCP工具调用**
   ```
   AI决策：调用洗衣店工具
   ↓
   工具调用：query_machine_tutorial
   ↓
   参数：{"user_input": "1号洗衣机怎么用？"}
   ```

3. **洗衣店服务器处理**
   ```
   提取机器编号：1
   ↓
   查找视频：videos/machine_1.mp4
   ↓
   返回结果：视频路径和元数据
   ```

4. **前端响应**
   ```
   WebSocket消息：laundry-video-response
   ↓
   触发VideoPlayer组件
   ↓
   全屏播放视频
   ```

### 视频播放器特性

1. **自动播放控制**
   ```tsx
   useEffect(() => {
     const video = videoRef.current;
     if (autoPlay) {
       video.play();
       setIsPlaying(true);
     }
   }, [autoPlay]);
   ```

2. **自动关闭机制**
   ```tsx
   const handleEnded = () => {
     setIsPlaying(false);
     if (autoClose) {
       setTimeout(() => {
         if (onClose) onClose();
       }, 3000); // 3秒后自动关闭
     }
   };
   ```

3. **控制栏自动隐藏**
   ```tsx
   useEffect(() => {
     let timer = setTimeout(() => {
       if (isPlaying) setShowControls(false);
     }, 3000);
     
     return () => clearTimeout(timer);
   }, [isPlaying]);
   ```

---

## 🎯 支持的查询模式

### 语音识别模式

| 用户输入 | 识别结果 | 系统响应 |
|---------|---------|---------|
| "1号洗衣机怎么用？" | 机器ID: 1 | 播放machine_1.mp4 |
| "A号洗衣机如何操作？" | 机器ID: A | 播放machine_A.mp4 |
| "第2台洗衣机的使用方法" | 机器ID: 2 | 播放machine_2.mp4 |
| "有哪些洗衣机？" | 列表查询 | 显示可用洗衣机列表 |

### 正则表达式模式

```python
patterns = [
    r'(\d+)[号台](?:洗衣机|机器)?',      # "1号洗衣机"
    r'([A-Z]\d*)[号台](?:洗衣机|机器)?',  # "A号洗衣机"
    r'(?:洗衣机|机器)[号台]?[_-]?([A-Z]?\d+)', # "洗衣机1"
    r'machine[_-]?([A-Z]?\d+)',          # "machine_1"
    r'第(\d+)台',                        # "第1台"
]
```

---

## 🛠️ 自定义和扩展

### 添加新的洗衣机

1. **添加视频文件**
   ```bash
   # 按照命名规范添加视频
   cp your_tutorial.mp4 videos/machine_C.mp4
   ```

2. **重启MCP服务器**
   ```bash
   # 系统会自动扫描新视频
   sudo systemctl restart theprojectyin
   ```

### 自定义识别模式

修改 `/src/solvia_for_chat/mcpp/laundry_server.py`：

```python
def _extract_machine_id_from_filename(self, filename: str) -> Optional[str]:
    # 添加自定义模式
    custom_patterns = [
        r'custom_pattern_(\w+)',  # 自定义模式
        # ...
    ]
    patterns.extend(custom_patterns)
```

### 自定义响应消息

修改 `/src/solvia_for_chat/conversations/laundry_handler.py`：

```python
def generate_welcome_message(self) -> str:
    return "欢迎来到XXX洗衣店！我是智能助手..."  # 自定义欢迎消息
```

---

## 🐛 故障排除

### 常见问题

1. **视频不播放**
   ```bash
   # 检查视频文件是否存在
   ls -la videos/

   # 检查MCP服务器日志
   sudo journalctl -u theprojectyin -f | grep laundry
   ```

2. **语音识别不准确**
   ```yaml
   # 调整VAD设置（conf.yaml）
   vad_config:
     silero_vad:
       prob_threshold: 0.6  # 提高阈值
   ```

3. **MCP服务器无法启动**
   ```bash
   # 手动测试MCP服务器
   cd /opt/TheProjectYin
   python -m src.solvia_for_chat.mcpp.laundry_server --videos-dir=videos
   ```

### 日志检查

```bash
# 主服务日志
sudo journalctl -u theprojectyin -f

# 应用日志
tail -f logs/debug_*.log

# MCP相关日志
sudo journalctl -u theprojectyin -f | grep -i mcp
```

---

## 📈 性能优化

### 视频文件优化

1. **推荐格式**：MP4 (H.264编码)
2. **分辨率**：1920x1080或1280x720
3. **文件大小**：建议每分钟不超过50MB
4. **压缩建议**：
   ```bash
   # 使用ffmpeg压缩视频
   ffmpeg -i input.mp4 -vcodec h264 -acodec aac -crf 23 output.mp4
   ```

### 系统性能

1. **内存优化**：视频播放时会占用额外内存
2. **存储优化**：定期清理临时文件
3. **网络优化**：本地存储视频文件，避免网络延迟

---

## 🔒 安全考虑

### 文件安全

1. **视频文件权限**
   ```bash
   chmod 644 videos/*.mp4
   chown root:root videos/*.mp4
   ```

2. **目录权限**
   ```bash
   chmod 755 videos/
   ```

### 访问控制

1. **MCP服务器**：仅本地访问
2. **视频文件**：通过应用层控制访问
3. **日志记录**：记录所有查询操作

---

## 📞 技术支持

### 联系方式
- 📧 技术支持邮箱：[技术支持邮箱]
- 📱 支持热线：[支持电话]
- 💬 在线文档：[文档链接]

### 更新日志
- **v1.0.0** (2025-01-08): 初始版本发布
  - ✅ 基础洗衣店客服功能
  - ✅ MCP架构集成
  - ✅ 视频播放器组件
  - ✅ 自动安装脚本

---

## 📝 开发备注

本实现基于TheProjectYin现有的MCP架构，充分利用了系统的模块化设计。所有改动都保持了向后兼容性，不影响现有功能的正常运行。

### 核心设计原则
1. **模块化**：使用MCP架构实现功能隔离
2. **可扩展**：易于添加新的洗衣机和功能
3. **用户友好**：自然语言交互，自动化流程
4. **稳定性**：错误处理和兜底机制
5. **性能**：优化视频播放和系统响应

### 技术栈
- **后端**：Python, FastAPI, MCP, WebSocket
- **前端**：React, TypeScript, Chakra UI
- **视频**：HTML5 Video API
- **AI**：OpenAI GPT-4o
- **语音**：Sherpa-ONNX (ASR), Fish TTS

---

*本文档会随着功能更新而持续维护更新。*