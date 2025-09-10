#!/bin/bash
# Logstash Network MCP Server Docker 启动脚本

set -e

echo "🚀 启动 Logstash Network MCP Server..."

# 获取当前目录
CURRENT_DIR=$(pwd)
PROJECT_ROOT=$(dirname "$CURRENT_DIR")

echo "📂 项目根目录: $PROJECT_ROOT"

# 构建并启动服务
echo "🔨 构建 MCP 服务器..."
cd "$PROJECT_ROOT"
docker-compose build mcp-server

echo "🚀 启动所有服务..."
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 10

echo "🔍 检查服务状态..."
docker-compose ps

echo "💚 健康检查..."
echo "Logstash 测试服务:"
curl -s http://localhost:19000/get_parsed_results | jq '.ok' || echo "❌ 不可用"

echo "MCP 服务器:"
curl -s http://localhost:19001/tools/health_check | jq '.healthy' || echo "❌ 不可用"

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "📡 服务地址："
echo "• Web 界面:           http://localhost:19000"
echo "• MCP 服务器:         http://localhost:19001"
echo "• MCP API 文档:       http://localhost:19001/docs"
echo "• SSE 测试页面:       http://localhost:19001/test"
echo "• 健康检查:           http://localhost:19001/tools/health_check"
echo ""
echo "🔧 管理命令："
echo "• 查看日志:           docker-compose logs -f mcp-server"
echo "• 停止服务:           docker-compose stop"
echo "• 重启服务:           docker-compose restart mcp-server"
echo "• 完全清理:           docker-compose down"
echo ""
echo "📚 使用指南:"
echo "• API 文档:           cat README.md"
echo "• 测试页面:           http://localhost:19001/test"
echo "• 健康检查:           curl http://localhost:19001/tools/health_check"
