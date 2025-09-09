#!/usr/bin/env python3
import os
import time
import socket
import argparse
from typing import Optional
from datetime import datetime
import re

class MessageSender:
    def __init__(self, target_host: str, target_port: int, chunk_size: int = 1024, timeout: int = 5):
        self.target_host = target_host
        self.target_port = target_port
        self.chunk_size = chunk_size
        self.timeout = timeout

    def test_connection(self) -> bool:
        """测试目标服务器连接"""
        try:
            # 先尝试解析域名
            try:
                ip_address = socket.gethostbyname(self.target_host)
                print(f"域名 {self.target_host} 解析到 IP: {ip_address}")
            except socket.gaierror as e:
                print(f"域名解析失败: {e}")
                return False

            # 尝试连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target_host, self.target_port))
            print(f"成功连接到 {self.target_host}:{self.target_port}")
            sock.close()
            return True
        except socket.timeout:
            print(f"连接超时: {self.target_host}:{self.target_port}")
            return False
        except ConnectionRefusedError:
            print(f"连接被拒绝: {self.target_host}:{self.target_port}")
            return False
        except Exception as e:
            print(f"连接错误: {e}")
            return False

    def send_test_message(self) -> bool:
        """发送测试消息"""
        test_message = "test message from python client"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target_host, self.target_port))
            sock.sendall(test_message.encode('utf-8'))
            print("测试消息发送成功")
            sock.close()
            return True
        except Exception as e:
            print(f"测试消息发送失败: {e}")
            return False

    def send_message(self, message: str) -> bool:
        """发送消息，支持分块发送"""
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
                
                return True
        except socket.gaierror as e:
            print(f"域名解析失败: {e}")
            return False
        except Exception as e:
            print(f"发送失败: {e}")
            return False

class FileMonitor:
    def __init__(self, file_path: str, sender: MessageSender):
        self.file_path = file_path
        self.sender = sender
        self.last_size = 0
        self.interval = 1

    def _get_file_size(self) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(self.file_path)
        except OSError:
            return 0

    def _process_file_content(self) -> None:
        """处理文件内容"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content:
                    return

                # 按完整的日志格式分割
                log_entries = re.split(r'(?=<\d+>)', content)
                
                for entry in log_entries:
                    entry = entry.strip()
                    if not entry:
                        continue

                    # 只显示消息的前100个字符，避免日志过长
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发送消息: {entry[:100]}...")
                    
                    if self.sender.send_message(entry):
                        print("发送成功")
                    else:
                        print("发送失败")

        except Exception as e:
            print(f"处理文件内容时发生错误: {e}")

    def monitor(self) -> None:
        """监控文件变化"""
        if not os.path.exists(self.file_path):
            print(f"错误: 文件 {self.file_path} 不存在")
            return

        print(f"开始监控文件: {self.file_path}")
        print("按 Ctrl+C 退出")

        try:
            # 首次启动立即处理文件内容
            print("首次运行，处理现有内容...")
            self._process_file_content()
            self.last_size = self._get_file_size()
            
            # 继续监控文件变化
            while True:
                current_size = self._get_file_size()
                
                if current_size != self.last_size:
                    print(f"文件大小从 {self.last_size} 变化到 {current_size} 字节")
                    self._process_file_content()
                    self.last_size = current_size
                
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n停止监控")
        except Exception as e:
            print(f"发生错误: {e}")

class LoopFileMonitor(FileMonitor):
    def __init__(self, file_path: str, sender: MessageSender, interval: int = 1):
        super().__init__(file_path, sender)
        self.interval = interval

    def monitor(self) -> None:
        """循环监控文件内容"""
        if not os.path.exists(self.file_path):
            print(f"错误: 文件 {self.file_path} 不存在")
            return

        print(f"开始循环监控文件: {self.file_path}")
        print(f"监控间隔: {self.interval} 秒")
        print("按 Ctrl+C 退出")

        try:
            # 首次启动立即处理文件内容
            print("首次运行，处理现有内容...")
            self._process_file_content()
            
            # 继续循环监控
            while True:
                time.sleep(self.interval)
                self._process_file_content()

        except KeyboardInterrupt:
            print("\n停止监控")
        except Exception as e:
            print(f"发生错误: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='文件监控和消息发送工具',
        epilog='''
使用示例:
  # 控制台输入模式
  python send_message.py --host 192.168.31.218 --port 18091 --console
  
  # 监控文件模式
  python send_message.py /path/to/logfile --host 192.168.31.218 --port 18091
  
  # 循环发送模式
  python send_message.py /path/to/logfile --host 192.168.31.218 --port 18091 --loop --interval 2
  
  # 发送测试消息
  python send_message.py --host 192.168.31.218 --port 18091 --test
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('file_path', nargs='?', help='要监控的文件路径')
    parser.add_argument('--host', default='logstash.hids.infrasec.test.shopee.io', 
                       help='目标服务器地址(IP或域名)')
    parser.add_argument('--port', type=int, default=1515, help='目标服务器端口')
    parser.add_argument('--chunk-size', type=int, default=1024, help='发送块大小')
    parser.add_argument('--timeout', type=int, default=5, help='连接超时时间')
    parser.add_argument('--test', action='store_true', help='仅发送测试消息')
    parser.add_argument('--loop', action='store_true', help='启用循环发送模式')
    parser.add_argument('--interval', type=int, default=1, help='循环发送时的间隔时间(秒)')
    parser.add_argument('--console', action='store_true', help='启用控制台输入模式')

    args = parser.parse_args()

    sender = MessageSender(args.host, args.port, args.chunk_size, args.timeout)
    
    if args.test:
        sender.send_test_message()
        return

    # 控制台输入模式
    if args.console:
        print("进入控制台输入模式。输入 'quit' 或 'exit' 退出。")
        while True:
            try:
                user_input = input("请输入要发送的消息: ").strip()
                if user_input.lower() in ['quit', 'exit']:
                    break
                if user_input:
                    if sender.send_message(user_input):
                        print("发送成功")
                    else:
                        print("发送失败")
            except KeyboardInterrupt:
                print("\n退出控制台输入模式")
                break
        return

    # 确保文件监控模式下提供了文件路径
    if not args.file_path:
        parser.error("在非控制台模式下必须提供文件路径")

    # 测试连接
    if not sender.test_connection():
        while True:
            response = input("连接测试失败，是否重试? (y/n/d/t): ")
            if response.lower() == 'y':
                if sender.test_connection():
                    break
            elif response.lower() == 'n':
                return
            elif response.lower() == 'd':
                break
            elif response.lower() == 't':
                if sender.send_test_message():
                    break
            else:
                print("请输入 y (重试), n (退出), d (继续运行), 或 t (发送测试消息)")

    # 根据模式选择不同的 FileMonitor
    if args.loop:
        monitor = LoopFileMonitor(args.file_path, sender, args.interval)
    else:
        monitor = FileMonitor(args.file_path, sender)
    
    monitor.monitor()

if __name__ == '__main__':
    main()



#python send_message.py --host 192.168.31.218 --port 18091 --console