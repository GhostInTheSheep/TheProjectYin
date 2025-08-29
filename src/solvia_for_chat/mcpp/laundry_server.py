#!/usr/bin/env python3
"""
洗衣店智能客服 MCP 服务器
提供洗衣机查询和视频播放功能
"""

import json
import re
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types
from pydantic import AnyUrl


class SimpleMediaConfig:
    """简化的媒体配置类，用于独立MCP服务器"""
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12393
        self.ads_directory = "ads"
        self.videos_directory = "videos"
    
    def get_directory_path(self, directory_type: str):
        """获取指定类型目录的路径"""
        if directory_type == 'ads':
            return Path(self.ads_directory)
        elif directory_type == 'videos':
            return Path(self.videos_directory)
        else:
            raise ValueError(f"Unknown directory type: {directory_type}")
    
    def get_video_url(self, category: str, filename: str) -> str:
        """生成视频文件的URL"""
        return f"http://{self.host}:{self.port}/{category}/{filename}"


def get_media_config():
    """获取媒体服务器配置"""
    # 直接使用简化配置，不依赖复杂的系统配置
    try:
        import yaml
        from pathlib import Path
        
        config_path = Path("conf.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                system_config = yaml_config.get('system_config', {})
                media_server_config = system_config.get('media_server', {})
                
                # 创建简化配置对象
                config = SimpleMediaConfig()
                config.host = media_server_config.get('host', '127.0.0.1')
                config.port = media_server_config.get('port', 12393)
                config.ads_directory = media_server_config.get('ads_directory', 'ads')
                config.videos_directory = media_server_config.get('videos_directory', 'videos')
                
                print(f"✅ Loaded media config from YAML: host={config.host}, port={config.port}")
                return config
    except Exception as yaml_error:
        print(f"⚠️ Warning: Failed to load YAML config: {yaml_error}")
    
    # 最后的fallback
    print("ℹ️ Using default media configuration")
    return SimpleMediaConfig()


class LaundryServer:
    """洗衣店智能客服服务器"""
    
    def __init__(self, videos_dir: str = "videos"):
        self.server = Server("laundry-assistant")
        
        # 获取媒体配置
        self.media_config = get_media_config()
        try:
            self.videos_dir = self.media_config.get_directory_path('videos')
        except:
            # Fallback to provided directory
            self.videos_dir = Path(videos_dir)
        
        self.machine_videos = {}
        self.welcome_messages = {
            "zh": "欢迎来到自动洗衣店！请问您需要了解哪台洗衣机的使用方法？",
            "ja": "セルフランドリーへようこそ！どちらの洗濯機の使用方法をご案内いたしますか？",
            "en": "Welcome to the laundromat! Which washing machine would you like to know how to use?"
        }
        # 默认语言模式（仅在启动时读取一次配置并缓存）
        self.default_language_mode = "auto"
        try:
            import yaml
            config_path = Path("conf.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    laundry_config = yaml_config.get('system_config', {}).get('laundry_system', {})
                    self.default_language_mode = laundry_config.get('language_mode', 'auto')
        except Exception as _e:
            # 保持默认值
            pass
        
        # 确保视频目录存在
        self.videos_dir.mkdir(exist_ok=True)
        
        # 扫描可用的洗衣机视频
        self._scan_machine_videos()
        
        # 注册工具和资源
        self._register_tools()
        self._register_resources()

    def _scan_machine_videos(self):
        """扫描视频目录，发现可用的洗衣机教程视频"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        
        for video_file in self.videos_dir.iterdir():
            if video_file.suffix.lower() in video_extensions:
                # 解析文件名提取机器编号
                machine_id = self._extract_machine_id_from_filename(video_file.name)
                if machine_id:
                    self.machine_videos[machine_id] = {
                        'path': str(video_file),
                        'name': video_file.stem,
                        'exists': True
                    }
        
        print(f"🎬 検出された洗濯機チュートリアル動画: {len(self.machine_videos)}個")
        for machine_id, info in self.machine_videos.items():
            print(f"  - 💻 {machine_id}番機: {info['name']}")

    def _extract_machine_id_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取机器编号"""
        patterns = [
            r'machine[_-]?(\w+)',
            r'洗衣机[_-]?(\w+)',
            r'washing[_-]?machine[_-]?(\w+)',
            r'^(\d+)[号台]?',
            r'^([A-Z]\d*)[号台]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None

    def _extract_machine_number_from_text(self, text: str) -> Optional[str]:
        """从用户输入文本中提取机器编号"""
        # 清理文本
        text = text.strip()
        
        # 首先处理中文数字转换
        chinese_numbers = {
            '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
        }
        
        # 日语数字转换
        japanese_numbers = {
            '一番': '1', '二番': '2', '三番': '3', '四番': '4', '五番': '5',
            '六番': '6', '七番': '7', '八番': '8', '九番': '9', '十番': '10',
            '１番': '1', '２番': '2', '３番': '3', '４番': '4', '５番': '5',
            '６番': '6', '７番': '7', '８番': '8', '９番': '9', '１０番': '10'
        }
        
        # 转换中文数字
        for chinese, arabic in chinese_numbers.items():
            text = text.replace(chinese, arabic)
        
        # 转换日语数字
        for japanese, arabic in japanese_numbers.items():
            text = text.replace(japanese, arabic)
        
        # 匹配模式 - 添加更多日语模式
        patterns = [
            # 日语模式
            r'(\d+)[番号台](?:の)?(?:洗濯機|機械|マシン)?',
            r'([A-Z]\d*)[番号台](?:の)?(?:洗濯機|機械|マシン)?',
            r'(?:洗濯機|機械|マシン)[番号台]?[_-]?([A-Z]?\d+)',
            r'(\d+)番(?:の)?(?:洗濯機|機械|使い方|マシン)?',
            r'([A-Z])番(?:の)?(?:洗濯機|機械|使い方|マシン)?',
            # 中文模式
            r'(\d+)[号台](?:洗衣机|机器)?',
            r'([A-Z]\d*)[号台](?:洗衣机|机器)?',
            r'(?:洗衣机|机器)[号台]?[_-]?([A-Z]?\d+)',
            r'第(\d+)台',
            r'(\d+)号',
            # 英语模式
            r'machine[_-]?([A-Z]?\d+)',
            r'([A-Z]?\d+)[_-]?machine'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1).upper()
                print(f"Debug: 从文本 '{text}' 中提取到机器编号: '{result}' (模式: {pattern})")
                return result
        
        # 如果找不到明确的编号，尝试提取纯数字或字母
        simple_patterns = [
            r'\b([A-Z]\d+)\b',
            r'\b(\d+)\b'
        ]
        
        for pattern in simple_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result = matches[0].upper()
                print(f"Debug: 从文本 '{text}' 中提取到简单编号: '{result}' (模式: {pattern})")
                return result
        
        print(f"Debug: 无法从文本 '{text}' 中提取机器编号")
        return None

    def _register_tools(self):
        """注册MCP工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """返回可用的工具列表"""
            return [
                types.Tool(
                    name="query_machine_tutorial",
                    description="查询特定洗衣机的使用教程视频",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_input": {
                                "type": "string",
                                "description": "用户的询问内容，比如'1号洗衣机怎么用'"
                            },
                            "language": {
                                "type": "string",
                                "description": "响应语言模式：'auto'(自动), 'zh'(中文), 'ja'(日语), 'en'(英语), 'silent'(静默无语音)",
                                "default": "auto"
                            }
                        },
                        "required": ["user_input"]
                    }
                ),
                types.Tool(
                    name="list_available_machines",
                    description="列出所有可用的洗衣机",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="welcome_message",
                    description="获取洗衣店欢迎消息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "description": "语言代码，如'zh'或'en'",
                                "default": "ja"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="refresh_machine_videos",
                    description="重新扫描videos目录，刷新洗衣机教程视频列表",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """处理工具调用"""
            if name == "query_machine_tutorial":
                return await self._query_machine_tutorial(arguments)
            elif name == "list_available_machines":
                return await self._list_available_machines(arguments)
            elif name == "welcome_message":
                return await self._welcome_message(arguments)
            elif name == "refresh_machine_videos":
                return await self._refresh_machine_videos(arguments)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
    
    async def _query_machine_tutorial(self, arguments: dict) -> list[types.TextContent]:
        """查询洗衣机使用教程"""
        user_input = arguments.get("user_input", "")
        
        if not user_input:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "type": "text_response",
                    "content": "どちらの洗濯機の使用方法をお知りになりたいですか？",
                    "suggestions": list(self.machine_videos.keys())
                }, ensure_ascii=False)
            )]
        
        # 提取机器编号
        machine_id = self._extract_machine_number_from_text(user_input)
        
        if not machine_id:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "type": "text_response",
                    "content": "申し訳ございません。どちらの洗濯機についてお尋ねかわかりませんでした。具体的な機械番号をお知らせください。例：'1番洗濯機'、'A番洗濯機'",
                    "available_machines": list(self.machine_videos.keys())
                }, ensure_ascii=False)
            )]
        
        # 检查是否有对应的视频
        if machine_id in self.machine_videos:
            video_info = self.machine_videos[machine_id]
            # 转换文件系统路径为完整的后端服务器URL
            web_video_path = f"/videos/{Path(video_info['path']).name}"  # 使用相对路径，自动适应任何域名
            
            # 支持多语言响应（已移除静默模式）
            language = arguments.get("language", "auto")  # auto, zh, ja, en
            
            # 如果language为auto，使用启动时缓存的默认语言模式，避免每次查询读盘
            if language == "auto":
                language = self.default_language_mode
            
            if language == "ja":
                response_text = f"{machine_id}番の洗濯機の使用方法をご案内いたします。"
            elif language == "en":
                response_text = f"Here's the tutorial for washing machine {machine_id}."
            else:
                # 默认日语或自动检测 - 面向日本客户
                response_text = f"かしこまりました。{machine_id}番洗濯機の使用方法をご案内いたします。"
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "type": "video_response",
                    "machine_id": machine_id,
                    "video_path": web_video_path,
                    "video_name": video_info["name"],
                    "response_text": response_text,
                    "auto_close": True
                }, ensure_ascii=False)
            )]
        else:
            return [types.TextContent(
                type="text", 
                text=json.dumps({
                    "type": "text_response",
                    "content": f"申し訳ございません。{machine_id}番洗濯機の使用方法の動画が見つかりませんでした。",
                    "available_machines": list(self.machine_videos.keys())
                }, ensure_ascii=False)
            )]

    async def _list_available_machines(self, arguments: dict) -> list[types.TextContent]:
        """列出所有可用的洗衣机"""
        machines_list = []
        for machine_id, info in self.machine_videos.items():
            machines_list.append(f"{machine_id}番洗濯機 - {info['name']}")
        
        if machines_list:
            content = "ご利用可能な洗濯機：\n" + "\n".join(machines_list)
        else:
            content = "現在、利用可能な洗濯機のチュートリアル動画はございません。"
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "type": "text_response",
                "content": content,
                "machines": list(self.machine_videos.keys())
            }, ensure_ascii=False)
        )]

    async def _welcome_message(self, arguments: dict) -> list[types.TextContent]:
        """获取欢迎消息"""
        language = arguments.get("language", "ja")  # 日本向けなのでデフォルトを日本語に
        welcome_text = self.welcome_messages.get(language, self.welcome_messages["ja"])
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "type": "text_response",
                "content": welcome_text,
                "available_machines": list(self.machine_videos.keys())
            }, ensure_ascii=False)
        )]

    async def _refresh_machine_videos(self, arguments: dict) -> list[types.TextContent]:
        """刷新洗衣机教程视频列表"""
        old_count = len(self.machine_videos)
        self._scan_machine_videos()
        new_count = len(self.machine_videos)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "type": "refresh_response",
                "old_count": old_count,
                "new_count": new_count,
                "message": f"洗濯機チュートリアルリストを更新しました: {old_count} → {new_count}",
                "machines": list(self.machine_videos.keys())
            }, ensure_ascii=False)
        )]

    def _register_resources(self):
        """注册MCP资源"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """
            列出所有可用的视频资源
            """
            resources = []
            
            for machine_id, info in self.machine_videos.items():
                resources.append(types.Resource(
                    uri=AnyUrl(f"laundry://machine/{machine_id}"),
                    name=f"洗濯機 {machine_id}番 使用方法",
                    description=f"{machine_id}番洗濯機の詳細な使用方法のチュートリアル動画",
                    mimeType="video/mp4"
                ))
            
            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            """
            读取视频资源信息
            """
            uri_str = str(uri)
            
            if uri_str.startswith("laundry://machine/"):
                machine_id = uri_str.split("/")[-1]
                
                if machine_id in self.machine_videos:
                    video_info = self.machine_videos[machine_id]
                    # 转换文件系统路径为完整的后端服务器URL
                    web_video_path = f"/videos/{Path(video_info['path']).name}"  # 使用相对路径，自动适应任何域名
                    return json.dumps({
                        "machine_id": machine_id,
                        "video_path": web_video_path,
                        "name": video_info["name"],
                        "description": f"{machine_id}番洗濯機使用方法のチュートリアル"
                    }, ensure_ascii=False)
            
            raise ValueError(f"Unknown resource: {uri}")

    async def run(self):
        """运行服务器"""
        from mcp.server.stdio import stdio_server
        
        try:
            print("🔌 Starting stdio server...")
            async with stdio_server() as (read_stream, write_stream):
                print("✅ Stdio server started, initializing MCP server...")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="laundry-assistant",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except (asyncio.CancelledError, KeyboardInterrupt) as e:
            print(f"🛑 Laundry server stopped gracefully: {type(e).__name__}")
            return  # 正常退出，不重新抛出异常
        except Exception as e:
            print(f"❌ Laundry server error: {e}")
            import traceback
            traceback.print_exc()
            raise  # 重新抛出异常以触发重试


async def main():
    """主函数 - 带有自动重启机制"""
    parser = argparse.ArgumentParser(description="ランドリー店スマートカスタマーサービス MCP サーバー")
    parser.add_argument(
        "--videos-dir", 
        default="videos", 
        help="動画ファイルディレクトリのパス"
    )
    
    args = parser.parse_args()
    
    # 自动重启机制
    max_retries = 10
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            print(f"🚀 启动洗衣机MCP服务器 (尝试 {attempt + 1}/{max_retries})")
            server = LaundryServer(videos_dir=args.videos_dir)
            await server.run()
            break  # 正常退出，不重启
            
        except (asyncio.CancelledError, KeyboardInterrupt):
            print("🛑 洗衣机MCP服务器被手动停止")
            break
            
        except Exception as e:
            print(f"❌ 洗衣机MCP服务器错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                print(f"⏳ {retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)  # 指数退避，最大30秒
            else:
                print("💀 洗衣机MCP服务器重试次数用尽，退出")
                raise


if __name__ == "__main__":
    asyncio.run(main())