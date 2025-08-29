#!/usr/bin/env python3
"""
洗衣店智能客服功能安装脚本
自动配置系统以支持洗衣店功能
"""

import os
import json
import shutil
import sys
from pathlib import Path


def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    try:
        import mcp
        print("✅ MCP库已安装")
    except ImportError:
        print("❌ MCP库未安装，正在安装...")
        os.system("pip install mcp")
    
    print("✅ 依赖检查完成")


def create_directories():
    """创建必要的目录"""
    print("📁 创建目录结构...")
    
    directories = [
        "videos",
        "videos/machine_1",
        "videos/machine_2", 
        "videos/machine_A",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    print("✅ 目录创建完成")


def create_sample_videos():
    """创建示例视频文件（用于测试）"""
    print("🎬 创建示例视频文件...")
    
    sample_videos = [
        "videos/machine_1.mp4",
        "videos/machine_2.mp4", 
        "videos/machine_A.mp4"
    ]
    
    for video_path in sample_videos:
        if not Path(video_path).exists():
            # 创建空文件作为占位符
            Path(video_path).touch()
            print(f"   ✅ {video_path} (占位符文件)")
    
    print("✅ 示例视频文件创建完成")
    print("⚠️  请将真实的教程视频文件替换占位符文件")


def update_mcp_config():
    """更新MCP服务器配置"""
    print("⚙️ 更新MCP配置...")
    
    config_file = "mcp_servers.json"
    
    if Path(config_file).exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {"mcp_servers": {}}
    
    # 添加洗衣店服务器配置
    config["mcp_servers"]["laundry-assistant"] = {
        "command": "python",
        "args": ["-m", "src.solvia_for_chat.mcpp.laundry_server", "--videos-dir=videos"],
        "env": {
            "PYTHONPATH": "."
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ MCP配置更新完成")


def update_main_config():
    """更新主配置文件"""
    print("⚙️ 更新主配置文件...")
    
    config_file = "conf.yaml"
    
    if not Path(config_file).exists():
        print("❌ conf.yaml文件不存在")
        return
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新MCP配置
    if "use_mcpp: False" in content:
        content = content.replace("use_mcpp: False", "use_mcpp: True")
        print("   ✅ 启用MCP功能")
    
    if "laundry-assistant" not in content:
        content = content.replace(
            'mcp_enabled_servers: ["time", "ddg-search"]',
            'mcp_enabled_servers: ["time", "ddg-search", "laundry-assistant"]'
        )
        print("   ✅ 添加洗衣店服务器到启用列表")
    
    # 写回配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 主配置文件更新完成")


def create_systemd_service():
    """创建系统服务（Linux）"""
    if sys.platform != "linux":
        print("⏭️  跳过systemd服务创建（非Linux系统）")
        return
    
    print("🔧 创建systemd服务...")
    
    service_content = """[Unit]
Description=TheProjectYin Laundry Assistant
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/TheProjectYin
Environment=PATH=/opt/TheProjectYin/tf-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/TheProjectYin/tf-env/bin/python run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "/etc/systemd/system/theprojectyin-laundry.service"
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        os.system("systemctl daemon-reload")
        print(f"✅ systemd服务已创建: {service_file}")
        print("   可以使用以下命令管理服务:")
        print("   sudo systemctl start theprojectyin-laundry")
        print("   sudo systemctl enable theprojectyin-laundry")
        
    except PermissionError:
        print("⚠️  需要root权限创建systemd服务")


def install_frontend_dependencies():
    """安装前端依赖"""
    print("📦 检查前端依赖...")
    
    frontend_dir = Path("frontend/Frontend-AI")
    if frontend_dir.exists():
        print("   ✅ 前端目录存在")
        
        # 检查是否需要安装依赖
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("   📦 安装前端依赖...")
            os.chdir(frontend_dir)
            os.system("npm install")
            os.chdir("../..")
            print("   ✅ 前端依赖安装完成")
        else:
            print("   ✅ 前端依赖已存在")
    else:
        print("   ⚠️  前端目录不存在，跳过前端依赖安装")


def print_success_message():
    """打印成功消息"""
    print("\n" + "="*60)
    print("🎉 洗衣店智能客服功能安装完成！")
    print("="*60)
    print()
    print("📋 接下来的步骤：")
    print()
    print("1. 📽️  将洗衣机教程视频放入 videos/ 目录")
    print("   - 命名格式：machine_1.mp4, machine_2.mp4, machine_A.mp4")
    print("   - 支持格式：MP4, AVI, MOV, MKV")
    print()
    print("2. 🔄 重启服务器")
    print("   sudo systemctl restart theprojectyin")
    print()
    print("3. 🗣️  测试语音功能")
    print("   说出：\"1号洗衣机怎么用？\"")
    print("   说出：\"请问A号洗衣机如何操作？\"")
    print()
    print("4. 🎛️  管理服务")
    print("   查看状态：sudo systemctl status theprojectyin")
    print("   查看日志：sudo journalctl -u theprojectyin -f")
    print()
    print("📞 如果遇到问题，请检查日志文件或联系技术支持")
    print("="*60)


def main():
    """主函数"""
    print("🤖 洗衣店智能客服功能安装程序")
    print("="*40)
    print()
    
    try:
        check_dependencies()
        create_directories()
        create_sample_videos()
        update_mcp_config()
        update_main_config()
        install_frontend_dependencies()
        create_systemd_service()
        print_success_message()
        
    except Exception as e:
        print(f"❌ 安装过程中出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()