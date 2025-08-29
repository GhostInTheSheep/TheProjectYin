# 🇯🇵 洗衣机系统日本本地化解决方案

## 问题描述

原有洗衣机系统在播放教程视频时会说出中文语音"好的，为您播放{machine_id}号洗衣机的使用教程。"，这对于面向日本用户的自助洗衣店是不合适的。

## 解决方案

### 1. 新增语言模式支持

在 `src/solvia_for_chat/mcpp/laundry_server.py` 中新增了多语言响应支持：

```python
# 支持的语言模式
- "auto": 自动检测（默认）
- "zh": 中文响应  
- "ja": 日语响应
- "en": 英语响应
- "silent": 静默模式（无语音）
```

### 2. 静默模式实现

当设置为 `silent` 模式时：
- `response_text` 为空字符串
- `silent_mode` 标志设为 `true`
- 前端收到响应后直接播放视频，不播放TTS语音

### 3. 配置文件更新

在 `conf.yaml` 中新增洗衣机系统配置：

```yaml
system_config:
  # 洗衣机系统配置 - 针对不同地区和语言的配置
  laundry_system:
    region: "japan"  # 地区设置
    language_mode: "silent"  # 语言模式
```

### 4. 日语支持

为日语用户提供适当的响应文本：
```python
response_text = f"{machine_id}番の洗濯機の使用方法をご案内いたします。"
```

## 修改的文件

### 后端文件

1. **`src/solvia_for_chat/mcpp/laundry_server.py`**
   - 新增 `language` 参数支持
   - 实现多语言响应逻辑
   - 从配置文件读取默认语言设置

2. **`src/solvia_for_chat/conversations/laundry_handler.py`**
   - 新增 `detect_language_mode()` 方法
   - 更新 `format_mcp_tool_call()` 支持语言参数
   - 新增 `silent_mode` 处理

### 前端文件

3. **`frontend/Frontend-AI/src/renderer/src/services/websocket-handler.tsx`**
   - 新增静默模式检测和处理逻辑
   - 添加调试日志输出

### 配置文件

4. **`conf.yaml`**
   - 新增 `laundry_system` 配置部分
   - 默认设置为日本地区和静默模式

## 使用方法

### 为日本地区配置

1. **编辑 `conf.yaml`**：
```yaml
system_config:
  laundry_system:
    region: "japan"
    language_mode: "silent"  # 静默模式，无语音提示
```

2. **重启服务**：
```bash
# 重启TheProjectYin服务
sudo systemctl restart theprojectyin
```

### 其他语言模式

- **中文环境**：`language_mode: "zh"`
- **日语环境**：`language_mode: "ja"`  
- **英语环境**：`language_mode: "en"`
- **自动检测**：`language_mode: "auto"`

## 测试验证

### 测试静默模式

1. 确保配置为静默模式
2. 访问系统Web界面
3. 语音询问："1号洗衣机怎么用？"
4. 预期结果：
   - ✅ 直接播放视频，无语音提示
   - ✅ 控制台显示 "🔇 静默模式: 是"
   - ✅ 视频正常播放和自动关闭

### 测试日语模式

1. 设置 `language_mode: "ja"`
2. 重启服务
3. 语音询问洗衣机使用方法
4. 预期结果：
   - ✅ 播放日语语音："{machine_id}番の洗濯機の使用方法をご案内いたします。"

## 技术细节

### 配置读取机制

```python
# 从配置文件读取语言模式
if language == "auto":
    try:
        import yaml
        config_path = Path("conf.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                laundry_config = yaml_config.get('system_config', {}).get('laundry_system', {})
                language = laundry_config.get('language_mode', 'auto')
    except Exception as e:
        print(f"Warning: Could not read laundry config: {e}")
        language = "auto"
```

### 前端静默模式检测

```tsx
// 检查是否为静默模式
if (message.silent_mode && message.response_text) {
    console.log(`🔇 静默模式已启用，跳过语音播放: "${message.response_text}"`);
    // 静默模式下直接播放视频，不播放TTS语音
}
```

## 向后兼容性

- ✅ 默认保持原有行为（`language_mode: "auto"`）
- ✅ 现有中文用户不受影响
- ✅ 可通过配置灵活切换模式

## 部署说明

### 日本洗衣店部署

1. 使用提供的配置模板
2. 确保设置 `region: "japan"` 和 `language_mode: "silent"`
3. 测试验证静默模式正常工作
4. 部署到生产环境

### 多地区支持

系统现在支持为不同地区提供不同的语言配置，可以根据实际需求灵活调整。

---

## 总结

通过这次修改，洗衣机系统现在完全支持日本地区的静默模式使用，解决了中文语音不适合的问题。用户可以通过简单的配置更改来适配不同的地区和语言需求。
