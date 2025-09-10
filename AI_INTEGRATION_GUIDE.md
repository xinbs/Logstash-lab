# 🤖 AI 集成调用指南

**面向第三方 AI 的 Logstash 规则测试服务调用文档**

本文档专门为第三方 AI 系统提供完整的调用指南，实现自动化的 Logstash 规则测试和验证。

---

## 🚀 快速开始 - MCP 集成 (推荐)

### 🔗 **MCP (Model Context Protocol) 配置**

**最佳实践**: 使用 MCP 协议可以让 AI 直接调用 Logstash 测试工具，无需编写复杂的 HTTP 请求代码。

#### ✅ **支持的 AI 客户端**
- Cursor
- Claude Desktop  
- 支持 MCP 协议的其他 AI 工具

#### 🔧 **快速配置**

**步骤 1**: 找到配置文件
```bash
# Cursor
~/.cursor/mcp.json

# Claude Desktop (macOS)  
~/Library/Application Support/Claude/claude_desktop_config.json

# Claude Desktop (Windows)
%APPDATA%/Claude/claude_desktop_config.json
```

**步骤 2**: 添加配置（推荐 URL 方式）
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

**步骤 3**: 重启 AI 客户端

#### 🎯 **可用工具 (8个)**
1. **upload_pipeline** - 上传完整 Pipeline 配置文件
2. **send_test_log** - 发送测试日志进行解析  
3. **get_parsed_results** - 获取最新解析结果
4. **clear_results** - 清空历史解析结果
5. **get_logstash_logs** - 获取 Logstash 运行日志
6. **test_pipeline_complete_stream** - 执行完整流式测试流程
7. **get_test_guidance** - 获取智能测试指导 ✨
8. **health_check** - 服务健康检查

#### 💡 **智能测试指导**

新增的 `get_test_guidance` 工具可以：
- 🎯 **自动分析场景**：新建配置、调试修复、测试验证、性能优化
- 📋 **提供步骤指导**：根据不同场景推荐最佳测试流程
- 🔍 **配置智能分析**：检测 Grok、Ruby、Mutate、Date 插件并提供建议
- 📊 **日志格式识别**：自动识别 Syslog、JSON 等格式
- ⚠️ **常见问题预警**：提前提醒可能的问题和解决方案

#### 🛠️ **兼容性配置**

如果 URL 方式不工作，可以使用 curl 命令方式：
```json
{
  "mcpServers": {
    "logstash-test": {
      "command": "curl",
      "args": [
        "-s", "-X", "POST",
        "http://localhost:19001/mcp", 
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ],
      "description": "Logstash 规则测试和调试工具"
    }
  }
}
```

---

## 📋 服务概述

### 🎯 **服务功能**
- **🌟 Pipeline 文件上传和解析**（推荐）
- **Logstash Filter 规则编辑和验证**
- **实时日志解析测试**
- **解析结果获取和分析**
- **调试日志查看**
- **自动化测试工作流**

### 🌐 **服务地址**
```
Web 服务: http://localhost:19000
MCP 服务器: http://localhost:19001
MCP JSON-RPC: POST http://localhost:19001/mcp
SSE 测试页面: http://localhost:19001/test
Health Check: GET http://localhost:19001/tools/health_check
```

### 🔑 **核心特性**
- ✅ **无需认证**：直接调用 API
- ✅ **热重载**：配置修改 3 秒内生效
- ✅ **智能处理**：自动条件判断替换
- ✅ **实时反馈**：即时获取解析结果
- ✅ **错误处理**：详细的错误信息

---

## 🚀 AI 调用快速开始

### 1️⃣ **服务健康检查**

在开始调用前，先检查服务状态：

```bash
# 检查服务是否可用
curl -s http://localhost:19000/get_parsed_results > /dev/null
echo "Service status: $?"  # 0=可用, 非0=不可用
```

**AI 实现建议**：
```python
import requests

def check_service_health():
    try:
        response = requests.get("http://localhost:19000/get_parsed_results", timeout=5)
        return response.status_code == 200
    except:
        return False
```

### 2️⃣ **基本调用工作流**

#### 🌟 **推荐方式：MCP 服务器 Pipeline 文件上传工作流**

```bash
#!/bin/bash
# AI 自动化测试工作流 - MCP 服务器方式（推荐）

MCP_URL="http://localhost:19001"
WEB_URL="http://localhost:19000"

# 1. 创建完整的 pipeline 配置文件
cat > /tmp/test_pipeline.conf << 'EOF'
input {
  http {
    port => 15515
    additional_codecs => { "application/json" => "json" }
  }
}

filter {
  if "apache" == [@metadata][type] {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
    mutate {
      rename => { "clientip" => "src_ip" }
      add_field => { "log_type" => "apache_access" }
    }
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
      target => "@timestamp"
    }
  }
}

output {
  file {
    path => "/data/out/events.ndjson"
    codec => json_lines
  }
}
EOF

# 2. 清空历史数据
curl -s -X POST "$BASE_URL/clear_results"

# 3. 上传 pipeline 文件（使用 MCP 服务器，自动提取 filter 并应用）
echo "📤 上传 Pipeline 配置..."
response=$(curl -s -X POST "$MCP_URL/tools/upload_pipeline" -F 'file=@/tmp/test_pipeline.conf')
echo "$response" | jq '.'

if [ "$(echo "$response" | jq -r .success)" = "true" ]; then
  echo "✅ Pipeline 上传成功"
  echo "📋 提取的 filter 数量: $(echo "$response" | jq -r .extracted_filters)"
else
  echo "❌ Pipeline 上传失败: $(echo "$response" | jq -r .error)"
  exit 1
fi

# 4. 等待热重载
sleep 3

# 5. 发送测试日志（使用 MCP 服务器）
echo "🧪 发送测试日志..."
test_response=$(curl -s -X POST "$MCP_URL/tools/send_test_log" \
  -H "Content-Type: application/json" \
  -d '{"log_content": "127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326"}')

# 6. 获取解析结果
curl -s "$BASE_URL/get_parsed_results" | jq '.'

# 7. 清理临时文件
rm -f /tmp/test_pipeline.conf
```

