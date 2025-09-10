# 🔗 MCP 配置参考指南

**完整的 Model Context Protocol 配置说明**

---

## 📋 支持的 AI 客户端

- ✅ **Cursor** - 全功能支持
- ✅ **Claude Desktop** - 全功能支持  
- ✅ **其他 MCP 兼容客户端** - 标准协议支持

---

## 🎯 配置方法对比

| 方法 | 兼容性 | 配置复杂度 | 推荐度 | 说明 |
|------|--------|------------|--------|------|
| URL 直连 | 高 | ⭐ | 🌟🌟🌟 | 最简单，大多数客户端支持 |
| curl 命令 | 最高 | ⭐⭐ | 🌟🌟 | 兼容性最好，适合故障排除 |
| Node.js 代理 | 中 | ⭐⭐⭐ | 🌟 | 高级用法，需要 Node.js |

---

## 🔧 配置文件位置

### Cursor
```bash
~/.cursor/mcp.json
```

### Claude Desktop

**macOS**:
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:
```cmd
%APPDATA%/Claude/claude_desktop_config.json
```

**Linux**:
```bash
~/.config/Claude/claude_desktop_config.json
```

---

## 📝 配置模板

### 方法一：URL 直连（推荐）

**最简单的配置，适合大多数情况**

```json
{
  "mcpServers": {
    "logstash-test": {
      "url": "http://localhost:19001/mcp",
      "description": "Logstash 规则测试和调试工具"
    }
  }
}
```

**优点**:
- ✅ 配置最简单
- ✅ 大多数客户端支持
- ✅ 无需外部依赖

**缺点**:
- ❌ 部分客户端可能不支持

### 方法二：curl 命令（兼容性最好）

**通过 curl 命令调用，兼容性最好**

```json
{
  "mcpServers": {
    "logstash-test": {
      "command": "curl",
      "args": [
        "-s",
        "-X", "POST", 
        "http://localhost:19001/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ],
      "description": "Logstash 规则测试和调试工具"
    }
  }
}
```

**优点**:
- ✅ 兼容性最好
- ✅ 适合故障排除
- ✅ 标准 HTTP 调用

**缺点**:
- ❌ 需要系统安装 curl
- ❌ 配置稍微复杂

### 方法三：Node.js 代理（高级用法）

**通过 Node.js 脚本代理请求**

```json
{
  "mcpServers": {
    "logstash-test": {
      "command": "node",
      "args": [
        "-e",
        "const http = require('http'); const data = JSON.stringify(JSON.parse(process.argv[2])); const options = { hostname: 'localhost', port: 19001, path: '/mcp', method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }; const req = http.request(options, (res) => { let body = ''; res.on('data', (chunk) => body += chunk); res.on('end', () => console.log(body)); }); req.on('error', (e) => console.error(JSON.stringify({jsonrpc:'2.0',error:{code:-32603,message:e.message}}))); req.write(data); req.end();"
      ],
      "description": "Logstash 规则测试和调试工具"
    }
  }
}
```

**优点**:
- ✅ 高度可定制
- ✅ 可添加认证等高级功能
- ✅ 完全控制请求过程

**缺点**:
- ❌ 需要系统安装 Node.js
- ❌ 配置最复杂
- ❌ 调试困难

---

## 🌐 网络配置

### IP 地址配置

根据您的部署环境，替换配置中的 IP 地址：

```json
{
  "url": "http://YOUR_SERVER_IP:19001/mcp"
}
```

**常见场景**:
- **本地开发**: `http://localhost:19001/mcp` 或 `http://127.0.0.1:19001/mcp`
- **局域网**: `http://192.168.x.x:19001/mcp`
- **公网**: `http://your-domain.com:19001/mcp`

### 端口说明

- **19001**: MCP 服务器端口
- **19000**: Web 界面端口

---

## 🛠️ 配置步骤

### 1. 创建配置文件

```bash
# Cursor 示例
mkdir -p ~/.cursor
nano ~/.cursor/mcp.json
```

### 2. 添加配置内容

选择上述任一配置模板，复制粘贴到配置文件中。

### 3. 修改 IP 地址

将 `192.168.31.218` 替换为您的实际服务器 IP。

### 4. 保存并重启

保存配置文件，完全重启 AI 客户端应用。

---

## ✅ 配置验证

### 检查工具是否加载

配置成功后，在 AI 对话中应该可以看到以下 8 个工具：

1. **upload_pipeline** - 上传 Pipeline 配置文件
2. **send_test_log** - 发送测试日志  
3. **get_parsed_results** - 获取解析结果
4. **clear_results** - 清空历史结果
5. **get_logstash_logs** - 获取 Logstash 日志
6. **test_pipeline_complete_stream** - 完整流式测试
7. **get_test_guidance** - 智能测试指导 ✨
8. **health_check** - 健康检查

### 测试连接

要求 AI 执行：
```
请调用 health_check 工具检查服务状态
```

如果返回服务健康信息，说明配置成功。

---

## 🚨 故障排除

### 常见问题

#### ❌ 工具不显示
**原因**: 配置文件格式错误或路径错误
**解决**: 
1. 检查 JSON 格式是否正确
2. 确认配置文件路径
3. 完全重启 AI 客户端

#### ❌ 连接超时  
**原因**: 网络问题或服务未启动
**解决**:
1. 检查服务器 IP 和端口
2. 确认防火墙设置
3. 验证服务是否运行

#### ❌ 权限错误
**原因**: curl 或 node 命令不可用
**解决**:
1. 安装对应命令行工具
2. 检查 PATH 环境变量
3. 使用 URL 直连方式

### 调试方法

#### 1. 直接测试端点
```bash
curl -X POST http://YOUR_IP:19001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "list_tools", "id": 1}'
```

#### 2. 检查服务状态
```bash
curl http://YOUR_IP:19001/tools/health_check
```

#### 3. 查看服务日志
```bash
sudo docker logs logstash-lab-mcp
```

---

## 📚 相关文档

- [MCP 服务器详细文档](mcp_server/README.md)
- [AI 集成调用指南](AI_INTEGRATION_GUIDE.md)
- [主项目文档](README.md)

---

## 💡 最佳实践

1. **优先使用 URL 直连方式**，配置最简单
2. **如遇问题切换到 curl 方式**，兼容性最好
3. **记得修改 IP 地址**为您的实际服务器地址
4. **完全重启客户端**后配置才能生效
5. **使用健康检查**验证配置是否成功

---

📞 **需要帮助?** 

如果配置过程中遇到问题，可以：
1. 查看 [故障排除文档](mcp_server/README.md#故障排除)
2. 检查服务器日志获取详细错误信息
3. 使用测试页面 `http://YOUR_IP:19001/test` 验证服务状态
