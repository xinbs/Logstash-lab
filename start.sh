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
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 启动完成！"
echo ""
echo "📋 访问地址:"
echo "   Web 界面: http://localhost:19000"
echo "   Logstash HTTP 输入: http://localhost:15515"
echo ""
echo "📚 使用说明:"
echo "   1. 打开 http://localhost:19000"
echo "   2. 在左侧编辑 Logstash filter 规则"
echo "   3. 在右侧输入测试日志"
echo "   4. 点击发送查看解析结果"
echo ""
echo "🛠️  其他命令:"
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
