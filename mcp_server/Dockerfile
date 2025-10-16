FROM python:3.11-slim

LABEL maintainer="Logstash MCP Server"
LABEL description="Network MCP Server for Logstash Testing Service"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY mcp_server.py .

# 创建非 root 用户并添加到 docker 组
RUN useradd -m -u 1000 mcp && \
    groupadd -g 110 docker && \
    usermod -aG docker mcp && \
    chown -R mcp:mcp /app
USER mcp

# 暴露端口
EXPOSE 19001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:19001/tools/health_check || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:19001", "--workers", "2", "--timeout", "60", "mcp_server:app"]
