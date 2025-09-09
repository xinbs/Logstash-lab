好的，给你一个「极简可用」的设计，满足：Docker 部署、Web 页面可编辑 Logstash 规则、在线投递测试日志并立刻查看解析结果。示例尽量短小，开箱即用。

方案概览（尽量简单）
	•	组件：web（Flask 简页） + logstash（开启热加载）
	•	交互：Web 页面只编辑 filter 段（更安全更直观）；输入测试日志 → Web 直接 POST 到 Logstash http input；结果由 Logstash 写到共享卷文件（NDJSON），Web 读取并显示。
	•	热更新：Web 将 filter 写入挂载卷中的 test.conf，Logstash 配置 config.reload.automatic: true，秒级热重载。

Browser ⇄ Flask(web) ——(写入 pipeline/filter、读结果文件)—— 共享卷 —— Logstash(HTTP input→filter→file/stdout)


⸻

目录结构

logstash-lab/
├─ docker-compose.yml
├─ web/
│  ├─ app.py
│  └─ templates/
│     └─ index.html
└─ logstash/
   ├─ logstash.yml
   ├─ pipelines.yml
   └─ pipeline/
      └─ test.conf        # 模板由 web 动态重写（只替换 filter 段）
└─ data/
   └─ out/
      └─ events.ndjson    # 解析结果（NDJSON），web 读取展示


⸻

docker-compose.yml（核心）

version: "3.9"
services:
  logstash:
    image: docker.elastic.co/logstash/logstash:8.14.2
    container_name: logstash-lab
    ports:
      - "8080:8080"         # http input（内网用，别暴露公网）
    environment:
      - LS_JAVA_OPTS=-Xms512m -Xmx512m
    volumes:
      - ./logstash/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - ./logstash/pipelines.yml:/usr/share/logstash/config/pipelines.yml:ro
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./data:/data
    healthcheck:
      test: ["CMD", "bash", "-lc", "curl -sS http://127.0.0.1:9600/_node/pipelines | grep -q test"]
      interval: 5s
      timeout: 3s
      retries: 20

  web:
    build: ./web
    container_name: logstash-lab-web
    ports:
      - "9000:9000"
    volumes:
      - ./logstash/pipeline:/app/pipeline         # 写 filter
      - ./data:/app/data                          # 读结果
    environment:
      - LOGSTASH_HTTP=http://logstash:8080        # 发送日志
    depends_on:
      - logstash


⸻

logstash/logstash.yml

http.host: "0.0.0.0"
api.enabled: true
api.http.host: "0.0.0.0"
api.http.port: 9600

# 热加载
config.reload.automatic: true
config.reload.interval: 3s

# 降低持久化干扰
path.data: /usr/share/logstash/data
path.logs: /usr/share/logstash/logs

logstash/pipelines.yml

- pipeline.id: test
  path.config: "/usr/share/logstash/pipeline/test.conf"
  pipeline.workers: 1
  pipeline.batch.size: 50

logstash/pipeline/test.conf（模板，filter 会被 Web 重写）

input {
  http {
    port => 8080
    additional_codecs => { "application/json" => "json" }
    # text/plain 会落在 [message] 字段
  }
}

### !!! Web 会把下面 filter {...} 整块替换 !!!
filter {
  # 默认示例（可被 web 覆盖）
  grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  date { match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"] target => "@timestamp" }
}

output {
  file {
    path => "/data/out/events.ndjson"
    codec => json_lines
  }
  stdout { codec => rubydebug }
}


⸻

Web 最小实现（Flask）

web/Dockerfile

FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/
COPY templates /app/templates
RUN pip install flask waitress
ENV PORT=9000
CMD ["python", "app.py"]

web/app.py

from flask import Flask, request, render_template, jsonify
import os, time, json, pathlib, re
import urllib.request

app = Flask(__name__)
PIPELINE_PATH = "/app/pipeline/test.conf"
RESULT_FILE = "/app/data/out/events.ndjson"
LOGSTASH_HTTP = os.getenv("LOGSTASH_HTTP", "http://logstash:8080")

FILTER_PATTERN = re.compile(r"(filter\s*\{)(.*?)(\}\s*output\s*\{)", re.S)

DEFAULT_FILTER = """filter {
  grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  date { match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"] target => "@timestamp" }
}
"""

def write_filter(new_filter_block: str):
    with open(PIPELINE_PATH, "r", encoding="utf-8") as f:
        conf = f.read()
    conf2 = re.sub(FILTER_PATTERN, lambda m: new_filter_block + "\noutput {", conf)
    with open(PIPELINE_PATH, "w", encoding="utf-8") as f:
        f.write(conf2)

@app.route("/", methods=["GET"])
def index():
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
    data = request.form.get("filter", "")
    block = data if data.strip().startswith("filter") else DEFAULT_FILTER
    write_filter(block)
    return jsonify({"ok": True})

@app.route("/test", methods=["POST"])
def test_send():
    body = request.form.get("logs", "")
    is_json = request.form.get("is_json") == "1"
    req = urllib.request.Request(
        LOGSTASH_HTTP,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json" if is_json else "text/plain"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass
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
    return jsonify({"ok": True, "events": [json.loads(x) for x in out if x.strip()]})

if __name__ == "__main__":
    from waitress import serve
    # 初始化：若 test.conf 不存在则写入模板
    p = pathlib.Path(PIPELINE_PATH)
    if not p.exists():
        os.makedirs(p.parent, exist_ok=True)
        with open(PIPELINE_PATH, "w", encoding="utf-8") as f:
            f.write(open("/app/templates/base_test.conf", "w"))
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 9000)))

