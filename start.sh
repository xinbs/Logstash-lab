#!/bin/bash

echo "🚀 启动 Logstash 规则测试工具..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查端口是否被占用
if lsof -i :19000 > /dev/null 2>&1; then
    echo "⚠️  警告: 端口 19000 已被占用"
    echo "请确保没有其他应用使用此端口"
fi

if lsof -i :15515 > /dev/null 2>&1; then
    echo "⚠️  警告: 端口 15515 已被占用"
    echo "请确保没有其他应用使用此端口"
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/out

# 构建并启动容器
echo "🔨 构建并启动容器..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

echo ""
echo "✅ 启动完成！"
echo ""
echo "📋 访问地址:"
echo "   🌐 Web 界面: http://localhost:19000"
echo "   🔗 Logstash HTTP 输入: http://localhost:15515"
echo ""
echo "📚 使用说明:"
echo "   1. 打开 http://localhost:19000"
echo "   2. 在左侧编辑 Logstash filter 规则"
echo "   3. 在右侧输入测试日志"
echo "   4. 点击发送查看解析结果"
echo "   5. 点击 '📋 查看 Logstash 日志' 获取日志指导"
echo ""
echo "🎯 快速开始:"
echo "   • 点击示例按钮（Apache/JSON/Syslog）快速测试"
echo "   • 页面支持全屏宽度显示和自适应高度"
echo "   • 开发模式已启用，代码修改自动生效"
echo ""
echo "🛠️  常用命令:"
echo "   查看日志: sudo docker compose logs -f"
echo "   查看 Web 日志: sudo docker compose logs -f web"
echo "   查看 Logstash 日志: sudo docker compose logs -f logstash"
echo "   停止服务: sudo docker compose down"
echo "   重启服务: sudo docker compose restart"
echo ""
echo "📖 详细文档:"
echo "   README.md - 完整使用指南"
echo "   快速开始.md - 5分钟快速上手"
echo "   使用指南.md - 详细配置说明"
echo ""
