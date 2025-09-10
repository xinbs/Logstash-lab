#!/bin/bash

echo "🌊 **Logstash MCP 服务器配置指南**"
echo ""
echo "🎯 **MCP 服务器地址**："
echo "   HTTP 端点: http://localhost:19001/mcp"
echo "   SSE 端点: http://localhost:19001/sse/test_pipeline_complete"
echo "   测试页面: http://localhost:19001/test"
echo ""

echo "📋 **AI 客户端配置方法**："
echo ""

echo "1️⃣ **Claude Desktop 配置**："
echo "   编辑配置文件："
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "   Linux: ~/.config/claude-desktop/claude_desktop_config.json"
else
    echo "   Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
fi

echo ""
echo "   配置内容："
cat << 'EOF'
{
  "mcpServers": {
    "logstash-test": {
      "command": "node",
      "args": ["-e", "
        const http = require('http');
        const data = JSON.stringify(JSON.parse(process.argv[2]));
        const options = {
          hostname: 'localhost',
          port: 19001,
          path: '/mcp',
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(data)
          }
        };
        const req = http.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => body += chunk);
          res.on('end', () => console.log(body));
        });
        req.on('error', (e) => console.error(JSON.stringify({jsonrpc:'2.0',error:{code:-32603,message:e.message}})));
        req.write(data);
        req.end();
      "]
    }
  }
}
EOF

echo ""
echo "2️⃣ **直接测试 MCP 协议**："
echo "   # 获取工具列表"
echo "   curl -X POST http://localhost:19001/mcp \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jsonrpc\": \"2.0\", \"method\": \"list_tools\", \"id\": 1}'"
echo ""
echo "   # 调用健康检查工具"
echo "   curl -X POST http://localhost:19001/mcp \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jsonrpc\": \"2.0\", \"method\": \"call_tool\", \"params\": {\"name\": \"health_check\", \"arguments\": {}}, \"id\": 2}'"

echo ""
echo "3️⃣ **使用 SSE 流式测试**："
echo "   在浏览器中打开: http://localhost:19001/test"

echo ""
echo "🔧 **开发模式优势**："
echo "   ✅ 修改代码自动重载，无需重建镜像"
echo "   ✅ 支持实时调试"
echo "   ✅ 卷挂载保证代码同步"

echo ""
echo "📊 **服务状态检查**："
curl -s http://localhost:19001/tools/health_check | jq '.healthy, .logstash_service_url' 2>/dev/null || echo "请先启动服务"

echo ""
echo "🎉 **配置完成！现在您可以在 AI 客户端中使用 Logstash 测试工具了**"
