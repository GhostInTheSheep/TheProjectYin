## Linux 系统级依赖（非 pip）

在 Linux 服务器上运行本项目，除了 `requirements.linux.txt` 的 pip 依赖外，建议安装以下系统级组件：

### 必需/强烈建议
- ffmpeg
  - 供 `pydub`/音视频处理使用。
  - Ubuntu/Debian：`sudo apt install -y ffmpeg`
- libsndfile
  - `soundfile` 在个别环境需要系统库支持。
  - Ubuntu/Debian：`sudo apt install -y libsndfile1`

### 可能需要
- build-essential / gcc / g++ 及 Python 头文件
  - 某些轮子缺失或需源码构建时使用。
  - Ubuntu/Debian：`sudo apt install -y build-essential python3-dev`
- libasound2 / pulseaudio 工具
  - 若服务器需要本地音频 I/O（通常不需要）。
  - Ubuntu/Debian：`sudo apt install -y alsa-utils pulseaudio`

### Torch/GPU（可选）
- 如果使用 GPU，请按 PyTorch 官方说明安装与你 CUDA 版本匹配的轮子，然后再安装本项目依赖。

安装示例（最小集）：
```bash
sudo apt update
sudo apt install -y ffmpeg libsndfile1
```
