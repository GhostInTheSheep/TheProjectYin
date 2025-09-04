FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# 常用运行依赖（证书等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖清单以利用缓存
COPY requirements.linux.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝项目代码
COPY . ${APP_HOME}

EXPOSE 12393

# 健康检查（可被 compose 覆盖）
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:12393/web-tool', timeout=3)" || exit 1

# 后端入口
CMD ["python", "run_server.py"]

ENV PYTHONPATH=/app
