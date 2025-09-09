#!/usr/bin/env python3
"""
日志发送工具 - Streamlit Web版本
基于send_message.py，提供Web界面操作
"""

import streamlit as st
import socket
import os
import time
import threading
import re
from datetime import datetime
from typing import Optional, Tuple
import queue


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


def init_session_state():
    """初始化会话状态"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'monitoring' not in st.session_state:
        st.session_state.monitoring = False
    if 'last_file_size' not in st.session_state:
        st.session_state.last_file_size = 0


def add_log(message: str):
    """添加日志消息"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    st.session_state.logs.append(log_entry)
    # 保持最新的100条日志
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]


def create_sender(host: str, port: int, timeout: int) -> Optional[MessageSender]:
    """创建消息发送器"""
    try:
        if not host.strip():
            st.error("请输入主机地址")
            return None
        return MessageSender(host.strip(), port, timeout=timeout)
    except Exception as e:
        st.error(f"创建发送器失败: {e}")
        return None


def monitor_file(file_path: str, sender: MessageSender):
    """文件监控函数"""
    if not os.path.exists(file_path):
        add_log(f"❌ 文件不存在: {file_path}")
        return

    def get_file_size():
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def process_file_content():
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
                    add_log(f"📤 发送消息: {preview}")
                    
                    success, msg = sender.send_message(entry)
                    add_log(msg)

        except Exception as e:
            add_log(f"❌ 处理文件内容时发生错误: {e}")

    add_log(f"🔍 开始监控文件: {file_path}")
    
    # 首次启动立即处理文件内容
    process_file_content()
    st.session_state.last_file_size = get_file_size()
    
    # 监控文件变化
    while st.session_state.monitoring:
        current_size = get_file_size()
        
        if current_size != st.session_state.last_file_size:
            add_log(f"📄 文件大小从 {st.session_state.last_file_size} 变化到 {current_size} 字节")
            process_file_content()
            st.session_state.last_file_size = current_size
        
        time.sleep(1)
    
    add_log("⏹️ 停止文件监控")