#### 🔧 **传统方式：直接 Filter 编辑工作流**

```bash
#!/bin/bash
# AI 自动化测试工作流 - 传统方式

BASE_URL="http://localhost:19000"

# 1. 清空历史数据
curl -s -X POST "$BASE_URL/clear_results"

# 2. 保存 Filter 规则（使用 --data-urlencode 避免编码问题）
curl -s -X POST "$BASE_URL/save_filter" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "filter=grok { match => { \"message\" => \"%{COMBINEDAPACHELOG}\" } }"

# 3. 等待热重载
sleep 3

# 4. 发送测试日志
curl -s -X POST "$BASE_URL/test" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "logs=127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326"

# 5. 获取解析结果
curl -s "$BASE_URL/get_parsed_results" | jq '.'
```

---

## 🌊 MCP 服务器 API（推荐）

### 🎯 **MCP 服务器优势**

MCP (Model Context Protocol) 服务器专为 AI 调用设计，提供更强大和便捷的接口：

- 🚀 **文件上传支持**: 直接上传 Pipeline 配置文件，避免编码问题
- 🌊 **SSE 流式反馈**: 实时监控测试进度，适合长时间运行的任务
- 🛡️ **多格式支持**: 支持文件上传、表单和 JSON 三种输入方式
- ⚡ **标准化错误处理**: 统一的错误响应格式
- 🔄 **智能解析**: 自动提取 filter 块并替换条件判断

### 🌟 **1. MCP Pipeline 上传接口**

**端点**: `POST http://localhost:19001/tools/upload_pipeline`

**支持的输入格式**:
1. **文件上传** (推荐): `-F 'file=@config.conf'`
2. **表单数据**: `-d 'pipeline=...'`  
3. **JSON 格式**: `-d '{"pipeline_content": "..."}'`

**AI 调用示例**:

```python
import requests

# 方式1：文件上传（最推荐）
def upload_pipeline_file(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:19001/tools/upload_pipeline',
            files={'file': f}
        )
    return response.json()

# 方式2：JSON 格式
def upload_pipeline_json(pipeline_content):
    response = requests.post(
        'http://localhost:19001/tools/upload_pipeline',
        json={'pipeline_content': pipeline_content}
    )
    return response.json()

# 使用示例
result = upload_pipeline_file('bomgar.conf')
if result['success']:
    print(f"✅ 上传成功: {result['message']}")
    print(f"📋 提取的 filter 数量: {result['extracted_filters']}")
    print(f"🔍 配置预览: {result['preview'][:100]}...")
else:
    print(f"❌ 上传失败: {result['error']}")
```

**响应格式**:
```json
{
  "success": true,
  "message": "Pipeline 已成功上传并应用到测试环境",
  "extracted_filters": 1,
  "preview": "if \"test\" == [@metadata][type] { ... }",
  "raw_response": {
    "ok": true,
    "message": "Pipeline 已成功上传并应用到测试环境",
    "extracted_filters": 1,
    "applied_filter_preview": "详细的配置预览"
  }
}
```

### 🧪 **2. MCP 发送测试日志接口**

**端点**: `POST http://localhost:19001/tools/send_test_log`

**AI 调用示例**:

```python
def send_test_log(log_content, is_json=False):
    response = requests.post(
        'http://localhost:19001/tools/send_test_log',
        json={
            'log_content': log_content,
            'is_json': is_json
        }
    )
    return response.json()

# 使用示例
result = send_test_log('127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326')
if result['success']:
    print(f"✅ 日志发送成功")
    print(f"📊 最新解析结果: {result['latest_event']}")
else:
    print(f"❌ 发送失败: {result['error']}")
```

### 📊 **3. MCP 获取解析结果接口**

**端点**: `GET http://localhost:19001/tools/get_parsed_results`

```python
def get_parsed_results():
    response = requests.get('http://localhost:19001/tools/get_parsed_results')
    return response.json()

# 使用示例
results = get_parsed_results()
print(f"📈 总记录数: {results['events_count']}")
for event in results['events']:
    print(f"🕒 {event['@timestamp']}: {event.get('message', '')[:50]}...")
```

### 🔍 **4. MCP 健康检查接口**

**端点**: `GET http://localhost:19001/tools/health_check`

```python
def health_check():
    response = requests.get('http://localhost:19001/tools/health_check')
    return response.json()

# 使用示例
health = health_check()
if health['healthy']:
    print(f"✅ 服务健康: {health['details']}")
else:
    print(f"❌ 服务异常: {health['details']}")
```

