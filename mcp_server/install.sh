#!/bin/bash
# Logstash MCP 服务器安装脚本

set -e

echo "🚀 安装 Logstash MCP 服务器..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要 Python 3.8 或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python 版本检查通过: $python_version"

# 创建虚拟环境（可选）
if [ "$1" = "--venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt

echo "✅ 依赖安装完成"

# 设置执行权限
chmod +x logstash_mcp_server.py

echo "🎉 Logstash MCP 服务器安装完成！"
echo ""
echo "📋 使用方法："
echo "1. 启动服务器: python3 logstash_mcp_server.py"
echo "2. 或在 AI 客户端中配置 MCP 服务器"
echo ""
echo "📚 查看文档: cat README.md"
