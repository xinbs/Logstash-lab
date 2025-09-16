#!/usr/bin/env python3
"""
Logstash 测试服务 SSE 版本 MCP 服务器
提供 Server-Sent Events 流式响应，支持实时进度反馈
"""

import asyncio
import json
import tempfile
import os
import traceback
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Generator
from flask import Flask, request, jsonify, Response, stream_template
from flask_cors import CORS
import requests
import threading

# Logstash 测试服务配置
LOGSTASH_SERVICE_URL = os.getenv("LOGSTASH_SERVICE_URL", "http://web:19000")

app = Flask(__name__)
CORS(app)  # 启用跨域支持

class LogstashMCPServer:
    """Logstash 测试服务 SSE 版本 MCP 服务器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        # 服务器启动时间
        self.start_time = datetime.now()
        # 活跃的 SSE 连接
        self.active_connections = {}
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """统一的请求处理方法"""
        url = f"{LOGSTASH_SERVICE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, files=files, timeout=timeout)
                else:
                    response = self.session.post(url, data=data, timeout=timeout)
            else:
                return {"success": False, "error": f"不支持的 HTTP 方法: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接到 Logstash 测试服务"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": f"请求超时 ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": f"请求异常: {str(e)}"}
    
    def _send_sse_event(self, connection_id: str, event_type: str, data: Dict[str, Any]):
        """发送 SSE 事件"""
        if connection_id in self.active_connections:
            event_data = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            try:
                # 这里实际的 SSE 发送会在路由中处理
                # 这个方法主要用于数据准备
                return event_data
            except Exception as e:
                print(f"SSE 发送失败: {e}")
        return None
    
    def upload_pipeline(self, pipeline_content: str, use_file_upload: bool = True) -> Dict[str, Any]:
        """上传 Pipeline 配置"""
        if use_file_upload:
            # 文件上传方式（推荐）
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(pipeline_content)
                temp_file = f.name
            
            try:
                with open(temp_file, 'rb') as f:
                    files = {'file': ('pipeline.conf', f, 'text/plain')}
                    result = self._make_request("POST", "/upload_pipeline", files=files)
            finally:
                os.unlink(temp_file)
        else:
            # 文本内容上传
            data = {"pipeline": pipeline_content}
            result = self._make_request("POST", "/upload_pipeline", data=data)
        
        return {
            "success": result.get("ok", False),
            "message": result.get("message", ""),
            "extracted_filters": result.get("extracted_filters", 0),
            "preview": result.get("applied_filter_preview", "")[:200] + "..." if result.get("applied_filter_preview") else "",
            "raw_response": result
        }
    
    def send_test_log(self, log_content: str, is_json: bool = False) -> Dict[str, Any]:
        """发送测试日志"""
        data = {"logs": log_content}
        if is_json:
            data["is_json"] = "1"
        
        result = self._make_request("POST", "/test", data=data)
        events = result.get("events", [])
        
        return {
            "success": result.get("ok", False),
            "message": result.get("message", ""),
            "events_count": len(events),
            "events": events,
            "latest_event": events[-1] if events else None,
            "raw_response": result
        }
    
    def get_parsed_results(self, count: int = -1) -> Dict[str, Any]:
        """获取解析结果"""
        result = self._make_request("GET", "/get_parsed_results")
        events = result.get("events", [])
        
        if count > 0:
            events = events[-count:]
        
        return {
            "success": result.get("ok", False),
            "total_count": result.get("count", 0),
            "returned_count": len(events),
            "events": events,
            "latest_event": events[-1] if events else None,
            "raw_response": result
        }
    
    def clear_results(self) -> Dict[str, Any]:
        """清空解析结果"""
        result = self._make_request("POST", "/clear_results")
        
        return {
            "success": result.get("ok", False),
            "message": result.get("message", ""),
            "raw_response": result
        }
    
    def get_logstash_logs(self, filter_errors: bool = False) -> Dict[str, Any]:
        """获取 Logstash 日志"""
        result = self._make_request("GET", "/logstash_logs")
        logs = result.get("logs", "")
        
        if filter_errors:
            log_lines = logs.split('\n')
            error_lines = [line for line in log_lines if 'ERROR' in line.upper()]
            filtered_logs = '\n'.join(error_lines)
            
            return {
                "success": result.get("ok", False),
                "total_lines": len(log_lines),
                "error_lines": len(error_lines),
                "logs": filtered_logs,
                "raw_response": result
            }
        
        return {
            "success": result.get("ok", False),
            "logs": logs,
            "raw_response": result
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        result = self._make_request("GET", "/get_parsed_results", timeout=5)
        healthy = result.get("ok", False) and not result.get("error")
        
        return {
            "healthy": healthy,
            "logstash_service_url": LOGSTASH_SERVICE_URL,
            "server_start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "details": result
        }
    
    def test_pipeline_complete_stream(self, pipeline_content: str, test_logs: List[str], 
                                    is_json: bool = False, wait_time: int = 3) -> Generator[str, None, None]:
        """完整的 Pipeline 测试流程 - SSE 流式版本"""
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = True
        
        def send_event(event_type: str, data: Dict[str, Any]):
            event_json = json.dumps({
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, ensure_ascii=False)
            return f"data: {event_json}\n\n"
        
        try:
            yield send_event("start", {
                "message": "开始 Pipeline 测试流程",
                "pipeline_preview": pipeline_content[:100] + "..." if len(pipeline_content) > 100 else pipeline_content,
                "test_logs_count": len(test_logs)
            })
            
            # 1. 健康检查
            yield send_event("progress", {"step": "health_check", "message": "正在检查服务健康状态..."})
            health_result = self.health_check()
            if not health_result["healthy"]:
                yield send_event("error", {"step": "health_check", "message": "Logstash 测试服务不可用", "details": health_result})
                return
            yield send_event("success", {"step": "health_check", "message": "✅ 服务可用"})
            
            # 2. 清空历史结果
            yield send_event("progress", {"step": "clear_results", "message": "正在清空历史结果..."})
            clear_result = self.clear_results()
            yield send_event("success", {"step": "clear_results", "message": clear_result.get("message", "清空完成")})
            
            # 3. 上传 Pipeline
            yield send_event("progress", {"step": "upload_pipeline", "message": "正在上传 Pipeline 配置..."})
            upload_result = self.upload_pipeline(pipeline_content, use_file_upload=True)
            if not upload_result["success"]:
                yield send_event("error", {
                    "step": "upload_pipeline", 
                    "message": f"Pipeline 上传失败: {upload_result.get('message')}", 
                    "details": upload_result
                })
                return
            yield send_event("success", {
                "step": "upload_pipeline", 
                "message": upload_result.get("message"),
                "extracted_filters": upload_result.get("extracted_filters"),
                "preview": upload_result.get("preview")
            })
            
            # 4. 等待热重载
            yield send_event("progress", {"step": "wait_reload", "message": f"等待 {wait_time} 秒热重载..."})
            for i in range(wait_time):
                time.sleep(1)
                yield send_event("progress", {
                    "step": "wait_reload", 
                    "message": f"热重载中... {i+1}/{wait_time}s",
                    "progress": (i+1) / wait_time * 100
                })
            yield send_event("success", {"step": "wait_reload", "message": f"热重载完成"})
            
            # 5. 发送测试日志
            all_events = []
            for i, log in enumerate(test_logs):
                yield send_event("progress", {
                    "step": f"send_log_{i+1}", 
                    "message": f"正在发送第 {i+1}/{len(test_logs)} 条日志...",
                    "log_preview": log[:50] + "..." if len(log) > 50 else log
                })
                
                send_result = self.send_test_log(log, is_json)
                
                if send_result["success"]:
                    yield send_event("success", {
                        "step": f"send_log_{i+1}", 
                        "message": send_result.get("message"),
                        "events_count": send_result.get("events_count", 0),
                        "latest_event": send_result.get("latest_event")
                    })
                    all_events.extend(send_result.get("events", []))
                else:
                    yield send_event("error", {
                        "step": f"send_log_{i+1}", 
                        "message": f"日志 {i+1} 发送失败: {send_result.get('message')}", 
                        "details": send_result
                    })
            
            # 6. 获取最终解析结果
            yield send_event("progress", {"step": "get_results", "message": "正在获取最终解析结果..."})
            parsed_result = self.get_parsed_results()
            if parsed_result["success"]:
                yield send_event("success", {
                    "step": "get_results", 
                    "message": f"获取到 {len(parsed_result.get('events', []))} 条解析记录",
                    "total_count": parsed_result.get("total_count"),
                    "events": parsed_result.get("events", [])
                })
            else:
                yield send_event("error", {
                    "step": "get_results", 
                    "message": f"获取结果失败: {parsed_result.get('message')}", 
                    "details": parsed_result
                })
            
            # 7. 检查错误日志
            yield send_event("progress", {"step": "check_logs", "message": "正在检查 Logstash 错误日志..."})
            logs_result = self.get_logstash_logs(filter_errors=True)
            if logs_result["success"]:
                error_count = logs_result.get("error_lines", 0)
                if error_count > 0:
                    yield send_event("warning", {
                        "step": "check_logs", 
                        "message": f"发现 {error_count} 个 Logstash 错误",
                        "error_logs": logs_result.get("logs", "")
                    })
                else:
                    yield send_event("success", {"step": "check_logs", "message": "未发现错误"})
            
            # 8. 完成
            yield send_event("complete", {
                "message": "Pipeline 测试流程完成",
                "total_events": len(parsed_result.get("events", [])),
                "success": True
            })
            
        except Exception as e:
            yield send_event("error", {
                "step": "exception", 
                "message": f"执行异常: {str(e)}", 
                "traceback": traceback.format_exc()
            })
        finally:
            # 清理连接
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
    
    def get_test_guidance(self, user_request: str, pipeline_content: str = "", test_logs: List[str] = None) -> str:
        """智能测试指导 - 根据用户输入自动分析并提供测试建议和步骤顺序"""
        if test_logs is None:
            test_logs = []
        
        guidance = []
        guidance.append("🎯 **智能测试指导**\n")
        
        # 分析用户请求
        request_lower = user_request.lower()
        
        # 1. 场景识别
        guidance.append("## 📋 **测试场景分析**")
        
        if any(keyword in request_lower for keyword in ['新建', '创建', '开发', '从零', 'new']):
            scenario = "新建配置"
            guidance.append("✅ **场景**: 新建 Pipeline 配置开发")
        elif any(keyword in request_lower for keyword in ['调试', 'debug', '错误', '问题', '失败', '不工作']):
            scenario = "调试修复"
            guidance.append("✅ **场景**: 调试现有配置问题")
        elif any(keyword in request_lower for keyword in ['测试', 'test', '验证', '检查']):
            scenario = "测试验证"
            guidance.append("✅ **场景**: 测试验证配置功能")
        elif any(keyword in request_lower for keyword in ['优化', '性能', '改进', '提升']):
            scenario = "性能优化"
            guidance.append("✅ **场景**: 性能优化和改进")
        else:
            scenario = "通用测试"
            guidance.append("✅ **场景**: 通用测试流程")
        
        # 2. 推荐测试步骤
        guidance.append("\n## 🚀 **推荐测试步骤**")
        
        if scenario == "新建配置":
            steps = [
                "1. **健康检查** - 确保服务正常运行",
                "2. **上传配置** - 使用 `upload_pipeline` 上传您的新配置",
                "3. **发送样本日志** - 使用 `send_test_log` 发送测试数据",
                "4. **检查解析结果** - 使用 `get_parsed_results` 查看输出",
                "5. **调试错误日志** - 如有问题，使用 `get_logstash_logs` 查看错误",
                "6. **迭代优化** - 根据结果调整配置并重复测试"
            ]
        elif scenario == "调试修复":
            steps = [
                "1. **获取错误日志** - 使用 `get_logstash_logs` 查看具体错误信息",
                "2. **清空历史结果** - 使用 `clear_results` 清理旧数据",
                "3. **重新上传配置** - 使用 `upload_pipeline` 上传修复后的配置",
                "4. **重现问题** - 使用 `send_test_log` 发送导致问题的日志",
                "5. **分析结果** - 使用 `get_parsed_results` 检查是否修复",
                "6. **健康检查** - 确认服务状态正常"
            ]
        elif scenario == "测试验证":
            steps = [
                "1. **健康检查** - 使用 `health_check` 确认服务状态",
                "2. **批量测试** - 使用 `test_pipeline_complete_stream` 进行完整流程测试",
                "3. **验证边界情况** - 测试异常日志格式和特殊字符",
                "4. **性能验证** - 测试大量日志的处理能力",
                "5. **结果对比** - 对比期望输出和实际输出"
            ]
        else:
            steps = [
                "1. **健康检查** - 使用 `health_check` 确认服务状态",
                "2. **上传配置** - 使用 `upload_pipeline` 更新配置",
                "3. **发送测试日志** - 使用 `send_test_log` 测试解析",
                "4. **获取结果** - 使用 `get_parsed_results` 查看输出",
                "5. **检查日志** - 如有问题使用 `get_logstash_logs` 调试"
            ]
        
        for step in steps:
            guidance.append(f"   {step}")
        
        # 3. 重要提示
        guidance.append("\n## ⚡ **重要提示 - 自动化特性**")
        guidance.append("🔄 **条件判断自动替换**: 系统会自动处理 `if` 条件判断")
        guidance.append("• 无论您输入 `if \"xxx\" == [@metadata][type]` 中的任何值")
        guidance.append("• 系统都会自动替换为 `if \"test\" == [@metadata][type]`")
        guidance.append("• 同时自动设置 `[@metadata][type] = \"test\"`")
        guidance.append("• **您无需担心条件匹配问题，专注编写 filter 逻辑即可**")
        
        # 4. 具体建议
        guidance.append("\n## 💡 **具体建议**")
        
        if pipeline_content:
            guidance.append("**配置分析**:")
            if "grok" in pipeline_content.lower():
                guidance.append("• 检测到 Grok 模式，建议先测试简单日志验证正则表达式")
            if "ruby" in pipeline_content.lower():
                guidance.append("• 检测到 Ruby 代码，注意检查语法错误和性能影响")
            if "mutate" in pipeline_content.lower():
                guidance.append("• 检测到字段变换，验证字段类型转换是否正确")
            if "date" in pipeline_content.lower():
                guidance.append("• 检测到时间解析，确认时间格式匹配日志格式")
        
        if test_logs:
            guidance.append("**日志样本分析**:")
            guidance.append(f"• 提供了 {len(test_logs)} 条测试日志")
            if any("<" in log and ">" in log for log in test_logs):
                guidance.append("• 检测到 Syslog 格式，确保正确解析优先级字段")
            if any('"' in log for log in test_logs):
                guidance.append("• 检测到 JSON 或引号，注意转义字符处理")
        
        # 4. 自动化工作流建议
        guidance.append("\n## 🔄 **自动化工作流**")
        guidance.append("推荐使用 `test_pipeline_complete_stream` 进行一站式测试：")
        guidance.append("• 自动上传配置 → 发送测试日志 → 获取结果 → 检查错误")
        guidance.append("• 支持实时流式反馈，方便监控测试进度")
        guidance.append("• 适合批量测试多条日志记录")
        
        # 5. 常见问题解决
        guidance.append("\n## ⚠️ **常见问题解决**")
        common_issues = [
            "**Grok 解析失败**: 检查正则表达式语法，使用在线 Grok 调试器",
            "**字段类型错误**: 检查 mutate 插件的类型转换配置",
            "**时间解析失败**: 确认 date 插件的时间格式与日志一致",
            "**性能问题**: 检查 Ruby 代码复杂度，考虑使用原生插件替代",
            "**编码问题**: 注意中文等特殊字符的编码处理"
        ]
        for issue in common_issues:
            guidance.append(f"• {issue}")
        
        guidance.append("\n---")
        guidance.append("💬 **提示**: 您可以要求我按照上述步骤自动执行测试，我会使用相应的工具来完成！")
        
        return "\n".join(guidance)
    
    def _generate_prompt_content(self, prompt_name: str, prompt_args: Dict[str, Any]) -> str:
        """生成具体的提示内容"""
        
        if prompt_name == "test_existing_config":
            config_type = prompt_args.get("config_type", "pipeline")
            return f"""请帮我测试现有的 Logstash 配置文件。