### 🌊 **5. SSE 流式测试接口**

**端点**: `GET http://localhost:19001/sse/test_pipeline_complete`

**适用场景**: 需要实时监控长时间运行测试流程的 AI 系统

```python
import requests
import json

def sse_test_pipeline(pipeline_content, test_logs):
    params = {
        'pipeline_content': pipeline_content,
        'test_logs': json.dumps(test_logs),
        'is_json': 'false',
        'wait_time': '3'
    }
    
    response = requests.get(
        'http://localhost:19001/sse/test_pipeline_complete',
        params=params,
        stream=True,
        headers={'Accept': 'text/event-stream'}
    )
    
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                print(f"[{event_data['timestamp']}] {event_data['type']}: {event_data['data']['message']}")
                
                if event_data['type'] in ['complete', 'error']:
                    break
            except json.JSONDecodeError:
                continue

# 使用示例
sse_test_pipeline(
    pipeline_content="filter { grok { match => { \"message\" => \"%{GREEDYDATA:content}\" } } }",
    test_logs=["test log message"]
)
```

## 🔧 传统 Web API 接口

以下是传统 Web 服务的 API 接口，仍然可用但建议优先使用 MCP 服务器：

### 🌟 **1. Pipeline 文件上传接口（Web 版本）**

**端点**: `POST /upload_pipeline`

**功能**: 上传完整的 Logstash pipeline 配置文件，系统自动提取 filter 块并应用到测试环境

**优势**:
- ✅ **完全避免 URL 编码问题**: 不会出现 `+` 号变空格等编码问题
- ✅ **保持原始格式**: 自动保留换行符、缩进和注释
- ✅ **智能解析**: 自动识别和提取 filter 块，支持复杂嵌套结构
- ✅ **双重支持**: 同时支持文件上传和文本内容粘贴

**AI 调用示例**:
```python
import requests
import tempfile
import os

def upload_pipeline_file(pipeline_content):
    """方式一：文件上传"""
    url = "http://localhost:19000/upload_pipeline"
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(pipeline_content)
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('pipeline.conf', f, 'text/plain')}
            response = requests.post(url, files=files)
        return response.json()
    finally:
        os.unlink(temp_file)

def upload_pipeline_text(pipeline_content):
    """方式二：文本内容上传"""
    url = "http://localhost:19000/upload_pipeline"
    data = {"pipeline": pipeline_content}
    
    response = requests.post(
        url, 
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()

# 使用示例
pipeline_config = """
input {
  udp {
    port => 18136
    codec => line {}
    add_field => { "[@metadata][type]" => "bomgar" }
  }
}

filter {
  if "bomgar" == [@metadata][type] {
    grok {
      match => { "message" => "<%{POSINT:syslog_pri}>%{POSINT:syslog_ver} %{DATA:syslog_timestamp} %{GREEDYDATA:content}" }
    }
    mutate {
      add_field => { "__source" => "bomgar", "log_type" => "bomgar_session" }
      convert => { "syslog_pri" => "integer", "syslog_ver" => "integer" }
    }
  }
}

output {
  kafka {
    bootstrap_servers => "localhost:9092"
    topic_id => "logs"
  }
}
"""

# 推荐使用文件上传方式
result = upload_pipeline_file(pipeline_config)
print(f"上传结果: {result['message']}")
print(f"提取的 filter 预览: {result.get('applied_filter_preview', '')[:100]}...")
```

**响应格式**:
```json
{
  "ok": true,
  "message": "Pipeline 已成功上传并应用到测试环境",
  "extracted_filters": 1,
  "applied_filter_preview": "    if \"bomgar\" == [@metadata][type] {\n        grok {\n            match => { \"message\" => \"<%{POSINT:syslog_pri}>%{POSINT:syslog_ver}...\" }\n        }\n        # More filter rules...\n    }"
}
```

### 🛠️ **2. 保存 Filter 规则（传统方式）**

**端点**: `POST /save_filter`

**功能**: 保存 Logstash filter 配置并自动重载

**请求格式**:
```http
POST /save_filter HTTP/1.1
Host: localhost:19000
Content-Type: application/x-www-form-urlencoded

filter=<FILTER_CONTENT>
```

**AI 调用示例**:
```python
import requests
import urllib.parse

def save_filter(filter_content):
    url = "http://localhost:19000/save_filter"
    data = {"filter": filter_content}
    
    response = requests.post(
        url, 
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()

# 使用示例
filter_rule = """
grok {
  match => { "message" => "%{COMBINEDAPACHELOG}" }
}
mutate {
  rename => { "clientip" => "src_ip" }
}
"""

result = save_filter(filter_rule)
print(f"保存结果: {result['message']}")
```

**智能功能**:
- 自动将任何 `if "xxx" == [@metadata][type]` 替换为 `if "test" == [@metadata][type]`
- 自动设置元数据类型为 "test"
- 3 秒内自动热重载

**响应格式**:
```json
{
  "ok": true,
  "message": "Filter 已保存并自动重载 (已自动添加条件判断: if \"test\" == [@metadata][type])"
}
```

### 📊 **3. 发送测试日志**

**端点**: `POST /test`

**功能**: 发送测试日志到 Logstash 并获取解析结果

**请求参数**:
- `logs`: 要测试的日志内容（必需）
- `is_json`: 是否为 JSON 格式，值为 "1" 表示是（可选）

