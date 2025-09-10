# 🌊 Logstash MCP Server 使用指南

**Server-Sent Events 实时流式 Logstash 测试服务**

## 📋 概述

Logstash MCP Server 是基于 Server-Sent Events 的实时流式服务器，提供**实时进度反馈**和**流式测试结果**。同时支持标准 REST API 和 SSE 流式接口，特别适合 AI 实时监控长时间运行的测试流程。

## ✨ 核心特性

- 🌊 **Server-Sent Events (SSE) 支持**
- ⚡ **实时进度反馈**
- 📊 **流式测试结果**
- 🔄 **步骤级进度追踪**
- 🎯 **所有标准 MCP 工具**
- 🧪 **内置测试页面**

## 🚀 快速开始

### 启动服务

```bash
# 使用 Docker Compose（推荐）
cd /path/to/Logstash-lab
sudo docker compose up -d --build

# 或使用一键启动脚本
./start.sh

# 服务地址: http://localhost:19001
```

## 🔗 MCP 客户端配置

### 📄 JSON 配置方式（推荐）

#### ✅ 方法一：URL 直连（推荐）

在 AI 客户端的 MCP 配置文件中（如 `~/.cursor/mcp.json`）：

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

**其他网络环境示例**：
```json
# 局域网部署
{
  "mcpServers": {
    "logstash-test": {
      "url": "http://YOUR_SERVER_IP:19001/mcp",
      "description": "Logstash 规则测试和调试工具"
    }
  }
}
```


### 🔧 配置步骤

1. **找到配置文件位置**
   ```bash
   # Cursor 配置文件
   ~/.cursor/mcp.json
   
   # Claude Desktop 配置文件 (macOS)
   ~/Library/Application Support/Claude/claude_desktop_config.json
   
   # Claude Desktop 配置文件 (Windows)
   %APPDATA%/Claude/claude_desktop_config.json
   ```

2. **创建或编辑配置文件**
   ```bash
   # 创建目录（如果不存在）
   mkdir -p ~/.cursor
   
   # 编辑配置文件
   nano ~/.cursor/mcp.json
   ```

3. **应用配置**
   - 保存配置文件
   - 完全重启 AI 客户端应用
   - 检查工具标签页中是否显示 Logstash 工具

### 🧪 配置验证

配置成功后，在 AI 对话中应该可以看到以下 8 个工具：

1. **upload_pipeline** - 上传 Pipeline 配置文件
2. **send_test_log** - 发送测试日志
3. **get_parsed_results** - 获取解析结果
4. **clear_results** - 清空历史结果
5. **get_logstash_logs** - 获取 Logstash 日志
6. **test_pipeline_complete_stream** - 完整流式测试
7. **get_test_guidance** - 智能测试指导 ✨
8. **health_check** - 健康检查

### 🌐 HTTP API 配置

如果您的 AI 客户端不支持 MCP 协议，也可以直接使用 HTTP API：

#### 基础端点
```bash
# MCP JSON-RPC 2.0 协议端点
POST http://localhost:19001/mcp

# 工具列表
POST http://localhost:19001/mcp
Content-Type: application/json
{
  "jsonrpc": "2.0",
  "method": "list_tools",
  "id": 1
}

# 调用工具
POST http://localhost:19001/mcp
Content-Type: application/json
{
  "jsonrpc": "2.0",
  "method": "call_tool",
  "params": {
    "name": "health_check",
    "arguments": {}
  },
  "id": 2
}
```

#### REST API 端点（向后兼容）
```bash
# 健康检查
GET http://192.168.31.218:19001/tools/health_check

# 上传配置
POST http://192.168.31.218:19001/tools/upload_pipeline

# 发送测试日志
POST http://192.168.31.218:19001/tools/send_test_log

# 获取解析结果
GET http://192.168.31.218:19001/tools/get_parsed_results
```

### 验证服务状态

```bash
# 健康检查
curl http://localhost:19001/tools/health_check

# 查看可用工具
curl http://localhost:19001/ | jq '.available_tools'

# 访问测试页面
open http://localhost:19001/test
```

### Docker 部署

