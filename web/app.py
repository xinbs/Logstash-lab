from flask import Flask, request, render_template, jsonify
import os, time, json, pathlib, re, subprocess
import urllib.request

app = Flask(__name__)
PIPELINE_PATH = "/app/pipeline/test.conf"
RESULT_FILE = "/app/data/out/events.ndjson"
LOGSTASH_HTTP = os.getenv("LOGSTASH_HTTP", "http://logstash:15515")

FILTER_PATTERN = re.compile(r"(filter\s*\{)(.*?)(\}\s*output\s*\{)", re.S)

DEFAULT_FILTER = """filter {
  grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  date { match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"] target => "@timestamp" }
}
"""

def extract_metadata_type_from_filter(filter_content):
    """从 filter 内容中提取 metadata type"""
    # 匹配 if "xxx" == [@metadata][type] { 模式
    match = re.search(r'if\s+"([^"]+)"\s*==\s*\[@metadata\]\[type\]', filter_content)
    return match.group(1) if match else ""

def wrap_filter_with_condition(filter_rules, metadata_type):
    """将 filter 规则包装在条件判断中"""
    if not metadata_type.strip():
        return filter_rules
    
    # 移除外层的 filter {} 包装（如果有）
    content = filter_rules.strip()
    if content.startswith('filter'):
        # 提取 filter { ... } 中间的内容
        match = re.match(r'filter\s*\{(.*)\}', content, re.DOTALL)
        if match:
            content = match.group(1).strip()
    
    # 检查是否已经有条件判断，如果有则提取内部内容
    # 匹配 if "任何值" == [@metadata][type] { ... } 模式
    condition_match = re.match(r'\s*if\s+"[^"]*"\s*==\s*\[@metadata\]\[type\]\s*\{(.*)\}\s*$', content, re.DOTALL)
    if condition_match:
        # 如果已经有条件判断，提取内部内容
        content = condition_match.group(1).strip()
    
    # 缩进处理：为每行添加适当的缩进
    lines = content.split('\n')
    indented_lines = []
    for line in lines:
        if line.strip():  # 只对非空行添加缩进
            indented_lines.append('        ' + line.lstrip())  # 8个空格缩进
        else:
            indented_lines.append('')
    
    indented_content = '\n'.join(indented_lines)
    
    # 生成带条件的 filter，固定使用 "test"
    wrapped = f'''filter {{
    if "test" == [@metadata][type] {{
{indented_content}
    }}
}}'''
    return wrapped

def write_filter(new_filter_block: str, metadata_type: str = ""):
    """更新 pipeline 配置文件中的 filter 段"""
    with open(PIPELINE_PATH, "r", encoding="utf-8") as f:
        conf = f.read()
    
    lines = conf.split('\n')
    
    # 固定使用 "test" 作为 metadata type，更新第一个 filter 块中的 metadata 设置
    if metadata_type.strip():
        # 查找第一个 filter 块（metadata 设置块）
        first_filter_updated = False
        for i, line in enumerate(lines):
            if 'add_field => { "[@metadata][type]"' in line:
                # 固定设置为 "test"
                lines[i] = '    add_field => { "[@metadata][type]" => "test" }'
                first_filter_updated = True
                break
        
        # 如果没有找到 metadata 设置，在 input 后添加
        if not first_filter_updated:
            input_end = -1
            for i, line in enumerate(lines):
                if line.strip() == '}' and i > 0:
                    # 检查前面是否有 input 相关内容
                    prev_lines = '\n'.join(lines[max(0, i-10):i])
                    if 'input {' in prev_lines and 'http {' in prev_lines:
                        input_end = i
                        break
            
            if input_end != -1:
                metadata_filter = [
                    "",
                    "# 自动设置 metadata type，这里会被 Web 界面动态替换",
                    "filter {",
                    "  mutate {",
                    f'    add_field => {{ "[@metadata][type]" => "{metadata_type}" }}',
                    "  }",
                    "}"
                ]
                lines = lines[:input_end + 1] + metadata_filter + lines[input_end + 1:]
    
    # 查找主要的 filter 块（带注释标记的）
    filter_start_line = -1
    filter_end_line = -1
    
    # 查找带有替换标记的 filter 块
    for i, line in enumerate(lines):
        if '!!! Web 会把下面 filter' in line:
            # 找到下一个 filter 块
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if stripped.startswith('filter {') or stripped == 'filter{':
                    filter_start_line = j
                    break
            break
    
    if filter_start_line == -1:
        # 如果没有找到标记的 filter 块，查找最后一个 filter 块
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                continue
            if stripped.startswith('filter {') or stripped == 'filter{':
                filter_start_line = i
    
    if filter_start_line != -1:
        # 找到 filter 块的结束行 - 改进的 bracket counting
        bracket_count = 0
        in_string = False
        escape_next = False
        
        for i in range(filter_start_line, len(lines)):
            line = lines[i]
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            filter_end_line = i
                            break
                            
            if filter_end_line != -1:
                break
        
        if filter_end_line == -1:
            # 如果无法找到结束行，尝试查找下一个顶级块（如 output）
            for i in range(filter_start_line + 1, len(lines)):
                stripped = lines[i].strip()
                if stripped.startswith('output {') or stripped.startswith('input {'):
                    filter_end_line = i - 1
                    break
            
            if filter_end_line == -1:
                filter_end_line = len(lines) - 1
        
        # 替换主要的 filter 块
        new_lines = lines[:filter_start_line] + [new_filter_block] + lines[filter_end_line + 1:]
    else:
        # 如果没有找到 filter 块，在最后添加
        new_lines = lines + ["", new_filter_block]
    
    conf2 = '\n'.join(new_lines)
    
    with open(PIPELINE_PATH, "w", encoding="utf-8") as f:
        f.write(conf2)