**AI 调用示例**:
```python
def send_test_log(log_content, is_json=False):
    url = "http://localhost:19000/test"
    data = {
        "logs": log_content
    }
    if is_json:
        data["is_json"] = "1"
    
    response = requests.post(url, data=data)
    return response.json()

# 测试纯文本日志
apache_log = '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326'
result = send_test_log(apache_log)
print(f"解析结果: {result['events']}")

# 测试 JSON 日志
json_log = '{"timestamp": "2023-12-25T10:00:00Z", "level": "info", "message": "用户登录成功"}'
result = send_test_log(json_log, is_json=True)
```

**响应格式**:
```json
{
  "ok": true,
  "message": "✅ 日志发送成功",
  "events": [
    {
      "@timestamp": "2024-12-25T10:00:00.000Z",
      "message": "原始日志内容",
      "clientip": "127.0.0.1",
      "verb": "GET",
      "request": "/index.html",
      "src_ip": "127.0.0.1"
    }
  ]
}
```

### 📈 **4. 获取解析结果**

**端点**: `GET /get_parsed_results`

**功能**: 获取最新的解析记录（最多 50 条）

**AI 调用示例**:
```python
def get_parsed_results():
    url = "http://localhost:19000/get_parsed_results"
    response = requests.get(url)
    return response.json()

def analyze_results():
    results = get_parsed_results()
    
    if results["ok"]:
        events = results["events"]
        count = results["count"]
        
        print(f"获取到 {count} 条解析记录")
        
        # 分析解析结果
        for i, event in enumerate(events):
            print(f"记录 {i+1}:")
            print(f"  时间: {event.get('@timestamp')}")
            print(f"  原始消息: {event.get('message', '')[:100]}...")
            
            # 检查解析出的字段
            parsed_fields = [k for k in event.keys() if not k.startswith('@') and k != 'message']
            print(f"  解析字段: {', '.join(parsed_fields)}")
            
        return events
    else:
        print(f"获取失败: {results.get('message')}")
        return []
```

**响应格式**:
```json
{
  "ok": true,
  "events": [
    {
      "@timestamp": "2024-12-25T10:00:00.000Z",
      "message": "原始日志",
      "parsed_field1": "value1",
      "parsed_field2": "value2",
      "_parsed_time": "2024-12-25 10:00:15"
    }
  ],
  "count": 1,
  "message": "成功获取 1 条解析记录"
}
```

### 📋 **5. 获取 Logstash 日志**

**端点**: `GET /logstash_logs`

**功能**: 获取 Logstash 运行日志，用于调试

**AI 调用示例**:
```python
def get_logstash_logs():
    url = "http://localhost:19000/logstash_logs"
    response = requests.get(url)
    return response.json()

def check_for_errors():
    logs_result = get_logstash_logs()
    
    if logs_result["ok"]:
        logs = logs_result["logs"]
        
        # 检查错误信息
        error_lines = [line for line in logs.split('\n') if 'ERROR' in line.upper()]
        warning_lines = [line for line in logs.split('\n') if 'WARN' in line.upper()]
        
        if error_lines:
            print("发现错误:")
            for error in error_lines[-5:]:  # 最近 5 个错误
                print(f"  {error}")
                
        if warning_lines:
            print("发现警告:")
            for warning in warning_lines[-3:]:  # 最近 3 个警告
                print(f"  {warning}")
                
        return len(error_lines) == 0  # 返回是否无错误
    
    return False
```

### 🗑️ **6. 清空解析结果**

**端点**: `POST /clear_results`

**功能**: 清空历史解析结果，重新开始测试

**AI 调用示例**:
```python
def clear_results():
    url = "http://localhost:19000/clear_results"
    response = requests.post(url)
    return response.json()

# 在新测试前清空历史数据
clear_results()
```

---

## 🤖 完整的 AI 集成类