web/templates/index.html（超简洁 UI）

<!doctype html><html><head><meta charset="utf-8"><title>Logstash Lab</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:24px;max-width:1100px}
textarea{width:100%;height:220px;font-family:ui-monospace,Menlo,Consolas,monospace}
pre{background:#111;color:#eee;padding:12px;overflow:auto;max-height:320px}
button{padding:8px 14px;margin-right:8px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
</style></head><body>
<h2>Logstash 规则测试</h2>

<div class="grid">
  <div>
    <h3>Filter（可编辑）</h3>
    <form id="f1">
      <textarea name="filter" id="filter">{{ current_filter }}</textarea>
      <div><button type="submit">保存 Filter（自动热重载）</button></div>
    </form>
  </div>
  <div>
    <h3>测试日志</h3>
    <form id="f2">
      <textarea name="logs" id="logs" placeholder="粘贴 text/plain（按行）或 JSON（勾选）"></textarea>
      <label><input type="checkbox" name="is_json" value="1"> 作为 application/json 发送</label>
      <div><button type="submit">发送并查看结果</button></div>
    </form>
  </div>
</div>

<h3>最近解析结果（NDJSON 展示前 50 条）</h3>
<pre id="out">{% for line in last %}{{ line }}
{% endfor %}</pre>

<script>
f1.onsubmit = async (e)=>{e.preventDefault();
  const fd = new FormData(f1);
  const r = await fetch('/save_filter',{method:'POST',body:fd});
  alert('已保存，Logstash 将自动热重载');
};
f2.onsubmit = async (e)=>{e.preventDefault();
  const fd = new FormData(f2);
  const r = await fetch('/test',{method:'POST',body:fd});
  const j = await r.json();
  out.textContent = j.events.map(x=>JSON.stringify(x)).join("\n");
};
</script>
</body></html>

说明：页面极简，只做三件事：保存 filter → 发送日志 → 显示 NDJSON 结果。
若需更华丽 UI/多 pipeline/多输出，后续再加即可。

⸻

启动与使用

# 1) 启动
docker compose up -d --build

# 2) 打开 Web
open http://localhost:9000

# 3) 在左侧编辑 filter，例如：
#   filter {
#     grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
#   }

# 4) 在右侧粘贴测试日志（text/plain 多行或勾选 JSON 发送），点击“发送并查看结果”
# 5) 下方会展示 /data/out/events.ndjson 最新 50 条


⸻

示例 filter 片段（可直接粘贴）

Apache 访问日志

filter {
  grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  mutate { rename => { "clientip" => "src_ip" } }
  date { match => ["timestamp","dd/MMM/yyyy:HH:mm:ss Z"] }
}

JSON 日志（应用直传 JSON）

filter {
  json { source => "message" }
  date { match => ["time","ISO8601"] target => "@timestamp" }
}

Suricata EVE（部分字段）

filter {
  json { source => "message" }
  if [event_type] == "alert" {
    mutate { add_field => { "attck_tactic" => "%{[alert][category]}" } }
  }
}


⸻

安全与稳定性要点
	•	不要把 8080 对公网（docker-compose 已暴露；仅用于本机/内网测试）。
	•	Logstash 运行 任意 filter 代码，仅用于可信场景。必要时可在 Web 限制/审计提交内容（白名单插件、行数限制等）。
	•	输出到文件避免外部依赖；如需看更直观的树形结构，可追加 stdout { codec => rubydebug }，用 docker logs -f logstash-lab 观察。
	•	若使用 file input 做回放，记得处理 sincedb（此方案用 http input，规避状态问题）。

⸻

可选增强（保持简单前提下的下一步）
	•	多 Pipeline：Web 生成 pipelines.yml 多条目 + 多 *.conf，实现并行对比。
	•	结果订阅：Logstash http output → Web /ingest_result 做实时推送（SSE/WebSocket）。
	•	内置样例集：在页面一键填充 Apache/Nginx/JSON/Suricata 样例，降低上手成本。
	•	限速/鉴权：在 Web 加简单 Token；Logstash http input 绑定 host 为容器网段。

⸻