def extract_current_filter(conf):
    """从完整配置中提取当前的 filter 块"""
    lines = conf.split('\n')
    filter_start_line = -1
    filter_end_line = -1
    
    # 查找 filter 块的开始行（跳过注释）
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        if stripped.startswith('filter {') or stripped == 'filter{':
            filter_start_line = i
            break
    
    if filter_start_line == -1:
        return DEFAULT_FILTER
    
    # 找到 filter 块的结束行
    bracket_count = 0
    for i in range(filter_start_line, len(lines)):
        line = lines[i]
        for char in line:
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    filter_end_line = i
                    break
        if filter_end_line != -1:
            break
    
    if filter_end_line == -1:
        return DEFAULT_FILTER
    
    return '\n'.join(lines[filter_start_line:filter_end_line + 1])

@app.route("/", methods=["GET"])
def index():
    """主页面 - 显示当前 filter 配置和最近结果"""
    # 读取当前 filter
    with open(PIPELINE_PATH, "r", encoding="utf-8") as f:
        conf = f.read()
    current_filter = extract_current_filter(conf)
    
    # 提取当前的 metadata type
    current_metadata_type = extract_metadata_type_from_filter(current_filter)
    
    # 读取最近 50 条结果
    last = []
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size-200000), os.SEEK_SET)  # 防爆内存
            lines = f.read().decode("utf-8", "ignore").splitlines()
            last = lines[-50:]
    
    return render_template("index.html", 
                         current_filter=current_filter, 
                         current_metadata_type=current_metadata_type,
                         last=last)

@app.route("/save_filter", methods=["POST"])
def save_filter():
    """保存 filter 配置"""
    filter_data = request.form.get("filter", "")
    # 固定使用 "test" 作为 metadata type
    metadata_type = "test"
    auto_wrap_condition = True  # 默认总是自动包装
    
    # 处理 filter 内容
    if not filter_data.strip():
        filter_data = DEFAULT_FILTER
    
    # 总是通过 wrap_filter_with_condition 处理，以确保条件判断使用正确的值
    block = wrap_filter_with_condition(filter_data, metadata_type)
    
    write_filter(block, metadata_type)
    
    # 构造响应消息
    message = f"Filter 已保存并自动重载 (已自动添加条件判断: if \"test\" == [@metadata][type])"
    
    return jsonify({"ok": True, "message": message})

@app.route("/test", methods=["POST"])
def test_send():
    """发送测试日志到 Logstash"""
    body = request.form.get("logs", "")
    is_json = request.form.get("is_json") == "1"
    
    if not body.strip():
        return jsonify({"ok": False, "message": "请输入测试日志内容"})
    
    req = urllib.request.Request(
        LOGSTASH_HTTP,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json" if is_json else "text/plain"},
        method="POST",
    )
    
    try:
        urllib.request.urlopen(req, timeout=3)
        send_status = "✅ 日志发送成功"
    except Exception as e:
        send_status = f"❌ 日志发送失败: {e}"
    
    # 简单等待 Logstash flush
    time.sleep(0.6)
    
    # 回读末尾 50 条
    out = []
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size-200000), os.SEEK_SET)
            lines = f.read().decode("utf-8", "ignore").splitlines()
            out = lines[-50:]
    
    events = []
    for line in out:
        if line.strip():
            try:
                events.append(json.loads(line))
            except:
                pass
    
    return jsonify({
        "ok": True, 
        "message": send_status,
        "events": events
    })