更新 `docker-compose.yml` 添加 SSE 服务：

```yaml
  sse-server:
    build: ./mcp_server
    command: python sse_mcp_server.py
    container_name: logstash-lab-sse
    ports:
      - "19002:19002"
    environment:
      - LOGSTASH_SERVICE_URL=http://web:19000
    depends_on:
      - web
```

## 🌊 SSE 流式接口

### 核心 SSE 接口

**GET** `/sse/test_pipeline_complete`

完整的 Pipeline 测试流程，提供实时进度反馈。

**查询参数**:
- `pipeline_content` (required): Pipeline 配置内容
- `test_logs` (required): 测试日志列表（JSON 编码字符串）
- `is_json` (optional): 是否为 JSON 格式，默认 false
- `wait_time` (optional): 等待热重载时间，默认 3 秒

**响应格式**: `text/event-stream`

### 事件类型

SSE 流会发送以下类型的事件：

- **`start`** - 流程开始
- **`progress`** - 进度更新
- **`success`** - 步骤成功
- **`error`** - 错误信息
- **`warning`** - 警告信息
- **`complete`** - 流程完成

### 事件数据格式

```json
{
  "type": "progress",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "data": {
    "step": "upload_pipeline",
    "message": "正在上传 Pipeline 配置...",
    "progress": 50
  }
}
```

## 💻 客户端使用示例

### JavaScript (EventSource)

```javascript
function startSSETest(pipelineContent, testLogs) {
    // 构建查询参数
    const params = new URLSearchParams({
        pipeline_content: pipelineContent,
        test_logs: JSON.stringify(testLogs),
        is_json: 'false',
        wait_time: '3'
    });
    
    const url = `http://localhost:19002/sse/test_pipeline_complete?${params.toString()}`;
    
    // 创建 SSE 连接
    const eventSource = new EventSource(url);
    
    eventSource.onopen = function(event) {
        console.log('✅ SSE 连接已建立');
    };
    
    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log(`[${data.type}] ${data.data.message}`);
            
            // 根据事件类型处理
            switch(data.type) {
                case 'start':
                    console.log('🚀 测试开始');
                    break;
                case 'progress':
                    console.log(`⏳ ${data.data.step}: ${data.data.message}`);
                    break;
                case 'success':
                    console.log(`✅ ${data.data.step}: ${data.data.message}`);
                    break;
                case 'error':
                    console.error(`❌ ${data.data.step}: ${data.data.message}`);
                    break;
                case 'complete':
                    console.log('🎉 测试完成');
                    eventSource.close();
                    break;
            }
        } catch (e) {
            console.error('解析事件失败:', event.data);
        }
    };
    
    eventSource.onerror = function(event) {
        console.error('❌ SSE 连接错误');
        eventSource.close();
    };
    
    return eventSource;
}

// 使用示例
const pipelineConfig = `
input { http { port => 15515 } }
filter {
  if "apache" == [@metadata][type] {
    grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  }
}
output { file { path => "/data/out/events.ndjson" } }
`;

const testLogs = [
    '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326'
];

const eventSource = startSSETest(pipelineConfig, testLogs);
```

### Python 客户端

```python
import requests
import json
import sseclient  # pip install sseclient-py

def sse_test_pipeline(pipeline_content, test_logs, base_url="http://localhost:19002"):
    """SSE 流式测试 Pipeline"""
    
    # 构建查询参数
    params = {
        'pipeline_content': pipeline_content,
        'test_logs': json.dumps(test_logs),
        'is_json': 'false',
        'wait_time': '3'
    }
    
    url = f"{base_url}/sse/test_pipeline_complete"
    
    # 创建 SSE 连接
    response = requests.get(url, params=params, stream=True, headers={
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
    })
    
    if response.status_code != 200:
        raise Exception(f"SSE 连接失败: {response.status_code}")
    
    print("✅ SSE 连接已建立")
    
    # 处理 SSE 事件
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        try:
            data = json.loads(event.data)
            event_type = data.get('type', 'unknown')
            message = data.get('data', {}).get('message', '')
            timestamp = data.get('timestamp', '')
            
            print(f"[{timestamp}] {event_type.upper()}: {message}")
            
            # 根据事件类型处理
            if event_type == 'start':
                print("🚀 测试开始")
            elif event_type == 'progress':
                step = data.get('data', {}).get('step', '')
                print(f"⏳ {step}: {message}")
            elif event_type == 'success':
                step = data.get('data', {}).get('step', '')
                print(f"✅ {step}: {message}")
            elif event_type == 'error':
                step = data.get('data', {}).get('step', '')
                print(f"❌ {step}: {message}")
                break
            elif event_type == 'complete':
                print("🎉 测试完成")
                break
                
        except json.JSONDecodeError as e:
            print(f"解析事件失败: {event.data}")
    
    print("🔌 SSE 连接关闭")

