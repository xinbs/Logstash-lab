#!/bin/bash

echo "🔍 **MCP 连接调试脚本**"
echo ""

echo "1️⃣ **网络连通性检查**"
echo -n "ping 测试: "
if ping -c 1 192.168.31.218 >/dev/null 2>&1; then
    echo "✅ 网络可达"
else
    echo "❌ 网络不通"
fi

echo -n "端口测试: "
if nc -z 192.168.31.218 19001; then
    echo "✅ 端口 19001 可访问"
else
    echo "❌ 端口 19001 不可访问"
fi

echo ""
echo "2️⃣ **MCP 协议测试**"

echo -n "初始化测试: "
init_response=$(curl -s -X POST http://192.168.31.218:19001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "debug", "version": "1.0.0"}}, "id": 0}')

if echo "$init_response" | jq -e '.result.serverInfo.name' >/dev/null 2>&1; then
    echo "✅ 初始化成功"
else
    echo "❌ 初始化失败"
    echo "响应: $init_response"
fi

echo -n "工具列表测试: "
tools_response=$(curl -s -X POST http://192.168.31.218:19001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "list_tools", "id": 1}')

tool_count=$(echo "$tools_response" | jq -r '.result.tools | length')
if [ "$tool_count" = "7" ]; then
    echo "✅ 获取到 $tool_count 个工具"
else
    echo "❌ 工具列表异常 (期待 7 个，实际 $tool_count 个)"
    echo "响应: $tools_response"
fi

echo ""
echo "3️⃣ **工具详情**"
echo "$tools_response" | jq -r '.result.tools[] | "• \(.name): \(.description)"'

echo ""
echo "4️⃣ **服务器信息**"
echo "服务器名称: $(echo "$init_response" | jq -r '.result.serverInfo.name')"
echo "协议版本: $(echo "$init_response" | jq -r '.result.protocolVersion')"
echo "工具能力: $(echo "$init_response" | jq -r '.result.capabilities.tools')"

echo ""
echo "5️⃣ **建议操作**"
if [ "$tool_count" = "7" ]; then
    echo "✅ MCP 服务器工作正常"
    echo ""
    echo "如果 AI 客户端仍然看不到工具，请尝试："
    echo "• 完全重启 AI 应用"
    echo "• 删除并重新添加 MCP 配置"
    echo "• 检查 AI 应用的 MCP 日志"
    echo "• 确保配置中的 URL 完全正确"
else
    echo "❌ MCP 服务器有问题，需要进一步排查"
fi

echo ""
echo "📋 **当前配置应该是**："
echo "类型: 可流式传输的 HTTP (streamableHttp)"
echo "URL: http://192.168.31.218:19001/mcp"
echo "请求头: Content-Type=application/json"
echo "超时: 60秒"
echo "长时间运行: 开启"
