#!/usr/bin/env python3
"""
Pipeline 配置验证工具模块
使用 Docker 容器运行 Logstash 配置验证
"""

import tempfile
import subprocess
import os
import re
import json
from typing import Dict, List, Any, Optional

class PipelineValidator:
    """Pipeline 配置验证器"""
    
    def __init__(self, logstash_image: str = "docker.elastic.co/logstash/logstash:8.14.2"):
        self.logstash_image = logstash_image
    
    def validate_pipeline(self, pipeline_content: str) -> Dict[str, Any]:
        """
        验证 Pipeline 配置
        
        Args:
            pipeline_content: Pipeline 配置内容
            
        Returns:
            验证结果字典，包含 success, errors, warnings 等信息
        """
        try:
            # 尝试多种验证方式
            # 1. 首先尝试通过 stdin 传递配置内容
            try:
                result = self._run_logstash_validation_with_stdin(pipeline_content)
                return result
            except Exception as stdin_error:
                # 2. 如果 stdin 方式失败，尝试创建临时文件
                try:
                    result = self._run_logstash_validation_with_tempfile(pipeline_content)
                    return result
                except Exception as tempfile_error:
                    # 3. 如果都失败了，返回详细的错误信息
                    return {
                        "success": False,
                        "errors": [
                            {
                                "message": f"验证失败 - stdin方式: {str(stdin_error)}; 临时文件方式: {str(tempfile_error)}", 
                                "line": None, 
                                "column": None
                            }
                        ],
                        "warnings": [],
                        "raw_output": "",
                        "validation_time": 0
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": f"验证过程出错: {str(e)}", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": 0
            }
    
    def _run_logstash_validation(self, config_path: str) -> Dict[str, Any]:
        """
        运行 Logstash Docker 容器进行配置验证
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            验证结果
        """
        import time
        start_time = time.time()
        
        try:
            # Docker 命令
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{config_path}:/tmp/test.conf:ro",
                self.logstash_image,
                "logstash", "--config.test_and_exit", "--path.config", "/tmp/test.conf"
            ]
            
            # 运行 Docker 容器
            process = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            validation_time = time.time() - start_time
            raw_output = process.stdout + process.stderr
            
            # 解析输出
            if process.returncode == 0:
                # 配置验证成功
                return {
                    "success": True,
                    "errors": [],
                    "warnings": self._extract_warnings(raw_output),
                    "raw_output": raw_output,
                    "validation_time": validation_time
                }
            else:
                # 配置验证失败
                errors = self._extract_errors(raw_output)
                warnings = self._extract_warnings(raw_output)
                
                return {
                    "success": False,
                    "errors": errors,
                    "warnings": warnings,
                    "raw_output": raw_output,
                    "validation_time": validation_time
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": [{"message": "验证超时（30秒）", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": 30
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": f"Docker 执行失败: {str(e)}", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": time.time() - start_time
            }
    
    def _run_logstash_validation_with_stdin(self, pipeline_content: str) -> Dict[str, Any]:
        """
        运行 Logstash Docker 容器进行配置验证，通过 stdin 传递配置内容
        
        Args:
            pipeline_content: Pipeline 配置内容
            
        Returns:
            验证结果
        """
        import time
        start_time = time.time()
        
        try:
            # Docker 命令 - 使用 bash 来创建临时文件并运行 logstash
            docker_cmd = [
                "docker", "run", "--rm", "-i",
                self.logstash_image,
                "bash", "-c", 
                "cat > /tmp/test.conf && logstash --config.test_and_exit --path.config /tmp/test.conf"
            ]
            
            # 运行 Docker 容器
            process = subprocess.run(
                docker_cmd,
                input=pipeline_content,
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            validation_time = time.time() - start_time
            raw_output = process.stdout + process.stderr
            
            # 解析输出
            if process.returncode == 0:
                # 配置验证成功
                return {
                    "success": True,
                    "errors": [],
                    "warnings": self._extract_warnings(raw_output),
                    "raw_output": raw_output,
                    "validation_time": validation_time
                }
            else:
                # 配置验证失败
                errors = self._extract_errors(raw_output)
                warnings = self._extract_warnings(raw_output)
                
                return {
                    "success": False,
                    "errors": errors,
                    "warnings": warnings,
                    "raw_output": raw_output,
                    "validation_time": validation_time
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": [{"message": "验证超时（30秒）", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": 30
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": f"Docker 执行失败: {str(e)}", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": time.time() - start_time
            }
    
    def _run_logstash_validation_with_tempfile(self, pipeline_content: str) -> Dict[str, Any]:
        """
        使用临时文件方式运行 Logstash 验证，参考 web 服务的 docker logs 实现
        
        Args:
            pipeline_content: Pipeline 配置内容
            
        Returns:
            验证结果
        """
        import time
        import tempfile
        import os
        start_time = time.time()
        
        try:
            # 创建临时配置文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp_file:
                temp_file.write(pipeline_content)
                temp_config_path = temp_file.name
            
            try:
                # 使用 subprocess 运行 docker 命令，类似于 web 服务中的 docker logs 实现
                import subprocess
                
                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{temp_config_path}:/tmp/test.conf:ro",
                    self.logstash_image,
                    "logstash", "--config.test_and_exit", "--path.config", "/tmp/test.conf"
                ]
                
                # 运行 Docker 容器，参考 web 服务的实现
                process = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30秒超时
                )
                
                validation_time = time.time() - start_time
                raw_output = process.stdout + process.stderr
                
                # 解析输出
                if process.returncode == 0:
                    # 配置验证成功
                    return {
                        "success": True,
                        "errors": [],
                        "warnings": self._extract_warnings(raw_output),
                        "raw_output": raw_output,
                        "validation_time": validation_time
                    }
                else:
                    # 配置验证失败
                    errors = self._extract_errors(raw_output)
                    warnings = self._extract_warnings(raw_output)
                    
                    return {
                        "success": False,
                        "errors": errors,
                        "warnings": warnings,
                        "raw_output": raw_output,
                        "validation_time": validation_time
                    }
                    
            finally:
                # 清理临时文件
                if os.path.exists(temp_config_path):
                    os.unlink(temp_config_path)
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": [{"message": "验证超时（30秒）", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": 30
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": f"Docker 执行失败: {str(e)}", "line": None, "column": None}],
                "warnings": [],
                "raw_output": "",
                "validation_time": time.time() - start_time
            }
    
    def _extract_errors(self, output: str) -> List[Dict[str, Any]]:
        """
        从 Logstash 输出中提取错误信息
        
        Args:
            output: Logstash 输出
            
        Returns:
            错误信息列表
        """
        errors = []
        
        # 常见的错误模式
        error_patterns = [
            # 语法错误 - FATAL 级别
            r'\[FATAL\].*?Expected one of (.+?) at line (\d+), column (\d+)',
            # 语法错误 - 一般格式
            r'Expected one of (.+?) at line (\d+), column (\d+)',
            # 编译错误
            r'compile_imperative.*?line (\d+)',
            # 配置错误
            r'Configuration error.*?line (\d+)',
            # 插件错误
            r'Plugin not found.*?(\w+)',
            # FATAL 错误
            r'\[FATAL\].*?(.+)',
            # 一般错误
            r'\[ERROR\].*?(.+)',
        ]
        
        lines = output.split('\n')
        
        for line in lines:
            # 检查 FATAL 级别的语法错误
            fatal_syntax_match = re.search(r'\[FATAL\].*?Expected one of (.+?) at line (\d+), column (\d+)', line)
            if fatal_syntax_match:
                errors.append({
                    "message": f"语法错误: 期望 {fatal_syntax_match.group(1)}",
                    "line": int(fatal_syntax_match.group(2)),
                    "column": int(fatal_syntax_match.group(3)),
                    "type": "syntax_error"
                })
                continue
            
            # 检查一般语法错误
            syntax_match = re.search(r'Expected one of (.+?) at line (\d+), column (\d+)', line)
            if syntax_match:
                errors.append({
                    "message": f"语法错误: 期望 {syntax_match.group(1)}",
                    "line": int(syntax_match.group(2)),
                    "column": int(syntax_match.group(3)),
                    "type": "syntax_error"
                })
                continue
            
            # 检查编译错误
            compile_match = re.search(r'compile_imperative', line)
            if compile_match and 'ERROR' in line:
                # 尝试提取行号
                line_match = re.search(r'line (\d+)', line)
                line_num = int(line_match.group(1)) if line_match else None
                
                errors.append({
                    "message": "配置编译错误",
                    "line": line_num,
                    "column": None,
                    "type": "compile_error",
                    "details": line.strip()
                })
                continue
            
            # 检查 FATAL 错误
            if '[FATAL]' in line:
                # 清理错误消息
                clean_message = re.sub(r'\[FATAL\].*?\s+', '', line).strip()
                clean_message = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*?\s+', '', clean_message)
                
                if clean_message and 'Expected one of' not in clean_message:
                    errors.append({
                        "message": clean_message,
                        "line": None,
                        "column": None,
                        "type": "fatal_error"
                    })
                continue
            
            # 检查一般错误
            if '[ERROR]' in line or 'ERROR' in line:
                # 清理错误消息
                clean_message = re.sub(r'\[.*?\]', '', line).strip()
                clean_message = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*?\s+', '', clean_message)
                
                if clean_message:
                    errors.append({
                        "message": clean_message,
                        "line": None,
                        "column": None,
                        "type": "general_error"
                    })
        
        # 如果没有找到具体错误，但返回码非0，添加通用错误
        if not errors and 'Configuration OK' not in output:
            errors.append({
                "message": "配置验证失败，请检查配置语法",
                "line": None,
                "column": None,
                "type": "unknown_error"
            })
        
        return errors
    
    def _extract_warnings(self, output: str) -> List[Dict[str, Any]]:
        """
        从 Logstash 输出中提取警告信息
        
        Args:
            output: Logstash 输出
            
        Returns:
            警告信息列表
        """
        warnings = []
        lines = output.split('\n')
        
        for line in lines:
            if '[WARN]' in line or 'WARNING' in line:
                # 清理警告消息
                clean_message = re.sub(r'\[.*?\]', '', line).strip()
                clean_message = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*?\s+', '', clean_message)
                
                if clean_message:
                    warnings.append({
                        "message": clean_message,
                        "type": "warning"
                    })
        
        return warnings

# 全局验证器实例
validator = PipelineValidator()

def validate_pipeline_config(pipeline_content: str) -> Dict[str, Any]:
    """
    验证 Pipeline 配置的便捷函数
    
    Args:
        pipeline_content: Pipeline 配置内容
        
    Returns:
        验证结果
    """
    return validator.validate_pipeline(pipeline_content)