📋 **测试任务**:
- 配置类型: {config_type}
- 验证配置语法是否正确
- 测试实际日志解析效果
- 检查字段提取和类型转换

🔧 **推荐测试流程**:
1. **上传配置**: 使用 `upload_pipeline` 工具上传您的配置文件
2. **清空现有解析记录**: 使用 `clear_results` 清理历史数据
3. **发送测试日志**: 使用 `send_test_log` 发送样本日志进行测试
4. **检查解析结果**: 使用 `get_parsed_results` 查看解析输出
5. **查看错误日志**: 如有问题使用 `get_logstash_logs` 查看详细错误
6. **健康检查**: 使用 `health_check` 确认服务状态

⚡ **重要提示**: 
- 系统会自动处理 `if "xxx" == [@metadata][type]` 条件替换
- 您无需担心条件匹配问题，专注测试解析逻辑
- 可以使用 `test_pipeline_complete_stream` 进行一站式流式测试

请提供您的配置文件，我会帮您完成测试。"""

        elif prompt_name == "test_log_matching":
            log_type = prompt_args.get("log_type", "custom")
            return f"""请帮我测试日志与配置的匹配效果。

📋 **匹配测试任务**:
- 日志类型: {log_type}
- 验证日志格式与配置的兼容性
- 检查字段提取完整性和准确性
- 测试边界情况和异常日志

