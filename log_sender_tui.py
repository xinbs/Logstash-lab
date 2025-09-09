#!/usr/bin/env python3
"""
日志发送工具 - 终端交互版本
基于send_message.py，提供友好的终端交互界面
适用于没有tkinter支持的环境
"""

import os
import time
import socket
import threading
import re
from datetime import datetime
from typing import Optional, Tuple
import sys


class MessageSender:
    """消息发送类 - 复用原有逻辑"""
    def __init__(self, target_host: str, target_port: int, chunk_size: int = 1024, timeout: int = 5):
        self.target_host = target_host
        self.target_port = target_port
        self.chunk_size = chunk_size
        self.timeout = timeout

    def test_connection(self) -> Tuple[bool, str]:
        """测试目标服务器连接，返回(成功状态, 消息)"""
        try:
            # 先尝试解析域名
            try:
                ip_address = socket.gethostbyname(self.target_host)
                dns_msg = f"域名 {self.target_host} 解析到 IP: {ip_address}"
            except socket.gaierror as e:
                return False, f"域名解析失败: {e}"

            # 尝试连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target_host, self.target_port))
            sock.close()
            return True, f"{dns_msg}\n✅ 成功连接到 {self.target_host}:{self.target_port}"
        except socket.timeout:
            return False, f"❌ 连接超时: {self.target_host}:{self.target_port}"
        except ConnectionRefusedError:
            return False, f"❌ 连接被拒绝: {self.target_host}:{self.target_port}"
        except Exception as e:
            return False, f"❌ 连接错误: {e}"

    def send_message(self, message: str) -> Tuple[bool, str]:
        """发送消息，返回(成功状态, 消息)"""
        try:
            with socket.create_connection((self.target_host, self.target_port), timeout=self.timeout) as sock:
                message_bytes = message.encode('utf-8')
                total_sent = 0
                
                while total_sent < len(message_bytes):
                    chunk = message_bytes[total_sent:total_sent + self.chunk_size]
                    sent = sock.send(chunk)
                    if sent == 0:
                        raise RuntimeError("连接断开")
                    total_sent += sent
                
                return True, f"✅ 消息发送成功 ({len(message_bytes)} 字节)"
        except socket.gaierror as e:
            return False, f"❌ 域名解析失败: {e}"
        except Exception as e:
            return False, f"❌ 发送失败: {e}"


