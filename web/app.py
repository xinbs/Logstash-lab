from flask import Flask, request, render_template, jsonify
import os, time, json, pathlib, re
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

def write_filter(new_filter_block: str):
    """更新 pipeline 配置文件中的 filter 段"""
    with open(PIPELINE_PATH, "r", encoding="utf-8") as f:
        conf = f.read()
    conf2 = re.sub(FILTER_PATTERN, lambda m: new_filter_block + "\noutput {", conf)
    with open(PIPELINE_PATH, "w", encoding="utf-8") as f:
        f.write(conf2)

@app.route("/", methods=["GET"])
def index():
    """主页面 - 显示当前 filter 配置和最近结果"""
    # 读取当前 filter
    with open(PIPELINE_PATH, "r", encoding="utf-8") as f:
        conf = f.read()
    m = FILTER_PATTERN.search(conf)
    current_filter = m.group(0).split("output")[0].strip() if m else DEFAULT_FILTER
    
    # 读取最近 50 条结果
    last = []
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size-200000), os.SEEK_SET)  # 防爆内存
            lines = f.read().decode("utf-8", "ignore").splitlines()
            last = lines[-50:]
    
    return render_template("index.html", current_filter=current_filter, last=last)

@app.route("/save_filter", methods=["POST"])
def save_filter():
    """保存 filter 配置"""
    data = request.form.get("filter", "")
    block = data if data.strip().startswith("filter") else DEFAULT_FILTER
    write_filter(block)
    return jsonify({"ok": True, "message": "Filter 已保存并自动重载"})

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

if __name__ == "__main__":
    from waitress import serve
    
    # 初始化：确保目录存在
    os.makedirs(os.path.dirname(PIPELINE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(RESULT_FILE), exist_ok=True)
    
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 19000)))