🧪 **测试步骤**:
1. **准备测试数据**: 提供多条不同格式的样本日志
2. **清空现有解析记录**: 使用 `clear_results` 确保测试环境干净
3. **发送测试日志**: 使用 `send_test_log` 逐条测试
4. **分析解析结果**: 使用 `get_parsed_results` 检查每条日志的解析效果
5. **对比期望输出**: 验证提取的字段是否符合预期
6. **批量测试**: 使用 `test_pipeline_complete_stream` 批量测试多条日志

🎯 **关注重点**:
- 字段提取是否完整
- 数据类型转换是否正确
- 时间解析是否准确
- 异常日志的处理情况

⚡ **自动化特性**: 
- 条件判断自动替换，无需关心 `[@metadata][type]` 匹配
- 专注验证解析逻辑的正确性

请提供您的样本日志，我会帮您测试匹配效果。"""

        elif prompt_name == "debug_parsing_failure":
            error_type = prompt_args.get("error_type", "通用解析错误")
            return f"""帮我调试日志解析失败问题。

📋 **故障诊断**:
- 错误类型: {error_type}
- 分析解析失败的根本原因
- 提供具体的修复建议
- 验证修复效果

🔍 **诊断流程**:
1. **获取错误信息**: 使用 `get_logstash_logs` 查看详细错误日志
2. **清空历史数据**: 使用 `clear_results` 清理旧的测试结果
3. **重现问题**: 使用 `send_test_log` 发送失败的日志样本
4. **分析错误模式**: 检查 `get_parsed_results` 中的错误标记
5. **验证修复**: 修改配置后重新测试