@app.route("/clear_results", methods=["POST"])
def clear_results():
    """清空结果文件"""
    try:
        if os.path.exists(RESULT_FILE):
            open(RESULT_FILE, 'w').close()
        return jsonify({"ok": True, "message": "结果已清空"})
    except Exception as e:
        return jsonify({"ok": False, "message": f"清空失败: {e}"})

@app.route("/get_parsed_results", methods=["GET"])
def get_parsed_results():
    """获取最新的解析记录"""
    try:
        events = []
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if os.path.exists(RESULT_FILE):
            with open(RESULT_FILE, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(max(0, size-500000), os.SEEK_SET)  # 读取最后 500KB
                lines = f.read().decode("utf-8", "ignore").splitlines()
                
                # 获取最新的 50 条记录
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                
                for line in recent_lines:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            # 添加时间戳信息
                            if '@timestamp' in event:
                                event['_parsed_time'] = current_time
                            events.append(event)
                        except json.JSONDecodeError:
                            # 跳过无效的 JSON 行
                            continue
        
        return jsonify({
            "ok": True, 
            "events": events,
            "count": len(events),
            "message": f"成功获取 {len(events)} 条解析记录"
        })
        
    except Exception as e:
        return jsonify({"ok": False, "message": f"获取解析记录失败: {e}"})

@app.route("/logstash_logs", methods=["GET"])
def logstash_logs():
    """获取 Logstash 日志"""
    try:
        logs_content = []
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 定义可能的日志文件路径
        log_paths = [
            "/app/data/../logs/logstash-plain.log",    # 通过挂载访问
            "/app/data/../logs/logstash.log",
            "/logs/logstash-plain.log",                # 直接日志挂载
            "/logs/logstash.log"
        ]
        
        # 尝试读取日志文件
        log_file_found = False
        for log_path in log_paths:
            if os.path.exists(log_path):
                log_file_found = True
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # 读取最后 100 行
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        
                        logs_content.append(f"📋 Logstash 日志文件: {log_path}")
                        logs_content.append(f"📅 读取时间: {current_time}")
                        logs_content.append(f"📊 显示最近 {len(recent_lines)} 条日志")
                        logs_content.append("=" * 80)
                        logs_content.extend([line.rstrip() for line in recent_lines])
                        break
                        
                except Exception as e:
                    logs_content.append(f"❌ 读取日志文件失败: {e}")
                    continue
        
        # 如果没有找到日志文件，尝试通过 Docker API 获取容器日志
        if not log_file_found:
            try:
                import subprocess
                result = subprocess.run([
                    "docker", "logs", "--tail", "50", "logstash-lab"
                ], capture_output=True, text=True, timeout=10, cwd="/")
                
                if result.returncode == 0:
                    logs_content.append(f"📋 Logstash 容器日志 (Docker API)")
                    logs_content.append(f"📅 获取时间: {current_time}")
                    logs_content.append("📊 显示最近 50 条日志")
                    logs_content.append("=" * 80)
                    
                    # 合并 stdout 和 stderr
                    container_logs = result.stdout + result.stderr
                    logs_content.extend(container_logs.splitlines())
                else:
                    raise Exception(f"Docker 命令执行失败: {result.stderr}")
                    
            except Exception as docker_error:
                # 如果都失败了，返回指导信息
                logs_content = [
                    f"📋 Logstash 日志查看功能",
                    f"📅 当前时间: {current_time}",
                    "",
                    "⚠️ 暂时无法直接读取日志文件，请使用以下命令行方式：",
                    "",
                    "🔧 查看实时日志：",
                    "sudo docker compose logs -f logstash",
                    "",
                    "📊 查看最近 50 条日志：",
                    "sudo docker compose logs --tail=50 logstash",
                    "",
                    "🔍 查看最近 100 条日志：",
                    "sudo docker compose logs --tail=100 logstash",
                    "",
                    "⚡ 只看错误日志：",
                    "sudo docker compose logs logstash | grep -i error",
                    "",
                    f"❌ 错误信息: {docker_error}",
                    "",
                    "💡 提示: 重启容器后日志文件可能需要一些时间生成"
                ]
        
        return jsonify({"ok": True, "logs": "\n".join(logs_content)})
        
    except Exception as e:
        return jsonify({"ok": False, "message": f"获取日志失败: {e}"})

def extract_filter_from_pipeline(pipeline_content):
    """从 pipeline 配置中提取 filter 块内容"""
    lines = pipeline_content.split('\n')
    filter_blocks = []
    current_block = []
    in_filter_block = False
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 跳过空行和注释
        if not stripped or stripped.startswith('#'):
            if in_filter_block:
                current_block.append(line)
            continue
        
        # 检查是否是 filter 块的开始
        if stripped.startswith('filter') and '{' in stripped and not in_filter_block:
            in_filter_block = True
            current_block = [line]
            bracket_count = 0
            
            # 计算这一行的括号
            for char in stripped:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                if not in_string:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
            
            if bracket_count == 0:
                # 单行 filter 块
                filter_blocks.append('\n'.join(current_block))
                in_filter_block = False
                current_block = []
        elif in_filter_block:
            current_block.append(line)
            
            # 计算这一行的括号
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                if not in_string:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
            
            # 检查是否结束
            if bracket_count == 0:
                filter_blocks.append('\n'.join(current_block))
                in_filter_block = False
                current_block = []
    
    return filter_blocks

def extract_main_filter_content(filter_block):
    """从 filter 块中提取主要内容（去除外层 filter {} 包装）"""
    lines = filter_block.split('\n')
    content_lines = []
    found_opening = False
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for line in lines:
        stripped = line.strip()
        
        if not found_opening:
            if stripped.startswith('filter') and '{' in stripped:
                found_opening = True
                # 提取 { 后面的内容
                brace_pos = line.find('{')
                after_brace = line[brace_pos + 1:].strip()
                if after_brace:
                    content_lines.append(after_brace)
                continue
            continue
        
        # 计算括号层级
        line_bracket_count = bracket_count
        for char in line:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
            if not in_string:
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
        
        # 如果这一行结束后括号平衡了，说明这是最后一行
        if bracket_count < 0:
            # 去除最后的 }
            brace_pos = line.rfind('}')
            if brace_pos >= 0:
                before_brace = line[:brace_pos].rstrip()
                if before_brace:
                    content_lines.append(before_brace)
            break
        else:
            content_lines.append(line)
    
    return '\n'.join(content_lines)

@app.route("/upload_pipeline", methods=["POST"])
def upload_pipeline():
    """接收 pipeline 配置文件，提取 filter 并应用到测试环境"""
    try:
        # 获取上传的内容
        if 'file' in request.files:
            # 文件上传
            file = request.files['file']
            if file.filename == '':
                return jsonify({"ok": False, "message": "未选择文件"})
            pipeline_content = file.read().decode('utf-8')
        elif 'pipeline' in request.form:
            # 表单数据
            pipeline_content = request.form.get('pipeline', '')
        else:
            return jsonify({"ok": False, "message": "未提供 pipeline 内容"})
        
        if not pipeline_content.strip():
            return jsonify({"ok": False, "message": "Pipeline 内容为空"})
        
        # 提取 filter 块
        filter_blocks = extract_filter_from_pipeline(pipeline_content)
        
        if not filter_blocks:
            return jsonify({"ok": False, "message": "未在 pipeline 中找到 filter 块"})
        
        # 选择最后一个 filter 块（通常是主要的处理逻辑）
        main_filter_block = filter_blocks[-1]
        
        # 提取 filter 内容（去除外层包装）
        filter_content = extract_main_filter_content(main_filter_block)
        
        if not filter_content.strip():
            return jsonify({"ok": False, "message": "提取的 filter 内容为空"})
        
        # 应用到测试环境（使用现有的逻辑）
        metadata_type = "test"
        
        # 包装 filter 内容
        block = wrap_filter_with_condition(filter_content, metadata_type)
        
        # 写入配置文件
        write_filter(block, metadata_type)
        
        return jsonify({
            "ok": True, 
            "message": f"Pipeline 已成功上传并应用到测试环境",
            "extracted_filters": len(filter_blocks),
            "applied_filter_preview": filter_content[:200] + "..." if len(filter_content) > 200 else filter_content
        })
        
    except Exception as e:
        return jsonify({"ok": False, "message": f"处理 pipeline 失败: {str(e)}"})

if __name__ == "__main__":
    # 初始化：确保目录存在
    os.makedirs(os.path.dirname(PIPELINE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(RESULT_FILE), exist_ok=True)
    
    # 开发模式：使用 Flask 开发服务器（支持自动重载）
    if os.getenv("FLASK_ENV") == "development":
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 19000)), debug=True)
    else:
        # 生产模式：使用 Waitress
        from waitress import serve
        serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 19000)))
