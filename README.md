# 🚀 Logstash 规则测试工具

<div align="center">

[![GitHub release](https://img.shields.io/github/release/username/logstash-lab.svg)](https://github.com/username/logstash-lab/releases)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**一个现代化的 Logstash 规则测试和调试工具**

提供直观的 Web 界面，支持实时编辑、测试和调试 Logstash filter 规则

[快速开始](#-快速开始) • [功能演示](#-功能演示) • [使用指南](#-使用指南) • [API 文档](#-api-文档)

</div>

---

## 📸 功能演示

### 主界面概览
![Logstash 测试工具主界面](./docs/screenshots/main-interface.jpg)

### 核心功能
- 🎯 **智能 Filter 编辑器**: 支持语法高亮和自动完成
- ⚡ **实时热重载**: 规则修改 3 秒内自动生效
- 🔍 **解析结果查看**: JSON 格式美化显示，支持一键获取
- 📊 **示例模板库**: 内置常用日志格式模板
- 🔧 **日志调试**: 实时查看 Logstash 运行日志
- 💾 **配置持久化**: 自动保存用户输入，刷新不丢失
- 🌊 **MCP 服务器**: 为 AI 提供 SSE 流式调用接口，支持实时进度反馈和文件上传

## ✨ 核心特性

### 🎯 **智能化 Metadata 管理**
- **自动条件判断替换**: 无论输入任何 `if "xxx" == [@metadata][type]` 条件，自动统一为 `if "test" == [@metadata][type]`
- **元数据自动设置**: 系统自动设置 `[@metadata][type] = "test"`，确保配置一致性
- **简化配置管理**: 用户专注编写 filter 逻辑，无需关心条件判断和元数据匹配

### 🔧 **先进的编辑体验**
- **宽屏自适应布局**: 充分利用屏幕空间，支持大屏显示
- **实时配置验证**: 保存时自动检查 Logstash 配置语法
- **热重载机制**: 配置修改后 3 秒内自动重新加载
- **配置持久化**: 使用 localStorage 保存用户输入，页面刷新不丢失

### 📊 **全面的调试功能**  
- **解析结果实时查看**: 发送日志后立即显示解析结果
- **历史记录获取**: 一键获取最新 50 条解析记录
- **JSON 美化显示**: 格式化输出，易于阅读和分析
- **Logstash 日志查看**: 内置日志查看功能，快速定位问题

### 🚀 **开发友好特性**
- **Docker 化部署**: 一键启动，无需复杂环境配置
- **开发模式支持**: 代码修改自动重载，适合开发调试
- **RESTful API**: 提供完整 API 接口，支持自动化测试
- **跨平台支持**: Linux、macOS、Windows 全平台支持

## 🚀 快速开始

### 系统要求
- Docker 20.0+
- Docker Compose 2.0+
- 可用内存 1GB+

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/username/logstash-lab.git
cd logstash-lab

# 2. 启动服务（推荐）
./start.sh

# 或手动启动
sudo docker compose up -d --build
```

### 访问服务

```bash
# Web 界面
http://localhost:19000

# MCP 服务器
http://localhost:19001

# 健康检查
curl http://localhost:19001/tools/health_check

# 服务状态检查
sudo docker compose ps
```

### 🔗 MCP 客户端配置

为 AI 客户端（如 Cursor、Claude Desktop）配置 MCP 连接：

#### 最简单配置 (推荐)
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

#### 兼容性配置
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

**配置位置**:
- **Cursor**: `~/.cursor/mcp.json`
- **Claude Desktop (macOS)**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Desktop (Windows)**: `%APPDATA%/Claude/claude_desktop_config.json`

**📚 详细配置指南**: 查看 [MCP 服务器文档](mcp_server/README.md)

## 📖 使用指南

### 基本工作流

#### 🌟 推荐方式：Pipeline 文件上传

1. **📁 准备 Pipeline 配置文件**
   ```logstash
   # your_pipeline.conf
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
       # 更多 filter 规则...
     }
   }
   
   output {
     kafka {
       bootstrap_servers => "localhost:9092"
       topic_id => "logs"
     }
   }
   ```

2. **🚀 上传并自动应用**
   ```bash
   # 方式一：文件上传（最推荐）
   curl -X POST http://localhost:19000/upload_pipeline -F 'file=@your_pipeline.conf'
   
   # 方式二：Web 界面上传
   # 访问 http://localhost:19000 → Pipeline 文件上传区域 → 选择文件或粘贴内容
   ```

#### 🔧 传统方式：直接编辑 Filter

1. **📝 编辑 Filter 规则**
   ```logstash
   # 输入您的 filter 规则，支持任何条件判断格式
   filter {
     if "apache" == [@metadata][type] {  # 会自动替换为 "test"
       grok {
         match => { "message" => "%{COMBINEDAPACHELOG}" }
       }
       mutate {
         rename => { "clientip" => "src_ip" }
       }
     }
   }
   ```

2. **💾 保存并自动重载**
   - 点击"保存 Filter"按钮
   - 系统自动重载配置（3秒内生效）
   - 自动设置正确的元数据类型

#### 🧪 共同步骤：测试和验证

3. **📝 输入测试数据**
   ```bash
   # Web 界面：直接在"测试日志"区域输入
   127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326
   
   # API 调用：推荐使用 --data-urlencode
   curl -X POST http://localhost:19000/test \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "logs=<133>1 2025-09-10T12:08:07+08:00 SGPDRT-VSBRS01 BG 16703 - [meta sequenceId=\"46\"] session_data"
   ```

4. **🚀 发送并查看结果**
   - **Web 界面**: 点击"发送并查看解析结果"按钮
   - **API 调用**: 使用 `/get_parsed_results` 接口
   - 实时查看 JSON 格式的解析结果
   - 使用"获取解析后的记录"查看历史记录

#### ⭐ 最佳实践

- **首选 Pipeline 文件上传**: 避免 URL 编码和格式问题
- **使用 `--data-urlencode`**: 处理特殊字符（如 `+` 号）
- **测试前清空结果**: 确保结果的准确性
- **查看 Logstash 日志**: 及时发现配置错误

### 内置示例模板

| 模板类型 | 描述 | 适用场景 |
|---------|------|----------|
| **Apache 日志** | COMBINEDAPACHELOG 格式 | Web 服务器访问日志 |
| **JSON 日志** | 结构化 JSON 格式 | 应用程序日志 |
| **Syslog** | 标准 syslog 格式 | 系统日志 |
| **自定义格式** | 用户自定义规则 | 特殊格式日志 |

### 高级功能

#### 🔍 **调试和排错**

```bash
# 查看实时日志
sudo docker compose logs -f logstash

# 查看解析结果
tail -f data/out/events.ndjson

# 检查配置语法
sudo docker compose exec logstash bin/logstash --config.test_and_exit
```

#### ⚙️ **自定义配置**

```yaml
# docker-compose.yml 自定义端口
services:
  web:
    ports:
      - "8080:19000"  # 修改 Web 端口
  logstash:
    environment:
      - LS_JAVA_OPTS=-Xms1g -Xmx2g  # 调整内存
```

## 🏗️ 项目架构

```
logstash-lab/
├── 📄 docker-compose.yml          # Docker 服务编排
├── 🚀 start.sh                    # 启动脚本
├── 🌐 web/                        # Web 应用
│   ├── 🐳 Dockerfile              # Web 服务容器
│   ├── 🐍 app.py                  # Flask 后端应用
│   └── 📱 templates/index.html    # 前端界面
├── ⚙️ logstash/                   # Logstash 配置
│   ├── 📝 logstash.yml            # 主配置文件
│   └── 🔧 pipeline/test.conf      # Pipeline 规则
├── 💾 data/out/                   # 输出数据
│   └── 📊 events.ndjson           # 解析结果
└── 📚 docs/                       # 文档和截图
    └── 📸 screenshots/            # 功能截图
```

## 🛠️ 技术栈

| 组件 | 技术选型 | 版本 | 作用 |
|------|----------|------|------|
| **后端框架** | Flask + Waitress | 2.3+ | Web 服务和 API |
| **日志处理** | Logstash | 8.14.2 | 规则解析引擎 |
| **前端技术** | HTML5 + CSS3 + JS | ES6+ | 用户界面 |
| **容器化** | Docker + Compose | 20.0+ | 服务编排 |
| **数据存储** | NDJSON Files | - | 轻量级数据存储 |

## 📋 API 文档

### 核心 API 端点概览

| 端点 | 方法 | 描述 | 状态码 |
|------|------|------|--------|
| `/upload_pipeline` | POST | 🌟 **推荐** 上传完整 pipeline 文件并自动提取 filter | 200 |
| `/save_filter` | POST | 保存和更新 filter 配置 | 200 |
| `/test` | POST | 发送测试日志并获取解析结果 | 200 |
| `/get_parsed_results` | GET | 获取最新的解析记录 | 200 |
| `/logstash_logs` | GET | 获取 Logstash 运行日志 | 200 |
| `/clear_results` | POST | 清空解析结果文件 | 200 |

---

### 🌟 1. Pipeline 文件上传接口（推荐）

**端点**: `/upload_pipeline`  
**方法**: `POST`  
**描述**: 上传完整的 Logstash pipeline 配置文件，系统自动提取 filter 块并应用到测试环境

#### 优势特性

- ✅ **完全避免 URL 编码问题**: 不会出现 `+` 号变空格等编码问题
- ✅ **保持原始格式**: 自动保留换行符、缩进和注释
- ✅ **智能解析**: 自动识别和提取 filter 块，支持复杂嵌套结构
- ✅ **双重支持**: 同时支持文件上传和文本内容粘贴
- ✅ **无缝集成**: 自动应用到测试环境，无需额外配置

#### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file` | File | 否* | Pipeline 配置文件 (.conf/.txt) |
| `pipeline` | string | 否* | Pipeline 配置文本内容 |

*注：`file` 和 `pipeline` 二选一*

#### 请求示例

```bash
# 🎯 方式一：文件上传（最推荐）
curl -X POST http://localhost:19000/upload_pipeline \
  -F 'file=@your_pipeline.conf'

# 🎯 方式二：文本内容上传
curl -X POST http://localhost:19000/upload_pipeline \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'pipeline=input {
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
      # 更多 filter 规则...
    }
  }
  
  output {
    kafka {
      bootstrap_servers => "localhost:9092"
      topic_id => "logs"
    }
  }'

# 🎯 方式三：从已有配置文件提取
curl -X POST http://localhost:19000/upload_pipeline \
  -F 'file=@/etc/logstash/pipelines.d/production.conf'
```

#### 响应示例

```json
{
  "ok": true,
  "message": "Pipeline 已成功上传并应用到测试环境",
  "extracted_filters": 1,
  "applied_filter_preview": "    if \"bomgar\" == [@metadata][type] {\n        grok {\n            match => { \"message\" => \"<%{POSINT:syslog_pri}>%{POSINT:syslog_ver}...\" }\n        }\n        # Parse bomgar specific fields...\n    }"
}
```

#### Web 界面使用

1. 访问 `http://localhost:19000`
2. 在 **"Pipeline 文件上传"** 区域：
   - **文件上传**: 点击 "选择文件" 上传 `.conf` 文件
   - **直接粘贴**: 点击 "直接粘贴内容" 输入配置
3. 系统自动解析并显示提取的 filter 预览
4. 配置立即应用到测试环境，无需额外操作

---

### 🔧 2. 编辑 Filter 接口

**端点**: `/save_filter`  
**方法**: `POST`  
**描述**: 保存 Logstash filter 配置，支持智能条件判断替换和热重载

> ⚠️ **注意**: 此接口可能遇到 URL 编码问题（如 `+` 号变空格）和换行符处理问题。**推荐使用 `/upload_pipeline` 接口**以获得更好的体验。

#### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `filter` | string | 是 | Logstash filter 配置内容 |

#### 请求示例

```bash
# ✅ 推荐方式：使用 --data-urlencode 避免编码问题
curl -X POST http://localhost:19000/save_filter \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "filter=grok { match => { \"message\" => \"%{COMBINEDAPACHELOG}\" } }"

# ⚠️ 可能有问题：使用 -d 可能导致特殊字符编码错误
curl -X POST http://localhost:19000/save_filter \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "filter=grok { match => { \"message\" => \"%{COMBINEDAPACHELOG}\" } }"

# ✅ 推荐方式：使用文件避免转义问题
echo 'filter=grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }' > /tmp/filter.txt
curl -X POST http://localhost:19000/save_filter \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data @/tmp/filter.txt

# ❌ 复杂配置建议使用 /upload_pipeline 接口
# 以下示例可能出现换行符丢失等问题
curl -X POST http://localhost:19000/save_filter \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "filter=filter {
    if \"apache\" == [@metadata][type] {
      grok {
        match => { \"message\" => \"%{COMBINEDAPACHELOG}\" }
      }
      mutate {
        rename => { \"clientip\" => \"src_ip\" }
      }
    }
  }"
```

#### URL 编码问题说明

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `+` 号变空格 | `curl -d` 自动进行 URL 解码 | 使用 `--data-urlencode` 或手动编码为 `%2B` |
| 换行符丢失 | Web 应用换行符处理 Bug | 使用 `/upload_pipeline` 接口 |
| 特殊字符错误 | 多层转义导致语法错误 | 使用文件传输或 `/upload_pipeline` |

#### 响应示例

```json
{
  "ok": true,
  "message": "Filter 已保存并自动重载 (已自动添加条件判断: if \"test\" == [@metadata][type])"
}
```

#### 智能功能说明

- **自动条件判断替换**: 任何 `if "xxx" == [@metadata][type]` 会自动替换为 `if "test" == [@metadata][type]`
- **元数据自动设置**: 系统自动设置 `[@metadata][type] = "test"`
- **热重载**: 配置保存后 3 秒内自动生效
- **语法验证**: 保存时自动检查 Logstash 配置语法

---

### 📊 3. 获取解析结果接口

**端点**: `/get_parsed_results`  
**方法**: `GET`  
**描述**: 获取最新的解析记录，支持实时查看处理结果

#### 请求示例

```bash
# 获取最新解析记录
curl http://localhost:19000/get_parsed_results

# 使用 jq 美化输出
curl -s http://localhost:19000/get_parsed_results | jq .

# 只获取记录数量
curl -s http://localhost:19000/get_parsed_results | jq .count

# 获取特定字段
curl -s http://localhost:19000/get_parsed_results | jq '.events[] | {timestamp: .["@timestamp"], message: .message}'
```

#### 响应示例

```json
{
  "ok": true,
  "events": [
    {
      "@timestamp": "2024-12-25T10:00:00.000Z",
      "message": "127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326",
      "clientip": "127.0.0.1",
      "verb": "GET",
      "request": "/index.html",
      "httpversion": "1.1",
      "response": "200",
      "bytes": "2326",
      "src_ip": "127.0.0.1",
      "__source": "test",
      "_parsed_time": "2024-12-25 10:00:15",
      "host": {
        "name": "logstash-container"
      }
    }
  ],
  "count": 1,
  "message": "成功获取 1 条解析记录"
}
```

#### 功能特性

- **最新记录**: 获取最后 50 条解析记录
- **时间戳**: 每条记录包含 `_parsed_time` 解析时间
- **字段完整**: 包含所有 filter 处理后的字段
- **实时更新**: 支持轮询获取最新数据

---

### 📋 4. 获取 Logstash 日志接口

**端点**: `/logstash_logs`  
**方法**: `GET`  
**描述**: 获取 Logstash 运行日志，用于调试和问题排查

#### 请求示例

```bash
# 获取 Logstash 日志
curl http://localhost:19000/logstash_logs

# 保存日志到文件
curl -s http://localhost:19000/logstash_logs | jq -r .logs > logstash.log

# 检查错误信息
curl -s http://localhost:19000/logstash_logs | jq -r .logs | grep -i error

# 实时监控（每5秒刷新）
watch -n 5 'curl -s http://localhost:19000/logstash_logs | jq -r .logs | tail -20'
```

#### 响应示例

```json
{
  "ok": true,
  "logs": "📋 Logstash 容器日志 (Docker API)\n📅 获取时间: 2024-12-25 10:00:15\n📊 显示最近 50 条日志\n================================================================================\n[2024-12-25T10:00:00,123][INFO ][logstash.agent           ] Successfully started Logstash API endpoint {:port=>9600}\n[2024-12-25T10:00:01,456][INFO ][logstash.runner          ] Starting Logstash {\"logstash.version\"=>\"8.14.2\"}\n[2024-12-25T10:00:02,789][INFO ][logstash.javapipeline    ][test] Pipeline started {\"pipeline.id\"=>\"test\"}\n[2024-12-25T10:00:03,012][INFO ][logstash.inputs.http     ][test] Starting http input listener {:address=>\"0.0.0.0:15515\"}\n[2024-12-25T10:00:05,345][INFO ][logstash.pipeline        ][test] Pipeline successfully reloaded"
}
```

#### 日志内容说明

- **启动信息**: Logstash 服务启动状态
- **Pipeline 状态**: 管道加载和重载信息
- **错误信息**: 配置语法错误和运行异常
- **性能信息**: 处理速度和内存使用
- **网络状态**: HTTP 输入端口监听状态

---

### 🧪 5. 发送测试日志接口

**端点**: `/test`  
**方法**: `POST`  
**描述**: 发送测试日志到 Logstash 并获取解析结果

#### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `logs` | string | 是 | 要测试的日志内容 |
| `is_json` | string | 否 | 是否为 JSON 格式 (值为 "1" 表示是) |

#### 请求示例

```bash
# ✅ 推荐方式：使用 --data-urlencode 避免特殊字符问题
curl -X POST http://localhost:19000/test \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "logs=127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326"

# ✅ 发送包含 + 号的日志（时间戳、URL编码等）
curl -X POST http://localhost:19000/test \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "logs=<133>1 2025-09-10T12:08:07+08:00 SGPDRT-VSBRS01 BG 16703 - [meta sequenceId=\"46\"] session_data"

# ✅ 发送 JSON 格式日志
curl -X POST http://localhost:19000/test \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "logs={\"timestamp\": \"2023-12-25T10:00:00Z\", \"level\": \"info\", \"message\": \"用户登录成功\"}" \
  -d "is_json=1"

# ⚠️ 不推荐：使用 -d 可能导致 + 号变空格
curl -X POST http://localhost:19000/test \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "logs=<133>1 2025-09-10T12:08:07+08:00 server BG 16703 - log_content"  # + 会变成空格

# 🎯 完整测试流程示例
# 1. 上传配置
curl -X POST http://localhost:19000/upload_pipeline -F 'file=@bomgar.config'

# 2. 清空结果
curl -X POST http://localhost:19000/clear_results

# 3. 发送测试日志
curl -X POST http://localhost:19000/test \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "logs=<133>1 2025-09-10T12:08:07+08:00 SGPDRT-VSBRS01 BG 16703 - [meta sequenceId=\"46\"] 1427:01:01:event=logout;site=remote.cit.seabank.com.sg;target=rep_client;when=1757477287;who=unknown;who_ip=116.12.204.154"

# 4. 获取解析结果
curl -s http://localhost:19000/get_parsed_results | jq '.events[-1]'
```

#### 响应示例

```json
{
  "ok": true,
  "message": "✅ 日志发送成功",
  "events": [
    {
      "@timestamp": "2024-12-25T10:00:00.000Z",
      "message": "127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326",
      "clientip": "127.0.0.1",
      "verb": "GET",
      "request": "/index.html",
      "httpversion": "1.1",
      "response": "200",
      "bytes": "2326",
      "src_ip": "127.0.0.1"
    }
  ]
}
```

#### ⚠️ 重要提示

| 问题类型 | 现象 | 解决方案 |
|----------|------|----------|
| **时间戳中的 `+` 号问题** | `2025-09-10T12:08:07+08:00` → `2025-09-10T12:08:07 08:00` | 使用 `--data-urlencode` 或手动编码为 `%2B` |
| **特殊字符编码** | `&`, `=`, `%` 等被错误解释 | 使用 `--data-urlencode` |
| **多行日志处理** | 换行符丢失或错误处理 | 使用 `--data-urlencode` 或文件传输 |

---

### 🗑️ 6. 清空结果接口

**端点**: `/clear_results`  
**方法**: `POST`  
**描述**: 清空解析结果文件，用于重新开始测试

#### 请求示例

```bash
# 清空解析结果
curl -X POST http://localhost:19000/clear_results

# 清空并确认
curl -X POST http://localhost:19000/clear_results && \
curl http://localhost:19000/get_parsed_results | jq .count
```

#### 响应示例

```json
{
  "ok": true,
  "message": "结果已清空"
}
```

---

### 📡 API 使用最佳实践

#### 🔄 **完整的测试工作流**

```bash
#!/bin/bash
# Logstash 规则测试脚本

BASE_URL="http://localhost:19000"

echo "🧹 1. 清空历史结果"
curl -s -X POST "$BASE_URL/clear_results" | jq .message

echo -e "\n🔧 2. 更新 Filter 规则"
curl -s -X POST "$BASE_URL/save_filter" \
  -d "filter=grok { match => { \"message\" => \"%{COMBINEDAPACHELOG}\" } }" \
  | jq .message

echo -e "\n⏱️ 3. 等待热重载完成"
sleep 3

echo -e "\n🧪 4. 发送测试日志"
curl -s -X POST "$BASE_URL/test" \
  -d "logs=127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326" \
  | jq .message

echo -e "\n📊 5. 获取解析结果"
curl -s "$BASE_URL/get_parsed_results" | jq '.events[] | {client: .clientip, method: .verb, path: .request}'

echo -e "\n📋 6. 检查 Logstash 日志"
curl -s "$BASE_URL/logstash_logs" | jq -r .logs | tail -5
```

#### 🔍 **错误处理示例**

```bash
# 检查 API 响应状态
response=$(curl -s -X POST http://localhost:19000/save_filter -d "filter=invalid syntax")
status=$(echo "$response" | jq -r .ok)

if [ "$status" = "true" ]; then
  echo "✅ Filter 保存成功"
else
  echo "❌ Filter 保存失败: $(echo "$response" | jq -r .message)"
fi

# 检查服务是否运行
if curl -s http://localhost:19000/get_parsed_results > /dev/null; then
  echo "✅ 服务运行正常"
else
  echo "❌ 服务不可访问，请检查容器状态"
fi
```

#### 📈 **性能监控脚本**

```bash
#!/bin/bash
# 监控 Logstash 性能

while true; do
  # 获取当前记录数
  count=$(curl -s http://localhost:19000/get_parsed_results | jq .count)
  
  # 检查内存使用
  memory=$(docker stats logstash-lab-logstash --no-stream --format "table {{.MemUsage}}" | tail -1)
  
  # 检查错误日志
  errors=$(curl -s http://localhost:19000/logstash_logs | jq -r .logs | grep -c ERROR || echo 0)
  
  echo "$(date): 记录数=$count, 内存=$memory, 错误=$errors"
  sleep 10
done
```

### 🌐 前端 JavaScript 集成

```javascript
// Logstash API 客户端类
class LogstashAPI {
  constructor(baseURL = 'http://localhost:19000') {
    this.baseURL = baseURL;
  }

  // 保存 filter 配置
  async saveFilter(filterContent) {
    const response = await fetch(`${this.baseURL}/save_filter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `filter=${encodeURIComponent(filterContent)}`
    });
    return response.json();
  }

  // 发送测试日志
  async sendTestLog(logs, isJSON = false) {
    const body = `logs=${encodeURIComponent(logs)}${isJSON ? '&is_json=1' : ''}`;
    const response = await fetch(`${this.baseURL}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body
    });
    return response.json();
  }

  // 获取解析结果
  async getParsedResults() {
    const response = await fetch(`${this.baseURL}/get_parsed_results`);
    return response.json();
  }

  // 获取 Logstash 日志
  async getLogstashLogs() {
    const response = await fetch(`${this.baseURL}/logstash_logs`);
    return response.json();
  }

  // 清空结果
  async clearResults() {
    const response = await fetch(`${this.baseURL}/clear_results`, { method: 'POST' });
    return response.json();
  }
}

// 使用示例
const api = new LogstashAPI();

// 保存 filter 并测试
async function testFilter() {
  try {
    // 1. 保存 filter
    await api.saveFilter('grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }');
    
    // 2. 等待重载
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // 3. 发送测试日志
    const testResult = await api.sendTestLog('127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326');
    
    // 4. 获取解析结果
    const results = await api.getParsedResults();
    
    console.log('解析结果:', results.events);
  } catch (error) {
    console.error('测试失败:', error);
  }
}
```

### 通用响应格式

所有 API 端点都返回统一的 JSON 格式：

```json
{
  "ok": true|false,
  "message": "操作状态描述",
  "data": {...},       // 可选，具体数据
  "events": [...],     // 可选，事件数组
  "count": 0,          // 可选，记录数量
  "logs": "..."        // 可选，日志内容
}
```

## 🌊 MCP 服务器使用指南

### 概述

MCP (Model Context Protocol) 服务器为 AI 和自动化工具提供了标准化的 Logstash 测试接口。它支持：
- 🚀 **文件上传**: 直接上传 Pipeline 配置文件
- 🌊 **SSE 流式反馈**: 实时监控测试进度
- ⚡ **自动化集成**: 标准 REST API 接口
- 🔄 **智能替换**: 自动处理条件判断和元数据

### 🌐 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **Web 界面** | http://localhost:19000 | 主要测试界面 |
| **MCP 服务器** | http://localhost:19001 | AI 调用接口 |
| **SSE 测试页面** | http://localhost:19001/test | 内置测试界面 |
| **API 文档** | http://localhost:19001/docs | 完整 API 文档 |

### 🚀 快速开始

#### 1. 使用内置测试页面（推荐）

```bash
# 在浏览器中打开 SSE 测试页面
open http://localhost:19001/test
```

这个页面提供了完整的可视化测试环境，包括：
- Pipeline 配置编辑器
- 测试日志输入框  
- 实时 SSE 流式反馈
- 步骤级进度追踪

#### 2. 文件上传方式

```bash
# 上传 Pipeline 配置文件
curl -X POST http://localhost:19001/tools/upload_pipeline \
  -F 'file=@your_pipeline.conf'

# 响应示例
{
  "success": true,
  "message": "Pipeline 已成功上传并应用到测试环境",
  "extracted_filters": 1,
  "preview": "if \"test\" == [@metadata][type] { ... }"
}
```

#### 3. SSE 流式测试

```bash
# 使用 curl 测试 SSE 连接（注意 -N 参数保持连接）
curl -N "http://localhost:19001/sse/test_pipeline_complete?pipeline_content=filter{grok{match=>{\"message\"=>\"%{GREEDYDATA:content\"}}}&test_logs=[\"test log message\"]"
```

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

# 或者使用测试页面
http://192.168.31.218:19001/test
```

### 🛠️ 故障排除

#### Docker 构建缓存问题

如果修改代码后容器没有更新，使用以下命令清理缓存：

```bash
# 清理 Docker 缓存
sudo docker system prune -f

# 强制重新构建
sudo docker compose build --no-cache mcp-server

# 重启服务
sudo docker compose restart mcp-server
```

#### 服务健康检查

```bash
# 检查 MCP 服务器状态
curl http://localhost:19001/tools/health_check

# 检查容器状态
sudo docker compose ps

# 查看 MCP 服务器日志
sudo docker compose logs -f mcp-server
```

#### 网络连接问题

```bash
# 检查端口是否正在监听
sudo netstat -tlnp | grep 19001

# 检查容器网络
sudo docker network ls
sudo docker network inspect logstash-lab_default
```

### 📋 MCP 工具列表

| 工具名称 | 功能描述 | 输入格式 |
|----------|----------|----------|
| `upload_pipeline` | 上传 Pipeline 配置 | 文件/表单/JSON |
| `send_test_log` | 发送测试日志 | JSON |
| `get_parsed_results` | 获取解析结果 | GET |
| `clear_results` | 清空测试结果 | POST |
| `get_logstash_logs` | 获取 Logstash 日志 | GET |
| `health_check` | 健康状态检查 | GET |
| `test_pipeline_complete_stream` | SSE 流式完整测试 | SSE |

### 🎯 AI 集成示例

```python
import requests
import json

# 上传 Pipeline 配置
def upload_pipeline(config_file):
    with open(config_file, 'rb') as f:
        response = requests.post(
            'http://localhost:19001/tools/upload_pipeline',
            files={'file': f}
        )
    return response.json()

# 发送测试日志
def test_log(log_content):
    response = requests.post(
        'http://localhost:19001/tools/send_test_log',
        json={'log_content': log_content}
    )
    return response.json()

# 使用示例
result = upload_pipeline('bomgar.conf')
if result['success']:
    test_result = test_log('test log message')
    print(f"解析结果: {test_result['latest_event']}")
```

更多详细信息请参考：[MCP 服务器完整文档](mcp_server/README.md)

## 🔧 常用命令

### 服务管理
```bash
# 启动服务
sudo docker compose up -d --build

# 查看服务状态  
sudo docker compose ps

# 重启特定服务
sudo docker compose restart web
sudo docker compose restart logstash

# 停止所有服务
sudo docker compose down
```

### 日志查看
```bash
# 实时查看所有日志
sudo docker compose logs -f

# 查看 Logstash 日志（最近50条）
sudo docker compose logs --tail=50 logstash

# 查看错误日志
sudo docker compose logs logstash | grep -i error

# 监控解析结果
tail -f data/out/events.ndjson | jq .
```

### 开发调试
```bash
# 进入容器调试
sudo docker exec -it logstash-lab-web bash
sudo docker exec -it logstash-lab-logstash bash

# 检查配置语法
sudo docker exec logstash-lab-logstash bin/logstash --config.test_and_exit

# 重新构建镜像
sudo docker compose build --no-cache
```

## 🐛 故障排除

### 常见问题

<details>
<summary><b>📌 Web 界面无法访问</b></summary>

**可能原因：**
- 端口被占用
- 容器启动失败
- 防火墙阻止

**解决方案：**
```bash
# 1. 检查端口占用
lsof -i :19000

# 2. 查看容器状态
sudo docker compose ps

# 3. 查看容器日志
sudo docker compose logs web

# 4. 重新构建
sudo docker compose build --no-cache web
sudo docker compose up -d
```
</details>

<details>
<summary><b>📌 Logstash 启动失败</b></summary>

**可能原因：**
- 内存不足
- 配置语法错误
- 端口冲突

**解决方案：**
```bash
# 1. 检查内存使用
free -h

# 2. 验证配置语法  
sudo docker exec logstash-lab-logstash bin/logstash --config.test_and_exit

# 3. 查看详细日志
sudo docker compose logs --tail=100 logstash

# 4. 调整内存限制
# 编辑 docker-compose.yml 中的 LS_JAVA_OPTS
```
</details>

<details>
<summary><b>📌 Filter 规则不生效</b></summary>

**可能原因：**
- 语法错误
- 条件判断不匹配
- 热重载未完成

**解决方案：**
```bash
# 1. 检查语法错误
sudo docker compose logs --tail=20 logstash | grep -i error

# 2. 等待热重载完成（3-5秒）

# 3. 手动重启 Logstash
sudo docker compose restart logstash

# 4. 使用系统自动处理条件判断
# 输入任何条件，系统会自动替换为 "test"
```
</details>

### 性能优化建议

1. **内存配置**：根据日志量调整 Logstash 内存
2. **磁盘空间**：定期清理 `data/out/events.ndjson`
3. **网络配置**：确保容器间网络通信正常
4. **规则优化**：避免过于复杂的正则表达式

## 🔐 安全注意事项

- ⚠️ **仅限测试环境使用**，不要在生产环境暴露端口
- 🛡️ **不要处理敏感数据**，本工具用于规则测试
- 🔒 **网络隔离**，建议在内网环境使用
- 🔐 **定期更新**，保持 Docker 镜像为最新版本

## 📊 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **CPU** | 1 核心 | 2+ 核心 |
| **内存** | 1GB | 2GB+ |
| **磁盘** | 2GB | 5GB+ |
| **网络** | 1Mbps | 10Mbps+ |

## 🎯 使用技巧

### 💡 **Filter 规则编写技巧**

1. **从简单开始**：先用基本的 grok 模式测试
2. **逐步添加**：确认基础规则工作后再添加复杂逻辑
3. **使用条件判断**：提高处理效率
4. **善用示例模板**：基于内置模板修改更高效

### 🔍 **调试技巧**

1. **查看原始输出**：使用 stdout 输出查看中间结果
2. **分步测试**：将复杂规则拆分为多个步骤测试
3. **使用 Logstash 日志**：及时查看错误信息
4. **JSON 模式测试**：对于结构化数据使用 JSON 输入模式

### ⚡ **性能优化技巧**

1. **避免过度解析**：只解析需要的字段
2. **合理使用条件**：减少不必要的处理
3. **定期清理数据**：避免输出文件过大
4. **内存监控**：关注 Logstash 内存使用

## 📚 学习资源

- 📖 [Logstash 官方文档](https://www.elastic.co/guide/en/logstash/current/index.html)
- 🔍 [Grok 模式库](https://github.com/elastic/logstash/blob/v1.4.2/patterns/grok-patterns)
- 🔧 [Filter 插件文档](https://www.elastic.co/guide/en/logstash/current/filter-plugins.html)
- 🐍 [Flask 快速入门](https://flask.palletsprojects.com/quickstart/)
- 🐳 [Docker Compose 指南](https://docs.docker.com/compose/)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Elastic](https://www.elastic.co/) - 提供强大的 Logstash 引擎
- [Flask](https://flask.palletsprojects.com/) - 简洁的 Python Web 框架
- [Docker](https://www.docker.com/) - 容器化技术支持

## 📚 相关文档

- **[AI 集成指南](AI_INTEGRATION_GUIDE.md)**: 为第三方 AI 提供完整的调用指南
- **[MCP 服务器文档](mcp_server/README.md)**: SSE 流式 MCP 服务器使用指南

---

<div align="center">

**🎉 开始你的 Logstash 规则测试之旅！**

如果这个项目对你有帮助，请考虑给它一个 ⭐️

[报告问题](https://github.com/username/logstash-lab/issues) • [功能建议](https://github.com/username/logstash-lab/issues) • [加入讨论](https://github.com/username/logstash-lab/discussions)

</div>