🚨 **常见解析失败原因**:
- **Grok 模式不匹配**: 正则表达式与日志格式不符
- **字段名冲突**: 多个插件定义了相同字段
- **类型转换错误**: 数据类型转换失败
- **日期解析失败**: 时间格式不匹配
- **编码问题**: 特殊字符或编码导致解析异常

🔧 **调试技巧**:
- 使用简化的 Grok 模式逐步调试
- 检查转义字符的正确性
- 验证字段命名的一致性

请提供失败的日志样本和错误信息，我会帮您定位并解决问题。"""

        elif prompt_name == "compare_before_after":
            modification_type = prompt_args.get("modification_type", "配置优化")
            return f"""帮我比较配置修改前后的解析效果。

📋 **对比测试任务**:
- 修改类型: {modification_type}
- 验证修改是否达到预期效果
- 确保不引入新的解析问题
- 评估性能和准确性改进

🔄 **对比测试流程**:
1. **保存原始结果**: 
   - 使用当前配置测试样本日志
   - 保存 `get_parsed_results` 的输出作为基准
2. **应用新配置**:
   - 使用 `upload_pipeline` 上传修改后的配置
   - 使用相同日志进行测试
3. **结果对比**:
   - 对比修改前后的字段提取结果
   - 检查新增、删除或修改的字段
   - 验证数据准确性和完整性
4. **性能评估**:
   - 使用 `test_pipeline_complete_stream` 测试处理速度
   - 检查资源消耗情况

📊 **对比维度**:
- ✅ **字段完整性**: 必要字段是否都被正确提取
- ✅ **数据准确性**: 提取的值是否正确
- ✅ **类型转换**: 数据类型是否符合预期
- ✅ **性能表现**: 处理速度是否有改善
- ✅ **错误率**: 解析失败的日志是否减少

⚡ **自动化优势**: 
- 系统自动处理条件判断，确保测试一致性
- 可以快速切换和对比不同配置版本

请提供修改前后的配置和测试日志，我会帮您完成详细对比。"""

        elif prompt_name == "validate_field_extraction":
            expected_fields = prompt_args.get("expected_fields", "所有字段")
            return f"""帮我验证字段提取是否正确。

📋 **字段验证任务**:
- 期望字段: {expected_fields}
- 验证字段提取的完整性和准确性
- 检查数据类型转换是否正确
- 确认字段映射关系

✅ **验证检查项**:
1. **字段存在性**: 所有期望的字段都被提取
2. **字段值准确性**: 提取的值与日志内容匹配
3. **数据类型正确性**: 数值、日期、字符串类型转换正确
4. **字段命名规范**: 字段名符合预期的命名约定
5. **特殊字段处理**: 时间戳、IP地址等特殊字段格式正确

🧪 **验证流程**:
1. **清空现有解析记录**: 使用 `clear_results` 确保测试环境干净
2. **发送测试日志**: 使用 `send_test_log` 发送包含所有字段的日志样本
3. **获取解析结果**: 使用 `get_parsed_results` 查看提取的字段
4. **逐字段检查**: 验证每个字段的存在性和值的正确性
5. **类型验证**: 检查数值字段是否为数字类型，日期是否正确解析
6. **边界测试**: 测试缺失字段、空值、特殊字符的处理