```python
import requests
import time
import json
from typing import Dict, List, Optional, Union

class LogstashTestService:
    """
    Logstash 测试服务 AI 客户端
    专为 AI 自动化调用设计
    """
    
    def __init__(self, base_url: str = "http://localhost:19000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def health_check(self) -> bool:
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/get_parsed_results", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_pipeline(self, pipeline_content: str, use_file: bool = True) -> Dict:
        """上传 Pipeline 配置（推荐方式）"""
        url = f"{self.base_url}/upload_pipeline"
        
        if use_file:
            # 方式一：文件上传（推荐）
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(pipeline_content)
                temp_file = f.name
            
            try:
                with open(temp_file, 'rb') as f:
                    files = {'file': ('pipeline.conf', f, 'text/plain')}
                    response = requests.post(url, files=files)
                return response.json()
            finally:
                os.unlink(temp_file)
        else:
            # 方式二：文本内容上传
            data = {"pipeline": pipeline_content}
            response = self.session.post(url, data=data)
            return response.json()
    
    def save_filter(self, filter_content: str) -> Dict:
        """保存 Filter 规则（传统方式）"""
        data = {"filter": filter_content}
        response = self.session.post(f"{self.base_url}/save_filter", data=data)
        return response.json()
    
    def send_test_log(self, logs: str, is_json: bool = False) -> Dict:
        """发送测试日志"""
        data = {"logs": logs}
        if is_json:
            data["is_json"] = "1"
        
        response = self.session.post(f"{self.base_url}/test", data=data)
        return response.json()
    
    def get_parsed_results(self) -> Dict:
        """获取解析结果"""
        response = self.session.get(f"{self.base_url}/get_parsed_results")
        return response.json()
    
    def get_logstash_logs(self) -> Dict:
        """获取 Logstash 日志"""
        response = self.session.get(f"{self.base_url}/logstash_logs")
        return response.json()
    
    def clear_results(self) -> Dict:
        """清空解析结果"""
        response = self.session.post(f"{self.base_url}/clear_results")
        return response.json()
    
    def test_pipeline_with_logs(self, pipeline_content: str, test_logs: List[str], 
                               is_json: bool = False, wait_time: int = 3, use_file: bool = True) -> Dict:
        """
        完整的 Pipeline 测试工作流：上传 pipeline -> 发送日志 -> 获取结果（推荐）
        
        Args:
            pipeline_content: 完整的 Pipeline 配置内容
            test_logs: 测试日志列表
            is_json: 是否为 JSON 格式日志
            wait_time: 等待热重载时间（秒）
            use_file: 是否使用文件上传方式
        
        Returns:
            包含测试结果的字典
        """
        result = {
            "success": False,
            "steps": {},
            "parsed_events": [],
            "errors": []
        }
        
        try:
            # 1. 健康检查
            if not self.health_check():
                result["errors"].append("服务不可用")
                return result
            result["steps"]["health_check"] = "✅ 服务可用"
            
            # 2. 清空历史结果
            clear_resp = self.clear_results()
            result["steps"]["clear_results"] = clear_resp.get("message", "清空完成")
            
            # 3. 上传 Pipeline
            upload_resp = self.upload_pipeline(pipeline_content, use_file)
            if not upload_resp.get("ok"):
                result["errors"].append(f"Pipeline 上传失败: {upload_resp.get('message')}")
                return result
            result["steps"]["upload_pipeline"] = upload_resp.get("message")
            
            # 4. 等待热重载
            time.sleep(wait_time)
            result["steps"]["wait_reload"] = f"等待 {wait_time} 秒热重载"
            
            # 5. 发送测试日志
            for i, log in enumerate(test_logs):
                send_resp = self.send_test_log(log, is_json)
                if send_resp.get("ok"):
                    result["steps"][f"send_log_{i+1}"] = send_resp.get("message")
                else:
                    result["errors"].append(f"日志 {i+1} 发送失败: {send_resp.get('message')}")
            
            # 6. 获取解析结果
            parsed_resp = self.get_parsed_results()
            if parsed_resp.get("ok"):
                result["parsed_events"] = parsed_resp.get("events", [])
                result["steps"]["get_results"] = f"获取到 {len(result['parsed_events'])} 条解析记录"
                result["success"] = True
            else:
                result["errors"].append(f"获取结果失败: {parsed_resp.get('message')}")
            
            # 7. 检查错误日志
            logs_resp = self.get_logstash_logs()
            if logs_resp.get("ok"):
                logs_content = logs_resp.get("logs", "")
                error_count = logs_content.upper().count("ERROR")
                if error_count > 0:
                    result["errors"].append(f"发现 {error_count} 个 Logstash 错误")
                result["steps"]["check_logs"] = f"检查日志完成，错误数: {error_count}"
            
        except Exception as e:
            result["errors"].append(f"执行异常: {str(e)}")
        
        return result

    def test_filter_with_logs(self, filter_content: str, test_logs: List[str], 
                             is_json: bool = False, wait_time: int = 3) -> Dict:
        """
        完整的测试工作流：保存 filter -> 发送日志 -> 获取结果
        
        Args:
            filter_content: Filter 规则内容
            test_logs: 测试日志列表
            is_json: 是否为 JSON 格式日志
            wait_time: 等待热重载时间（秒）
        
        Returns:
            包含测试结果的字典
        """
        result = {
            "success": False,
            "steps": {},
            "parsed_events": [],
            "errors": []
        }
        
        try:
            # 1. 健康检查
            if not self.health_check():
                result["errors"].append("服务不可用")
                return result
            result["steps"]["health_check"] = "✅ 服务可用"
            
            # 2. 清空历史结果
            clear_resp = self.clear_results()
            result["steps"]["clear_results"] = clear_resp.get("message", "清空完成")
            
            # 3. 保存 Filter
            save_resp = self.save_filter(filter_content)
            if not save_resp.get("ok"):
                result["errors"].append(f"Filter 保存失败: {save_resp.get('message')}")
                return result
            result["steps"]["save_filter"] = save_resp.get("message")
            
            # 4. 等待热重载
            time.sleep(wait_time)
            result["steps"]["wait_reload"] = f"等待 {wait_time} 秒热重载"
            
            # 5. 发送测试日志
            for i, log in enumerate(test_logs):
                send_resp = self.send_test_log(log, is_json)
                if send_resp.get("ok"):
                    result["steps"][f"send_log_{i+1}"] = send_resp.get("message")
                else:
                    result["errors"].append(f"日志 {i+1} 发送失败: {send_resp.get('message')}")
            
            # 6. 获取解析结果
            parsed_resp = self.get_parsed_results()
            if parsed_resp.get("ok"):
                result["parsed_events"] = parsed_resp.get("events", [])
                result["steps"]["get_results"] = f"获取到 {len(result['parsed_events'])} 条解析记录"
                result["success"] = True
            else:
                result["errors"].append(f"获取结果失败: {parsed_resp.get('message')}")
            
            # 7. 检查错误日志
            logs_resp = self.get_logstash_logs()
            if logs_resp.get("ok"):
                logs_content = logs_resp.get("logs", "")
                error_count = logs_content.upper().count("ERROR")
                if error_count > 0:
                    result["errors"].append(f"发现 {error_count} 个 Logstash 错误")
                result["steps"]["check_logs"] = f"检查日志完成，错误数: {error_count}"
            
        except Exception as e:
            result["errors"].append(f"执行异常: {str(e)}")
        
        return result
    
    def analyze_parsing_effectiveness(self, events: List[Dict]) -> Dict:
        """分析解析效果"""
        if not events:
            return {"effectiveness": 0, "details": "无解析结果"}
        
        analysis = {
            "total_events": len(events),
            "parsed_fields": {},
            "effectiveness": 0,
            "field_coverage": {},
            "details": []
        }
        
        # 统计字段分布
        all_fields = set()
        for event in events:
            event_fields = [k for k in event.keys() if not k.startswith('@') and k not in ['message', 'host']]
            all_fields.update(event_fields)
            
            for field in event_fields:
                if field not in analysis["parsed_fields"]:
                    analysis["parsed_fields"][field] = 0
                analysis["parsed_fields"][field] += 1
        
        # 计算字段覆盖率
        for field, count in analysis["parsed_fields"].items():
            coverage = (count / len(events)) * 100
            analysis["field_coverage"][field] = f"{coverage:.1f}%"
        
        # 计算整体有效性
        if len(all_fields) > 0:
            analysis["effectiveness"] = min(100, len(all_fields) * 10)  # 每个字段贡献10分，最高100分
        
        # 生成详细说明
        analysis["details"] = [
            f"共解析 {len(events)} 条日志",
            f"提取字段 {len(all_fields)} 个: {', '.join(sorted(all_fields))}",
            f"解析有效性评分: {analysis['effectiveness']}/100"
        ]
        
        return analysis

# 使用示例
def ai_test_example():
    """AI 调用示例 - 推荐使用 Pipeline 方式"""
    service = LogstashTestService()
    
    # 🌟 推荐方式：使用完整的 Pipeline 配置
    apache_pipeline = """
input {
  http {
    port => 15515
    additional_codecs => { "application/json" => "json" }
  }
}

filter {
  if "apache" == [@metadata][type] {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
    mutate {
      rename => { "clientip" => "src_ip" }
      add_field => { "log_type" => "apache_access" }
    }
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
      target => "@timestamp"
    }
  }
}

output {
  file {
    path => "/data/out/events.ndjson"
    codec => json_lines
  }
}
    """
    
    apache_logs = [
        '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326',
        '192.168.1.100 - - [25/Dec/2023:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 128'
    ]
    
    # 🌟 执行 Pipeline 测试（推荐）
    result = service.test_pipeline_with_logs(apache_pipeline, apache_logs)
    
    if result["success"]:
        print("✅ Pipeline 测试成功!")
        print("\n📋 执行步骤:")
        for step, message in result["steps"].items():
            print(f"  {step}: {message}")
        
        print(f"\n📊 解析结果: {len(result['parsed_events'])} 条记录")
        
        # 分析解析效果
        analysis = service.analyze_parsing_effectiveness(result["parsed_events"])
        print(f"\n📈 解析分析:")
        for detail in analysis["details"]:
            print(f"  {detail}")
            
        print(f"\n🔍 字段覆盖率:")
        for field, coverage in analysis["field_coverage"].items():
            print(f"  {field}: {coverage}")
            
    else:
        print("❌ Pipeline 测试失败!")
        for error in result["errors"]:
            print(f"  错误: {error}")

def ai_test_example_legacy():
    """AI 调用示例 - 传统 Filter 方式"""
    service = LogstashTestService()
    
    # 传统方式：仅使用 Filter 规则
    apache_filter = """
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
    mutate {
      rename => { "clientip" => "src_ip" }
      add_field => { "log_type" => "apache" }
    }
    """
    
    apache_logs = [
        '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326',
        '192.168.1.100 - - [25/Dec/2023:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 128'
    ]
    
    # 执行传统测试
    result = service.test_filter_with_logs(apache_filter, apache_logs)
    
    if result["success"]:
        print("✅ Filter 测试成功!")
        print(f"\n📊 解析结果: {len(result['parsed_events'])} 条记录")
        
        # 分析解析效果
        analysis = service.analyze_parsing_effectiveness(result["parsed_events"])
        print(f"\n📈 解析分析:")
        for detail in analysis["details"]:
            print(f"  {detail}")
    else:
        print("❌ Filter 测试失败!")
        for error in result["errors"]:
            print(f"  错误: {error}")

if __name__ == "__main__":
    # 推荐使用 Pipeline 方式
    ai_test_example()
    
    # 如果需要，也可以测试传统方式
    # ai_test_example_legacy()
```

