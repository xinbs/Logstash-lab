#!/bin/bash

echo "🚀 启动 Logstash 规则测试工具..."

# 检查 Docker 是否运行
if ! sudo docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查端口是否被占用
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        echo "⚠️  警告: 端口 $1 已被占用"
        echo "请确保没有其他应用使用此端口"
    fi
}

check_port 19000
check_port 19001
check_port 15515

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/out

# 构建并启动容器
echo "🔨 构建并启动容器..."
if command -v docker-compose &> /dev/null; then
    sudo docker-compose up -d --build
else
    sudo docker compose up -d --build
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
if command -v docker-compose &> /dev/null; then
    sudo docker-compose ps
else
    sudo docker compose ps
fi

echo ""
echo "💚 健康检查..."

# 检查 Logstash 测试服务
echo -n "• Logstash 测试服务: "
if curl -s http://localhost:19000/get_parsed_results > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 不可用"
fi

# 检查 MCP 服务器
echo -n "• MCP 服务器: "
if curl -s http://localhost:19001/tools/health_check > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 不可用"
fi

echo ""
echo "✅ 启动完成！"
echo ""
echo "📋 访问地址:"
echo "   🌐 Web 界面: http://localhost:19000"
echo "   🌊 MCP 服务器: http://localhost:19001"
echo "   🧪 SSE 测试页面: http://localhost:19001/test"
echo "   📚 MCP API 文档: http://localhost:19001/docs"
echo "   🔗 Logstash HTTP 输入: http://localhost:15515"
echo ""
echo "📚 使用说明:"
echo "   🌐 Web 界面使用："
echo "     1. 打开 http://localhost:19000"
echo "     2. 在左侧编辑 Logstash filter 规则"
echo "     3. 在右侧输入测试日志"
echo "     4. 点击发送查看解析结果"
echo ""
echo "   🌊 MCP/AI 调用："
echo "     1. REST API: http://localhost:19001/tools/*"
echo "     2. SSE 流式: http://localhost:19001/sse/*"
echo "     3. 测试页面: http://localhost:19001/test"
echo ""
echo "🎯 快速开始:"
echo "   • 点击示例按钮（Apache/JSON/Syslog）快速测试"
echo "   • 页面支持全屏宽度显示和自适应高度"
echo "   • 开发模式已启用，代码修改自动生效"
echo ""
echo "🛠️  常用命令:"
echo "   查看所有日志: sudo docker compose logs -f"
echo "   查看 Web 日志: sudo docker compose logs -f web"
echo "   查看 MCP 日志: sudo docker compose logs -f mcp-server"
echo "   查看 Logstash 日志: sudo docker compose logs -f logstash"
echo "   停止服务: sudo docker compose down"
echo "   重启服务: sudo docker compose restart"
echo "   重启 MCP: sudo docker compose restart mcp-server"
echo ""
echo "📖 详细文档:"
echo "   README.md - 完整使用指南"
echo "   mcp_server/README.md - MCP 服务器文档"
echo "   AI_INTEGRATION_GUIDE.md - AI 集成指南"
echo ""