class TerminalUI:
    """终端用户界面类"""
    
    def __init__(self):
        self.sender = None
        self.monitoring = False
        
    def print_banner(self):
        """打印程序横幅"""
        print("=" * 60)
        print("📤 日志发送工具 - 终端交互版本")
        print("基于 send_message.py 的友好终端界面")
        print("=" * 60)
        print()
    
    def print_menu(self):
        """打印主菜单"""
        print("\n🎯 主菜单:")
        print("1. 配置连接参数")
        print("2. 测试连接")
        print("3. 手动发送消息")
        print("4. 逐行发送消息")
        print("5. 文件监控模式")
        print("6. 显示当前配置")
        print("0. 退出程序")
        print("-" * 40)
    
    def configure_connection(self):
        """配置连接参数"""
        print("\n🔧 配置连接参数:")
        print("(直接回车使用默认值)")
        
        host = input(f"主机地址 [logstash.hids.infrasec.test.shopee.io]: ").strip()
        if not host:
            host = "logstash.hids.infrasec.test.shopee.io"
        
        port_input = input("端口 [1515]: ").strip()
        port = int(port_input) if port_input else 1515
        
        timeout_input = input("超时时间(秒) [5]: ").strip()
        timeout = int(timeout_input) if timeout_input else 5
        
        self.sender = MessageSender(host, port, timeout=timeout)
        print(f"✅ 连接配置已更新: {host}:{port} (超时: {timeout}s)")
    
    def test_connection(self):
        """测试连接"""
        if not self.sender:
            print("❌ 请先配置连接参数 (选项 1)")
            return
        
        print("\n🔍 正在测试连接...")
        success, msg = self.sender.test_connection()
        print(f"{'✅' if success else '❌'} {msg}")
    
    def send_single_message(self):
        """发送单条消息"""
        if not self.sender:
            print("❌ 请先配置连接参数 (选项 1)")
            return
        
        print("\n✏️ 手动发送消息:")
        print("(输入消息内容，支持多行，输入单独的'END'结束)")
        
        lines = []
        while True:
            line = input(">>> ")
            if line.strip() == "END":
                break
            lines.append(line)
        
        if not lines:
            print("❌ 没有输入任何内容")
            return
        
        message = "\n".join(lines)
        print(f"\n📤 正在发送消息 ({len(message)} 字符)...")
        
        success, msg = self.sender.send_message(message)
        print(f"{'✅' if success else '❌'} {msg}")
    
    def send_lines_message(self):
        """逐行发送消息"""
        if not self.sender:
            print("❌ 请先配置连接参数 (选项 1)")
            return
        
        print("\n📋 逐行发送消息:")
        print("(每行作为独立消息发送，输入单独的'END'结束)")
        
        lines = []
        while True:
            line = input(f"第{len(lines)+1}行>>> ")
            if line.strip() == "END":
                break
            if line.strip():  # 跳过空行
                lines.append(line.strip())
        
        if not lines:
            print("❌ 没有输入任何有效内容")
            return
        
        print(f"\n📤 将逐行发送 {len(lines)} 条消息，确认继续? (y/n): ", end="")
        if input().lower() != 'y':
            print("❌ 已取消发送")
            return
        
        success_count = 0
        for i, line in enumerate(lines, 1):
            print(f"📤 发送第 {i}/{len(lines)} 行...", end=" ")
            success, msg = self.sender.send_message(line)
            
            if success:
                success_count += 1
                print("✅")
            else:
                print(f"❌ {msg}")
        
        print(f"\n📊 发送完成: {success_count}/{len(lines)} 成功")
    
    def file_monitor_mode(self):
        """文件监控模式"""
        if not self.sender:
            print("❌ 请先配置连接参数 (选项 1)")
            return
        
        file_path = input("\n📁 请输入要监控的文件路径: ").strip()
        if not file_path:
            print("❌ 文件路径不能为空")
            return
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return
        
        print(f"🔍 开始监控文件: {file_path}")
        print("📝 按 Ctrl+C 停止监控")
        
        last_size = 0
        try:
            # 首次处理现有内容
            self._process_file_content(file_path)
            last_size = os.path.getsize(file_path)
            
            # 监控文件变化
            while True:
                current_size = os.path.getsize(file_path)
                if current_size != last_size:
                    print(f"📄 文件大小变化: {last_size} -> {current_size} 字节")
                    self._process_file_content(file_path)
                    last_size = current_size
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n⏹️ 停止文件监控")
        except Exception as e:
            print(f"❌ 监控错误: {e}")
    
    def _process_file_content(self, file_path: str):
        """处理文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content:
                    return

                # 按完整的日志格式分割
                log_entries = re.split(r'(?=<\d+>)', content)
                
                for entry in log_entries:
                    entry = entry.strip()
                    if not entry:
                        continue

                    preview = entry[:50] + "..." if len(entry) > 50 else entry
                    print(f"📤 发送: {preview}")
                    
                    success, msg = self.sender.send_message(entry)
                    print(f"{'✅' if success else '❌'} {msg}")

        except Exception as e:
            print(f"❌ 处理文件错误: {e}")
    
    def show_current_config(self):
        """显示当前配置"""
        print("\n⚙️ 当前配置:")
        if self.sender:
            print(f"主机: {self.sender.target_host}")
            print(f"端口: {self.sender.target_port}")
            print(f"超时: {self.sender.timeout}s")
            print(f"块大小: {self.sender.chunk_size}")
        else:
            print("❌ 尚未配置连接参数")
    
    def run(self):
        """运行主程序"""
        self.print_banner()
        
        # 使用默认配置
        self.sender = MessageSender("logstash.hids.infrasec.test.shopee.io", 1515)
        print("✅ 已使用默认配置初始化")
        
        while True:
            try:
                self.print_menu()
                choice = input("请选择功能 (0-6): ").strip()
                
                if choice == "0":
                    print("\n👋 再见!")
                    break
                elif choice == "1":
                    self.configure_connection()
                elif choice == "2":
                    self.test_connection()
                elif choice == "3":
                    self.send_single_message()
                elif choice == "4":
                    self.send_lines_message()
                elif choice == "5":
                    self.file_monitor_mode()
                elif choice == "6":
                    self.show_current_config()
                else:
                    print("❌ 无效选择，请输入 0-6")
            
            except KeyboardInterrupt:
                print("\n\n👋 程序已退出")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


def main():
    """主函数"""
    ui = TerminalUI()
    ui.run()


if __name__ == '__main__':
    main()