def main():
    """主函数"""
    st.set_page_config(
        page_title="日志发送工具",
        page_icon="📤",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    st.title("📤 日志发送工具 - Web版本")
    st.markdown("基于 `send_message.py` 的Web界面版本，用于发送日志到 Logstash 端口")
    
    # 侧边栏 - 连接配置
    with st.sidebar:
        st.header("🔧 连接配置")
        
        host = st.text_input(
            "主机地址",
            value="192.168.31.218",
            help="输入IP地址或域名"
        )
        
        port = st.number_input(
            "端口",
            min_value=1,
            max_value=65535,
            value=1515,
            help="目标服务器端口"
        )
        
        timeout = st.number_input(
            "超时时间(秒)",
            min_value=1,
            max_value=60,
            value=5,
            help="网络连接超时时间"
        )
        
        st.divider()
        
        # 测试连接
        if st.button("🔍 测试连接", use_container_width=True):
            sender = create_sender(host, port, timeout)
            if sender:
                with st.spinner("正在测试连接..."):
                    success, msg = sender.test_connection()
                    add_log(f"连接测试: {msg}")
                    if success:
                        st.success("连接成功!")
                    else:
                        st.error("连接失败!")
        
        st.divider()
        
        # 清空日志
        if st.button("🗑️ 清空日志", use_container_width=True):
            st.session_state.logs = []
            st.rerun()

    # 主界面 - 两列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("✏️ 手动发送消息")
        
        message = st.text_area(
            "消息内容",
            height=150,
            placeholder="在此输入要发送的消息...\n支持多行输入，可选择整体发送或逐行发送"
        )
        
        # 发送选项
        col1_1, col1_2 = st.columns(2)
        
        with col1_1:
            if st.button("📤 发送整条消息", use_container_width=True):
                if not message.strip():
                    st.warning("请输入要发送的消息")
                else:
                    sender = create_sender(host, port, timeout)
                    if sender:
                        with st.spinner("正在发送消息..."):
                            success, msg = sender.send_message(message)
                            preview = message[:50] + "..." if len(message) > 50 else message
                            add_log(f"手动发送 '{preview}': {msg}")
                            
                            if success:
                                st.success("发送成功!")
                                st.rerun()  # 刷新页面清空输入
                            else:
                                st.error("发送失败!")
        
        with col1_2:
            if st.button("📤 逐行发送", use_container_width=True):
                if not message.strip():
                    st.warning("请输入要发送的消息")
                else:
                    sender = create_sender(host, port, timeout)
                    if sender:
                        lines = [line.strip() for line in message.split('\n') if line.strip()]
                        if not lines:
                            st.warning("没有找到有效的行内容")
                        else:
                            success_count = 0
                            total_lines = len(lines)
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, line in enumerate(lines):
                                status_text.text(f"正在发送第 {i+1}/{total_lines} 行...")
                                progress_bar.progress((i + 1) / total_lines)
                                
                                success, msg = sender.send_message(line)
                                preview = line[:30] + "..." if len(line) > 30 else line
                                
                                if success:
                                    success_count += 1
                                    add_log(f"✅ 逐行发送 [{i+1}/{total_lines}] '{preview}': {msg}")
                                else:
                                    add_log(f"❌ 逐行发送 [{i+1}/{total_lines}] '{preview}': {msg}")
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if success_count == total_lines:
                                st.success(f"🎉 全部发送成功! ({success_count}/{total_lines} 行)")
                                st.rerun()  # 刷新页面清空输入
                            elif success_count > 0:
                                st.warning(f"⚠️ 部分发送成功: {success_count}/{total_lines} 行")
                            else:
                                st.error(f"❌ 全部发送失败: {success_count}/{total_lines} 行")
    
    with col2:
        st.header("📁 文件监控")
        
        file_path = st.text_input(
            "文件路径",
            placeholder="输入要监控的文件路径...",
            help="输入日志文件的完整路径"
        )
        
        # 文件上传作为替代选项
        uploaded_file = st.file_uploader(
            "或上传文件",
            type=['log', 'txt'],
            help="上传日志文件进行监控"
        )
        
        if uploaded_file is not None:
            # 将上传的文件保存到临时位置
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_path = temp_path
            st.info(f"已上传文件: {uploaded_file.name}")
        
        col2_1, col2_2 = st.columns(2)
        
        with col2_1:
            if st.button("▶️ 开始监控", disabled=st.session_state.monitoring):
                if not file_path:
                    st.warning("请输入文件路径或上传文件")
                elif not os.path.exists(file_path):
                    st.error(f"文件不存在: {file_path}")
                else:
                    sender = create_sender(host, port, timeout)
                    if sender:
                        st.session_state.monitoring = True
                        # 在后台线程中启动监控
                        threading.Thread(
                            target=monitor_file,
                            args=(file_path, sender),
                            daemon=True
                        ).start()
                        st.success("已开始监控文件!")
                        st.rerun()
        
        with col2_2:
            if st.button("⏹️ 停止监控", disabled=not st.session_state.monitoring):
                st.session_state.monitoring = False
                st.info("已停止监控!")
                st.rerun()
        
        # 显示监控状态
        if st.session_state.monitoring:
            st.success("🟢 正在监控文件...")
        else:
            st.info("🔴 未在监控")
    
    # 日志显示区域
    st.header("📋 运行日志")
    
    if st.session_state.logs:
        # 显示日志，最新的在上面
        log_container = st.container()
        with log_container:
            for log in reversed(st.session_state.logs[-20:]):  # 显示最新20条
                st.text(log)
    else:
        st.info("暂无日志记录")
    
    # 自动刷新
    if st.session_state.monitoring:
        time.sleep(1)
        st.rerun()


if __name__ == '__main__':
    main()