📝 **验证报告**:
- ✅ 正确提取的字段列表
- ❌ 缺失或错误的字段
- 🔄 需要修改的配置建议
- 📊 字段提取完整性评分

⚡ **系统特性**: 
- 自动条件判断替换，确保测试环境一致
- 可以重复测试和验证不同的日志样本

请提供您的期望字段列表和测试日志，我会帮您完成详细验证。"""

        elif prompt_name == "batch_test_logs":
            test_scenario = prompt_args.get("test_scenario", "综合测试")
            return f"""帮我批量测试多条日志记录。

📋 **批量测试任务**:
- 测试场景: {test_scenario}
- 验证配置对不同日志的处理能力
- 识别潜在的解析问题和边界情况
- 评估整体解析成功率

🎯 **测试场景类型**:
- **正常日志**: 标准格式的常见日志
- **异常日志**: 格式不完整或包含特殊字符的日志
- **边界情况**: 极长字段、空值、特殊编码等
- **混合格式**: 不同来源或时间段的日志混合

🚀 **批量测试流程**:
1. **准备测试数据集**: 收集不同类型的日志样本
2. **执行批量测试**: 使用 `test_pipeline_complete_stream` 工具
   - 支持实时流式反馈
   - 自动处理多条日志
   - 提供详细的进度报告
3. **结果分析**: 
   - 统计解析成功率
   - 识别解析失败的日志模式
   - 分析字段提取的一致性
4. **问题诊断**: 对失败的日志使用 `get_logstash_logs` 查看错误

📊 **测试指标**:
- 📈 **解析成功率**: 成功解析的日志百分比
- 🎯 **字段完整性**: 关键字段的提取率
- ⚡ **处理性能**: 每秒处理的日志数量
- 🚨 **错误类型分布**: 不同错误的频率统计

✨ **批量测试优势**:
- 流式处理，实时查看测试进度
- 自动汇总统计结果
- 识别配置的鲁棒性问题
- 系统自动处理条件判断替换

请提供您的日志数据集，我会帮您执行全面的批量测试。"""

        else:
            return f"""未知的提示类型: {prompt_name}

🔧 **可用的测试提示**:
- **test_existing_config**: 测试现有的 Logstash 配置文件
- **test_log_matching**: 测试日志与配置的匹配效果  
- **debug_parsing_failure**: 调试日志解析失败问题
- **compare_before_after**: 比较配置修改前后的解析效果
- **validate_field_extraction**: 验证字段提取是否正确
- **batch_test_logs**: 批量测试多条日志记录

💡 **使用建议**:
这些提示专门针对实际测试场景设计，帮助您：
- 快速测试现有配置
- 验证日志解析效果
- 调试解析问题
- 批量测试和性能评估

