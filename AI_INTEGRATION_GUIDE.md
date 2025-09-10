# 🤖 AI 集成调用指南

**面向第三方 AI 的 Logstash 规则测试服务调用文档**

本文档专门为第三方 AI 系统提供完整的调用指南，实现自动化的 Logstash 规则测试和验证。

---

## 📋 服务概述

### 🎯 **服务功能**
- **Logstash Filter 规则编辑和验证**
- **实时日志解析测试**
- **解析结果获取和分析**
- **调试日志查看**
- **自动化测试工作流**

### 🌐 **服务地址**
```
Base URL: http://localhost:19000
Health Check: GET /get_parsed_results
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

```bash
#!/bin/bash
# AI 自动化测试工作流

BASE_URL="http://localhost:19000"

# 1. 清空历史数据
curl -s -X POST "$BASE_URL/clear_results"

# 2. 保存 Filter 规则
curl -s -X POST "$BASE_URL/save_filter" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "filter=grok { match => { \"message\" => \"%{COMBINEDAPACHELOG}\" } }"

# 3. 等待热重载
sleep 3

# 4. 发送测试日志
curl -s -X POST "$BASE_URL/test" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "logs=127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] \"GET /index.html HTTP/1.1\" 200 2326"

# 5. 获取解析结果
curl -s "$BASE_URL/get_parsed_results" | jq .
```

---

## 🔧 API 接口详细说明

### 🛠️ **1. 保存 Filter 规则**

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

### 📊 **2. 发送测试日志**

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

### 📈 **3. 获取解析结果**

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

### 📋 **4. 获取 Logstash 日志**

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

### 🗑️ **5. 清空解析结果**

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
    
    def save_filter(self, filter_content: str) -> Dict:
        """保存 Filter 规则"""
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
    """AI 调用示例"""
    service = LogstashTestService()
    
    # 测试 Apache 日志解析
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
    
    # 执行测试
    result = service.test_filter_with_logs(apache_filter, apache_logs)
    
    if result["success"]:
        print("✅ 测试成功!")
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
        print("❌ 测试失败!")
        for error in result["errors"]:
            print(f"  错误: {error}")

if __name__ == "__main__":
    ai_test_example()
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
    
    # 测试数据
    test_cases = [
        {
            "name": "Apache 访问日志",
            "filter": 'grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }',
            "logs": [
                '127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326',
                '192.168.1.100 - user [25/Dec/2023:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 128'
            ],
            "is_json": False
        },
        {
            "name": "JSON 应用日志",
            "filter": 'json { source => "message" } if [level] { mutate { uppercase => ["level"] } }',
            "logs": [
                '{"timestamp": "2023-12-25T10:00:00Z", "level": "info", "message": "用户登录成功", "user_id": 12345}',
                '{"timestamp": "2023-12-25T10:00:01Z", "level": "error", "message": "数据库连接失败", "error_code": 500}'
            ],
            "is_json": True
        }
    ]
    
    # 执行测试
    all_results = []
    
    for test_case in test_cases:
        print(f"\n🧪 测试: {test_case['name']}")
        print(f"Filter: {test_case['filter'][:50]}...")
        
        result = service.test_filter_with_logs(
            test_case['filter'],
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