# 使用示例
pipeline_config = """
input { http { port => 15515 } }
filter {
  if "apache" == [@metadata][type] {
    grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  }
}
output { file { path => "/data/out/events.ndjson" } }
"""

test_logs = [
    '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326'
]

sse_test_pipeline(pipeline_config, test_logs)
```

### cURL 示例

```bash
# URL 编码参数
PIPELINE_CONTENT="input%20%7B%20http%20%7B%20port%20%3D%3E%2015515%20%7D%20%7D%0Afilter%20%7B%0A%20%20if%20%22apache%22%20%3D%3D%20%5B%40metadata%5D%5Btype%5D%20%7B%0A%20%20%20%20grok%20%7B%20match%20%3D%3E%20%7B%20%22message%22%20%3D%3E%20%22%25%7BCOMBINEDAPACHELOG%7D%22%20%7D%20%7D%0A%20%20%7D%0A%7D%0Aoutput%20%7B%20file%20%7B%20path%20%3D%3E%20%22%2Fdata%2Fout%2Fevents.ndjson%22%20%7D%20%7D"

TEST_LOGS='%5B%22127.0.0.1%20-%20-%20%5B25%2FDec%2F2023%3A10%3A00%3A00%20%2B0000%5D%20%5C%22GET%20%2Findex.html%20HTTP%2F1.1%5C%22%20200%202326%22%5D'

# SSE 流式请求
curl -N -H "Accept: text/event-stream" \
  "http://localhost:19002/sse/test_pipeline_complete?pipeline_content=${PIPELINE_CONTENT}&test_logs=${TEST_LOGS}&is_json=false&wait_time=3"
```

## 🛠️ 标准 REST API

SSE 服务器同时提供所有标准的 REST API 接口，与 `network_mcp_server.py` 完全兼容：

- `POST /tools/upload_pipeline`
- `POST /tools/send_test_log`
- `GET /tools/get_parsed_results`
- `POST /tools/clear_results`
- `GET /tools/get_logstash_logs`
- `GET /tools/health_check`

## 🧪 内置测试页面

访问 `http://localhost:19002/test` 查看内置的 SSE 测试页面，提供：

- 📝 Pipeline 配置编辑器
- 📋 测试日志编辑器
- 🌊 实时 SSE 流显示
- 🎨 事件类型高亮

## 📊 事件流示例

完整测试流程的事件序列：

```
1. start: 开始 Pipeline 测试流程
2. progress: 正在检查服务健康状态...
3. success: ✅ 服务可用
4. progress: 正在清空历史结果...
5. success: 清空完成
6. progress: 正在上传 Pipeline 配置...
7. success: Pipeline 已成功上传并应用到测试环境
8. progress: 等待 3 秒热重载...
9. progress: 热重载中... 1/3s
10. progress: 热重载中... 2/3s
11. progress: 热重载中... 3/3s
12. success: 热重载完成
13. progress: 正在发送第 1/1 条日志...
14. success: ✅ 日志发送成功
15. progress: 正在获取最终解析结果...
16. success: 获取到 1 条解析记录
17. progress: 正在检查 Logstash 错误日志...
18. success: 未发现错误
19. complete: Pipeline 测试流程完成
```

## 🎯 AI 集成优势

### 相比标准 REST API

**传统 REST API**:
- ❌ 长时间等待，无法知道进度
- ❌ 只能等待最终结果
- ❌ 网络超时问题