请选择适合您当前需求的提示类型。"""

# 创建全局服务实例
mcp_server = LogstashMCPServer()

# HTTP API 路由定义
@app.route("/", methods=["GET"])
def index():
    """服务器首页"""
    return jsonify({
        "service": "Logstash SSE MCP Server",
        "version": "1.0.0",
        "description": "为 AI 提供 Logstash 测试工具的 SSE 流式调用接口",
        "start_time": mcp_server.start_time.isoformat(),
        "features": [
            "Server-Sent Events (SSE) 支持",
            "实时进度反馈",
            "流式测试结果",
            "所有标准 MCP 工具"
        ],
        "available_tools": [
            "upload_pipeline",
            "test_pipeline_complete_stream", 
            "send_test_log",
            "get_parsed_results",
            "clear_results",
            "get_logstash_logs",
            "health_check"
        ],
        "docs": "/docs"
    })

@app.route("/docs", methods=["GET"])
def docs():
    """API 文档"""
    return jsonify({
        "api_documentation": {
            "sse_endpoints": {
                "test_pipeline_complete_stream": {
                    "method": "GET",
                    "endpoint": "/sse/test_pipeline_complete",
                    "description": "SSE 流式完整测试流程",
                    "parameters": {
                        "pipeline_content": "string (required) - Pipeline 配置内容",
                        "test_logs": "array (required) - 测试日志列表（JSON 编码）",
                        "is_json": "boolean (optional) - 是否为 JSON 格式，默认 false",
                        "wait_time": "integer (optional) - 等待热重载时间，默认 3 秒"
                    },
                    "response_format": "text/event-stream",
                    "event_types": [
                        "start - 开始流程",
                        "progress - 进度更新", 
                        "success - 步骤成功",
                        "error - 错误信息",
                        "warning - 警告信息",
                        "complete - 流程完成"
                    ]
                }
            },
            "standard_endpoints": {
                "upload_pipeline": {
                    "method": "POST",
                    "endpoint": "/tools/upload_pipeline",
                    "description": "上传完整的 Logstash pipeline 配置"
                },
                "send_test_log": {
                    "method": "POST",
                    "endpoint": "/tools/send_test_log", 
                    "description": "发送测试日志"
                },
                "get_parsed_results": {
                    "method": "GET",
                    "endpoint": "/tools/get_parsed_results",
                    "description": "获取解析结果"
                },
                "clear_results": {
                    "method": "POST",
                    "endpoint": "/tools/clear_results",
                    "description": "清空解析结果"
                },
                "get_logstash_logs": {
                    "method": "GET", 
                    "endpoint": "/tools/get_logstash_logs",
                    "description": "获取 Logstash 日志"
                },
                "health_check": {
                    "method": "GET",
                    "endpoint": "/tools/health_check",
                    "description": "健康检查"
                }
            }
        }
    })

# SSE 流式接口
@app.route("/sse/test_pipeline_complete", methods=["GET"])
def sse_test_pipeline_complete():
    """SSE 流式完整测试流程"""
    try:
        pipeline_content = request.args.get("pipeline_content", "")
        test_logs_json = request.args.get("test_logs", "[]")
        is_json = request.args.get("is_json", "false").lower() == "true"
        wait_time = int(request.args.get("wait_time", "3"))
        
        if not pipeline_content:
            return jsonify({"error": "缺少 pipeline_content 参数"}), 400
        
        try:
            test_logs = json.loads(test_logs_json)
        except json.JSONDecodeError:
            return jsonify({"error": "test_logs 参数必须是有效的 JSON 数组"}), 400
        
        if not test_logs:
            return jsonify({"error": "test_logs 不能为空"}), 400
        
        def generate():
            yield from mcp_server.test_pipeline_complete_stream(
                pipeline_content, test_logs, is_json, wait_time
            )
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
    
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

# MCP 协议支持
@app.route("/mcp", methods=["POST"])
def mcp_handler():
    """处理 MCP (Model Context Protocol) 请求"""
    try:
        if not request.is_json:
            return jsonify({"error": "MCP 请求必须是 JSON 格式"}), 400
        
        data = request.get_json()
        
        # 检查 JSON-RPC 格式
        if not isinstance(data, dict) or "method" not in data:
            return jsonify({"error": "无效的 JSON-RPC 请求"}), 400
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        # 处理不同的 MCP 方法
        if method == "initialize":
            # MCP 标准初始化协议
            client_info = params.get("clientInfo", {})
            protocol_version = params.get("protocolVersion", "2024-11-05")
            capabilities = params.get("capabilities", {})
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        },
                        "logging": {},
                        "prompts": {
                            "listChanged": True
                        },
                        "resources": {},
                        "sampling": {}
                    },
                    "serverInfo": {
                        "name": "Logstash MCP Server",
                        "version": "1.0.0",
                        "description": "Logstash 规则测试和调试工具 MCP 服务器"
                    }
                }
            })
        
        elif method == "notifications/initialized":
            # MCP 初始化完成通知 - 返回空的成功响应
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        
        elif method == "list_prompts" or method == "prompts/list":
            # 返回可用提示列表
            prompts = [
                {
                    "name": "test_existing_config",
                    "description": "测试现有的 Logstash 配置文件",
                    "arguments": [
                        {
                            "name": "config_type",
                            "description": "配置类型 (filter/pipeline/完整配置)",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "test_log_matching",
                    "description": "测试日志与配置的匹配效果",
                    "arguments": [
                        {
                            "name": "log_type",
                            "description": "日志类型 (nginx/apache/syslog/json/custom)",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "debug_parsing_failure",
                    "description": "调试日志解析失败问题",
                    "arguments": [
                        {
                            "name": "error_type",
                            "description": "错误类型 (grok_failure/json_parse_error/date_parse_error)",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "compare_before_after",
                    "description": "比较配置修改前后的解析效果",
                    "arguments": [
                        {
                            "name": "modification_type",
                            "description": "修改类型 (grok_pattern/field_mapping/date_format)",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "validate_field_extraction",
                    "description": "验证字段提取是否正确",
                    "arguments": [
                        {
                            "name": "expected_fields",
                            "description": "期望提取的字段列表",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "batch_test_logs",
                    "description": "批量测试多条日志记录",
                    "arguments": [
                        {
                            "name": "test_scenario",
                            "description": "测试场景 (正常日志/异常日志/边界情况)",
                            "required": False
                        }
                    ]
                }
            ]
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": prompts
                }
            })
        
        elif method == "get_prompt" or method == "prompts/get":
            prompt_name = params.get("name")
            prompt_args = params.get("arguments", {})
            
            # 生成具体的提示内容
            prompt_content = mcp_server._generate_prompt_content(prompt_name, prompt_args)
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "description": f"Logstash 配置提示: {prompt_name}",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": prompt_content
                            }
                        }
                    ]
                }
            })
        
        elif method == "list_tools" or method == "tools/list":
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "upload_pipeline",
                            "description": "上传完整的 Logstash Pipeline 配置文件，自动提取 filter 块并应用到测试环境。重要：系统会自动将任何 if \"xxx\" == [@metadata][type] 条件替换为 if \"test\" == [@metadata][type]，您无需担心条件匹配问题",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "pipeline_content": {
                                        "type": "string",
                                        "description": "完整的 Pipeline 配置内容"
                                    },
                                    "use_file_upload": {
                                        "type": "boolean",
                                        "description": "是否为文件上传方式",
                                        "default": True
                                    }
                                },
                                "required": ["pipeline_content"]
                            }
                        },
                        {
                            "name": "send_test_log",
                            "description": "发送测试日志到 Logstash 进行解析",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "log_content": {
                                        "type": "string",
                                        "description": "要测试的日志内容"
                                    },
                                    "is_json": {
                                        "type": "boolean",
                                        "description": "日志是否为 JSON 格式",
                                        "default": False
                                    }
                                },
                                "required": ["log_content"]
                            }
                        },
                        {
                            "name": "get_parsed_results",
                            "description": "获取最新的解析结果",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False
                            }
                        },
                        {
                            "name": "clear_results",
                            "description": "清空历史解析结果",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False
                            }
                        },
                        {
                            "name": "get_logstash_logs",
                            "description": "获取 Logstash 运行日志",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False
                            }
                        },
                        {
                            "name": "test_pipeline_complete_stream",
                            "description": "执行完整的 Pipeline 测试流程，包括上传配置、发送测试日志、获取结果。支持 SSE 流式反馈",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "pipeline_content": {
                                        "type": "string",
                                        "description": "Pipeline 配置内容"
                                    },
                                    "test_logs": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "description": "测试日志列表"
                                    },
                                    "is_json": {
                                        "type": "boolean",
                                        "description": "日志是否为 JSON 格式",
                                        "default": False
                                    },
                                    "wait_time": {
                                        "type": "integer",
                                        "description": "等待热重载时间（秒）",
                                        "default": 3
                                    }
                                },
                                "required": ["pipeline_content", "test_logs"]
                            }
                        },
                        {
                            "name": "get_test_guidance",
                            "description": "获取智能测试指导，根据用户输入自动分析并提供测试建议和步骤顺序",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "user_request": {
                                        "type": "string",
                                        "description": "用户的测试请求或问题描述"
                                    },
                                    "pipeline_content": {
                                        "type": "string",
                                        "description": "可选：Pipeline 配置内容，用于分析和建议"
                                    },
                                    "test_logs": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "可选：测试日志样本，用于分析格式和内容"
                                    }
                                },
                                "required": ["user_request"]
                            }
                        },
                        {
                            "name": "health_check",
                            "description": "检查服务健康状态",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False
                            }
                        }
                    ]
                }
            })
        
        elif method == "call_tool" or method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "upload_pipeline":
                result = mcp_server.upload_pipeline(
                    tool_args.get("pipeline_content", ""),
                    tool_args.get("use_file_upload", True)
                )
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Pipeline 上传结果：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                            }
                        ],
                        "isError": not result.get("success", False)
                    }
                })
            
            elif tool_name == "send_test_log":
                result = mcp_server.send_test_log(
                    tool_args.get("log_content", ""),
                    tool_args.get("is_json", False)
                )
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"测试日志发送结果：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                            }
                        ],
                        "isError": not result.get("success", False)
                    }
                })
            
            elif tool_name == "get_parsed_results":
                result = mcp_server.get_parsed_results()
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"解析结果：\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                            }
                        ]
                    }
                })
            
            elif tool_name == "clear_results":
                result = mcp_server.clear_results()
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"清空结果：{result.get('message', '操作完成')}"
                            }
                        ]
                    }
                })
            
            elif tool_name == "get_logstash_logs":
                result = mcp_server.get_logstash_logs()
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Logstash 日志：\n{result.get('logs', '无日志')[-2000:]}"  # 限制长度
                            }
                        ]
                    }
                })
            
            elif tool_name == "test_pipeline_complete_stream":
                # 对于流式工具，返回 SSE 端点信息
                pipeline_content = tool_args.get("pipeline_content", "")
                test_logs = tool_args.get("test_logs", [])
                is_json = tool_args.get("is_json", False)
                wait_time = tool_args.get("wait_time", 3)
                
                # 构建 SSE URL
                sse_url = f"{request.url_root}sse/test_pipeline_complete"
                params_dict = {
                    "pipeline_content": pipeline_content,
                    "test_logs": json.dumps(test_logs),
                    "is_json": str(is_json).lower(),
                    "wait_time": str(wait_time)
                }
                
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"SSE 流式测试已启动。\n\n请使用以下信息连接 SSE 流：\n\nURL: {sse_url}\n参数: {json.dumps(params_dict, ensure_ascii=False, indent=2)}\n\n或直接访问测试页面: {request.url_root}test"
                            }
                        ]
                    }
                })
            
            elif tool_name == "get_test_guidance":
                guidance = mcp_server.get_test_guidance(
                    tool_args.get("user_request", ""),
                    tool_args.get("pipeline_content", ""),
                    tool_args.get("test_logs", [])
                )
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": guidance
                            }
                        ]
                    }
                })
            
            elif tool_name == "health_check":
                result = mcp_server.health_check()
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"健康检查结果：\n状态: {'健康' if result.get('healthy') else '异常'}\n详情: {json.dumps(result.get('details', {}), ensure_ascii=False, indent=2)}"
                            }
                        ]
                    }
                })
            
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知的工具: {tool_name}"
                    }
                }), 400
        
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"未知的方法: {method}"
                }
            }), 400
    
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get("id") if isinstance(data, dict) else None,
            "error": {
                "code": -32603,
                "message": f"内部错误: {str(e)}",
                "data": traceback.format_exc()
            }
        }), 500

# 标准 REST API 接口（与 network_mcp_server.py 兼容）
@app.route("/tools/upload_pipeline", methods=["POST"])
def api_upload_pipeline():
    """上传 Pipeline 配置"""
    try:
        pipeline_content = ""
        use_file_upload = True
        
        # 检查是否是文件上传
        if 'file' in request.files:
            # 文件上传方式
            file = request.files['file']
            if file.filename:
                pipeline_content = file.read().decode('utf-8')
                use_file_upload = True
        elif 'pipeline' in request.form:
            # 表单数据方式
            pipeline_content = request.form.get('pipeline', '')
            use_file_upload = False
        elif request.is_json:
            # JSON 数据方式
            data = request.get_json()
            pipeline_content = data.get("pipeline_content", "")
            use_file_upload = data.get("use_file_upload", True)
        else:
            return jsonify({"success": False, "error": "未提供 pipeline 内容"}), 400
        
        if not pipeline_content:
            return jsonify({"success": False, "error": "缺少 pipeline_content 参数"}), 400
        
        result = mcp_server.upload_pipeline(pipeline_content, use_file_upload)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/tools/send_test_log", methods=["POST"])
def api_send_test_log():
    """发送测试日志"""
    try:
        data = request.get_json()
        log_content = data.get("log_content", "")
        is_json = data.get("is_json", False)
        
        if not log_content:
            return jsonify({"success": False, "error": "缺少 log_content 参数"}), 400
        
        result = mcp_server.send_test_log(log_content, is_json)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/tools/get_parsed_results", methods=["GET"])
def api_get_parsed_results():
    """获取解析结果"""
    try:
        count = request.args.get("count", -1, type=int)
        result = mcp_server.get_parsed_results(count)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/tools/clear_results", methods=["POST"])
def api_clear_results():
    """清空解析结果"""
    try:
        result = mcp_server.clear_results()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/tools/get_logstash_logs", methods=["GET"])
def api_get_logstash_logs():
    """获取 Logstash 日志"""
    try:
        filter_errors = request.args.get("filter_errors", "false").lower() == "true"
        result = mcp_server.get_logstash_logs(filter_errors)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/tools/health_check", methods=["GET"])
def api_health_check():
    """健康检查"""
    try:
        result = mcp_server.health_check()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500

# SSE 测试页面
@app.route("/test", methods=["GET"])
def test_page():
    """SSE 测试页面"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>SSE MCP Server 测试</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; }
        textarea { width: 100%; height: 200px; font-family: monospace; }
        button { padding: 10px 20px; margin: 5px; }
        .log { 
            background: #f5f5f5; 
            border: 1px solid #ddd; 
            padding: 10px; 
            height: 400px; 
            overflow-y: scroll; 
            font-family: monospace; 
            white-space: pre-wrap;
        }
        .event { margin: 5px 0; padding: 5px; border-left: 3px solid #ccc; }
        .start { border-left-color: #007bff; }
        .progress { border-left-color: #ffc107; }
        .success { border-left-color: #28a745; }
        .error { border-left-color: #dc3545; }
        .warning { border-left-color: #fd7e14; }
        .complete { border-left-color: #6f42c1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌊 SSE MCP Server 测试</h1>
        
        <h3>Pipeline 配置:</h3>
        <textarea id="pipelineContent">
input {
  http { port => 15515 }
}
filter {
  if "apache" == [@metadata][type] {
    grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
    mutate { rename => { "clientip" => "src_ip" } }
  }
}
output {
  file { path => "/data/out/events.ndjson" }
}
        </textarea>
        
        <h3>测试日志:</h3>
        <textarea id="testLogs">127.0.0.1 - - [25/Dec/2023:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326
192.168.1.100 - - [25/Dec/2023:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 128</textarea>
        
        <div>
            <button onclick="startSSETest()">🚀 开始 SSE 流式测试</button>
            <button onclick="clearLog()">🗑️ 清空日志</button>
        </div>
        
        <h3>实时日志:</h3>
        <div id="logOutput" class="log"></div>
    </div>
    
    <script>
        let eventSource = null;
        
        function startSSETest() {
            const pipelineContent = document.getElementById('pipelineContent').value;
            const testLogsText = document.getElementById('testLogs').value;
            const testLogs = testLogsText.split('\\n').filter(line => line.trim());
            
            if (!pipelineContent.trim() || testLogs.length === 0) {
                alert('请输入 Pipeline 配置和测试日志');
                return;
            }
            
            // 关闭之前的连接
            if (eventSource) {
                eventSource.close();
            }
            
            clearLog();
            addLog('🔌 正在连接 SSE 流...', 'progress');
            
            // 构建 URL
            const params = new URLSearchParams({
                pipeline_content: pipelineContent,
                test_logs: JSON.stringify(testLogs),
                is_json: 'false',
                wait_time: '3'
            });
            
            const url = `/sse/test_pipeline_complete?${params.toString()}`;
            
            // 创建 SSE 连接
            eventSource = new EventSource(url);
            
            eventSource.onopen = function(event) {
                addLog('✅ SSE 连接已建立', 'success');
            };
            
            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    const timestamp = new Date(data.timestamp).toLocaleTimeString();
                    const message = `[${timestamp}] ${data.type.toUpperCase()}: ${data.data.message || JSON.stringify(data.data)}`;
                    addLog(message, data.type);
                    
                    if (data.type === 'complete' || data.type === 'error') {
                        addLog('🏁 流程结束，连接将关闭', 'complete');
                        eventSource.close();
                        eventSource = null;
                    }
                } catch (e) {
                    addLog(`解析事件失败: ${event.data}`, 'error');
                }
            };
            
            eventSource.onerror = function(event) {
                addLog('❌ SSE 连接错误', 'error');
                eventSource.close();
                eventSource = null;
            };
        }
        
        function addLog(message, type = 'info') {
            const logOutput = document.getElementById('logOutput');
            const eventDiv = document.createElement('div');
            eventDiv.className = `event ${type}`;
            eventDiv.textContent = message;
            logOutput.appendChild(eventDiv);
            logOutput.scrollTop = logOutput.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('logOutput').innerHTML = '';
        }
        
        // 页面关闭时清理连接
        window.addEventListener('beforeunload', function() {
            if (eventSource) {
                eventSource.close();
            }
        });
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    print("🌊 启动 Logstash MCP Server (SSE 支持)...")
    print(f"📡 服务地址: http://0.0.0.0:19001")
    print(f"📚 API 文档: http://0.0.0.0:19001/docs")
    print(f"🧪 测试页面: http://0.0.0.0:19001/test")
    print(f"🌊 SSE 接口: http://0.0.0.0:19001/sse/test_pipeline_complete")
    print(f"🔗 Logstash 服务: {LOGSTASH_SERVICE_URL}")
    
    # 检查是否在开发模式
    is_development = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=19001, debug=is_development, use_reloader=is_development)