---

## 🎯 AI 使用场景和模式

### 📊 **1. 日志格式验证**

```python
def validate_log_format(service, log_samples, expected_fields):
    """验证日志格式是否能正确解析出期望字段"""
    
    # 使用通用 grok 模式
    generic_filter = 'grok { match => { "message" => "%{GREEDYDATA:content}" } }'
    
    result = service.test_filter_with_logs(generic_filter, log_samples)
    
    if result["success"]:
        # 检查是否解析出期望字段
        events = result["parsed_events"]
        found_fields = set()
        
        for event in events:
            found_fields.update(event.keys())
        
        missing_fields = set(expected_fields) - found_fields
        extra_fields = found_fields - set(expected_fields) - {'@timestamp', 'message', 'host'}
        
        return {
            "valid": len(missing_fields) == 0,
            "found_fields": list(found_fields),
            "missing_fields": list(missing_fields),
            "extra_fields": list(extra_fields)
        }
    
    return {"valid": False, "error": result["errors"]}
```

### 🔧 **2. Filter 规则优化**

```python
def optimize_filter_rules(service, base_filter, test_logs, optimization_goals):
    """基于测试结果优化 Filter 规则"""
    
    results = []
    
    # 测试基础规则
    base_result = service.test_filter_with_logs(base_filter, test_logs)
    results.append({"type": "base", "filter": base_filter, "result": base_result})
    
    # 尝试不同的优化策略
    optimizations = [
        # 添加字段重命名
        base_filter + '\nmutate { rename => { "clientip" => "src_ip" } }',
        
        # 添加字段类型转换
        base_filter + '\nmutate { convert => { "response" => "integer", "bytes" => "integer" } }',
        
        # 添加条件处理
        base_filter + '\nif [response] >= 400 { mutate { add_tag => ["error"] } }'
    ]
    
    for i, opt_filter in enumerate(optimizations):
        opt_result = service.test_filter_with_logs(opt_filter, test_logs)
        results.append({"type": f"optimization_{i+1}", "filter": opt_filter, "result": opt_result})
    
    # 分析最佳规则
    best_result = max(results, key=lambda x: len(x["result"].get("parsed_events", [])))
    
    return {
        "best_filter": best_result["filter"],
        "all_results": results,
        "recommendation": f"推荐使用 {best_result['type']} 规则"
    }
```