**SSE 流式 API**:
- ✅ **实时进度反馈**
- ✅ **步骤级状态监控**
- ✅ **即时错误反馈**
- ✅ **更好的用户体验**

### AI 使用场景

1. **长时间测试**: 复杂 Pipeline 配置测试
2. **多日志测试**: 批量日志解析验证
3. **调试模式**: 实时监控每个步骤
4. **进度展示**: 向用户展示测试进度

## 🔧 配置和部署

### 环境变量

- `LOGSTASH_SERVICE_URL`: Logstash 测试服务地址，默认 `http://logstash-web:19000`
- `PORT`: 服务端口，默认 19002

### Docker Compose 更新

```yaml
version: "3.9"
services:
  # ... 其他服务 ...
  
  sse-server:
    build: ./mcp_server
    command: python sse_mcp_server.py
    container_name: logstash-lab-sse
    ports:
      - "19002:19002"
    environment:
      - LOGSTASH_SERVICE_URL=http://web:19000
    depends_on:
      - web
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:19002/tools/health_check"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /sse/ {
        proxy_pass http://localhost:19002/sse/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 特殊配置
        proxy_set_header Cache-Control no-cache;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## 🚨 故障排除

### 🔧 常见配置错误

#### ❌ 错误的 SSE 配置
```bash
# 错误：缺少具体端点
@http://192.168.31.218:19001/sse
```

#### ✅ 正确的配置
```bash
# 正确：SSE 流式测试端点
http://192.168.31.218:19001/sse/test_pipeline_complete

# 或者使用测试页面（推荐）
http://192.168.31.218:19001/test
```

### 🛠️ Docker 构建问题

如果修改代码后容器没有更新，按以下步骤排查：

```bash
# 1. 清理 Docker 缓存
sudo docker system prune -f

# 2. 强制重新构建
sudo docker compose build --no-cache mcp-server

# 3. 重启服务
sudo docker compose restart mcp-server

# 4. 验证代码更新
sudo docker exec logstash-lab-mcp grep -n "检查是否是文件上传" /app/mcp_server.py
```

### 🔍 服务健康检查

```bash
# 检查 MCP 服务器状态
curl http://localhost:19001/tools/health_check

# 检查容器状态
sudo docker compose ps | grep mcp

# 查看详细日志
sudo docker compose logs -f mcp-server

# 检查端口监听
sudo netstat -tlnp | grep 19001
```

### 🌐 网络连接问题

```bash
# 检查容器网络
sudo docker network ls
sudo docker network inspect logstash-lab_default

# 测试容器间通信
sudo docker exec logstash-lab-mcp curl -s http://web:19000/get_parsed_results

# 检查环境变量
sudo docker exec logstash-lab-mcp env | grep LOGSTASH_SERVICE_URL
```

### 📋 常见问题

1. **SSE 连接中断**
   - 检查网络稳定性
   - 确认服务器未超时关闭连接
   - 客户端实现重连机制

2. **文件上传失败**
   - 确认文件格式正确
   - 检查文件大小限制
   - 验证文件编码（UTF-8）

3. **Pipeline 解析错误**
   - 验证 Logstash 配置语法
   - 检查特殊字符转义
   - 确认 filter 块格式正确

### 🧪 调试技巧

```bash
# 检查 SSE 连接
curl -N -H "Accept: text/event-stream" \
  "http://localhost:19001/sse/test_pipeline_complete?pipeline_content=filter{}&test_logs=[\"test\"]"

# 测试文件上传
curl -X POST http://localhost:19001/tools/upload_pipeline \
  -F 'file=@test.conf' | jq '.'

# 检健康状态
curl http://localhost:19001/tools/health_check | jq '.'

# 查看服务日志
docker logs logstash-lab-sse
```

## 📈 性能优化

- **连接管理**: 自动清理断开的连接
- **事件缓冲**: 避免事件丢失
- **错误恢复**: 优雅处理连接中断
- **资源清理**: 及时释放资源

---

**SSE MCP Server 让 AI 能够实时监控 Logstash 测试流程！** 🌊