### 🧪 **3. 批量日志测试**

```python
def batch_log_testing(service, log_samples_by_type):
    """批量测试不同类型的日志"""
    
    test_results = {}
    
    # 预定义的 Filter 模板
    filter_templates = {
        "apache": 'grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }',
        "json": 'json { source => "message" }',
        "syslog": 'grok { match => { "message" => "%{SYSLOGTIMESTAMP:timestamp} %{IPORHOST:host} %{PROG:program}: %{GREEDYDATA:log_message}" } }'
    }
    
    for log_type, log_samples in log_samples_by_type.items():
        print(f"\n🧪 测试 {log_type} 日志类型...")
        
        if log_type in filter_templates:
            filter_rule = filter_templates[log_type]
            is_json = log_type == "json"
            
            result = service.test_filter_with_logs(filter_rule, log_samples, is_json=is_json)
            
            # 分析结果
            if result["success"]:
                analysis = service.analyze_parsing_effectiveness(result["parsed_events"])
                test_results[log_type] = {
                    "success": True,
                    "events_count": len(result["parsed_events"]),
                    "effectiveness": analysis["effectiveness"],
                    "fields": list(analysis["parsed_fields"].keys())
                }
            else:
                test_results[log_type] = {
                    "success": False,
                    "errors": result["errors"]
                }
        else:
            test_results[log_type] = {
                "success": False,
                "errors": [f"未找到 {log_type} 类型的 Filter 模板"]
            }
    
    return test_results
```

---

## ⚠️ 注意事项和最佳实践

### 🚨 **错误处理**

```python
def robust_api_call(func, *args, **kwargs):
    """健壮的 API 调用包装器"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"连接失败，{retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise Exception("服务连接失败，请检查服务状态")
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"请求超时，{retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                raise Exception("服务响应超时")
        except Exception as e:
            raise Exception(f"API 调用异常: {str(e)}")
```

### ⏱️ **性能优化**

```python
# 1. 使用连接池
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
session.mount('http://', adapter)

# 2. 设置合理的超时
timeout_config = {
    "save_filter": 10,    # Filter 保存可能需要更长时间
    "test": 5,           # 发送日志
    "get_results": 3,    # 获取结果
    "logs": 8            # 获取日志可能较慢
}

# 3. 批量处理
def batch_send_logs(service, logs, batch_size=5):
    """批量发送日志，避免过于频繁的请求"""
    results = []
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i+batch_size]
        batch_content = '\n'.join(batch)
        result = service.send_test_log(batch_content)
        results.append(result)
        time.sleep(0.5)  # 短暂延迟避免过载
    return results
```

### 🔍 **调试支持**

```python
import logging

# 配置调试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebugLogstashService(LogstashTestService):
    """带调试功能的服务客户端"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = True
    
    def _debug_log(self, message):
        if self.debug:
            logger.debug(f"[LogstashService] {message}")
    
    def save_filter(self, filter_content):
        self._debug_log(f"保存 Filter: {len(filter_content)} 字符")
        result = super().save_filter(filter_content)
        self._debug_log(f"保存结果: {result.get('message')}")
        return result
    
    def send_test_log(self, logs, is_json=False):
        self._debug_log(f"发送日志: {len(logs)} 字符, JSON={is_json}")
        result = super().send_test_log(logs, is_json)
        self._debug_log(f"发送结果: {result.get('message')}")
        return result
```

---

## 📋 完整示例脚本

```python
#!/usr/bin/env python3
"""
完整的 AI 集成示例
演示如何使用 Logstash 测试服务进行自动化日志解析测试
"""

import sys
from logstash_service import LogstashTestService

def main():
    """主函数：完整的测试流程"""
    
    print("🤖 AI 集成测试开始...")
    
    # 初始化服务
    service = LogstashTestService()
    
    # 健康检查
    if not service.health_check():
        print("❌ 服务不可用，请检查 Logstash 测试服务状态")
        sys.exit(1)
    
    print("✅ 服务状态正常")
    
    # 🌟 推荐测试数据：使用完整 Pipeline 配置
    pipeline_test_cases = [
        {
            "name": "Apache 访问日志 Pipeline",
            "pipeline": """
input {
  http {
    port => 15515
    additional_codecs => { "application/json" => "json" }
  }
}

filter {
  if "apache" == [@metadata][type] {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
    mutate {
      rename => { "clientip" => "src_ip" }
      add_field => { "log_type" => "apache_access" }
    }
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
      target => "@timestamp"
    }
  }
}

output {
  file {
    path => "/data/out/events.ndjson"
    codec => json_lines
  }
}
            """,
            "logs": [
                '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326',
                '192.168.1.100 - user [25/Dec/2023:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 128'
            ],
            "is_json": False
        },
        {
            "name": "JSON 应用日志 Pipeline",
            "pipeline": """
input {
  http {
    port => 15515
    additional_codecs => { "application/json" => "json" }
  }
}

filter {
  if "json_app" == [@metadata][type] {
    json {
      source => "message"
    }
    if [level] {
      mutate {
        uppercase => ["level"]
      }
    }
    date {
      match => [ "timestamp", "ISO8601" ]
      target => "@timestamp"
    }
  }
}

output {
  file {
    path => "/data/out/events.ndjson"
    codec => json_lines
  }
}
            """,
            "logs": [
                '{"timestamp": "2023-12-25T10:00:00Z", "level": "info", "message": "用户登录成功", "user_id": 12345}',
                '{"timestamp": "2023-12-25T10:00:01Z", "level": "error", "message": "数据库连接失败", "error_code": 500}'
            ],
            "is_json": True
        }
    ]
    
    # 执行测试
    all_results = []
    
    for test_case in pipeline_test_cases:
        print(f"\n🧪 测试: {test_case['name']}")
        print(f"Pipeline: {test_case['pipeline'][:100]}...")
        
        # 🌟 使用 Pipeline 测试方法（推荐）
        result = service.test_pipeline_with_logs(
            test_case['pipeline'],
            test_case['logs'],
            is_json=test_case['is_json']
        )
        
        if result["success"]:
            print("✅ 测试成功")
            
            # 分析结果
            analysis = service.analyze_parsing_effectiveness(result["parsed_events"])
            print(f"📊 解析效果: {analysis['effectiveness']}/100")
            print(f"📋 提取字段: {', '.join(analysis['parsed_fields'].keys())}")
            
            all_results.append({
                "test_case": test_case['name'],
                "success": True,
                "analysis": analysis
            })
        else:
            print("❌ 测试失败")
            for error in result["errors"]:
                print(f"  错误: {error}")
            
            all_results.append({
                "test_case": test_case['name'],
                "success": False,
                "errors": result["errors"]
            })
    
    # 生成总结报告
    print("\n" + "="*50)
    print("📋 测试总结报告")
    print("="*50)
    
    success_count = sum(1 for r in all_results if r["success"])
    total_count = len(all_results)
    
    print(f"总测试数: {total_count}")
    print(f"成功数: {success_count}")
    print(f"成功率: {(success_count/total_count)*100:.1f}%")
    
    for result in all_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test_case']}")
        
        if result["success"]:
            analysis = result["analysis"]
            print(f"   解析效果: {analysis['effectiveness']}/100")
            print(f"   字段数量: {len(analysis['parsed_fields'])}")
        else:
            print(f"   错误: {'; '.join(result['errors'])}")
    
    print("\n🎉 AI 集成测试完成!")
    print("\n💡 **最佳实践提示**:")
    print("• 优先使用 service.test_pipeline_with_logs() 方法")
    print("• 避免 URL 编码问题，获得更好的测试体验") 
    print("• 如需使用传统方式，记得在 curl 命令中使用 --data-urlencode")

if __name__ == "__main__":
    main()
```

---

## 🔗 相关资源

- **项目主文档**: [README.md](README.md)
- **服务启动**: `./start.sh`
- **Web 界面**: http://localhost:19000
- **API 基础地址**: http://localhost:19000

---

## 📞 支持和反馈

如果 AI 在调用过程中遇到问题，可以：

1. **检查服务状态**: `curl http://localhost:19000/get_parsed_results`
2. **查看服务日志**: `docker compose logs -f`
3. **重启服务**: `docker compose restart`
4. **检查网络连接**: 确保端口 19000 可访问

**常见问题**:
- 服务不响应 → 检查 Docker 容器状态
- 解析结果为空 → 检查 Filter 语法和日志格式匹配
- 热重载失败 → 等待更长时间或手动重启服务

---

*本文档专为 AI 系统设计，提供了完整的调用指南和示例代码。*
