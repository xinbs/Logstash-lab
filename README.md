# Logstash 规则测试工具

一个简单易用的 Docker 化 Logstash 规则测试工具，提供 Web 界面进行规则编辑和测试。

## 🚀 快速开始

```bash
# 启动服务
./start.sh

# 访问 Web 界面
open http://localhost:19000
```

## ✨ 功能特性

- 🔧 Web 界面编辑 Logstash filter 规则
- 🚀 实时发送测试日志并查看解析结果  
- 🔥 支持热重载（3秒生效）
- 📚 内置常用日志格式示例模板
- 📱 响应式设计，支持移动端访问

## 📖 详细说明

查看 [使用指南.md](./使用指南.md) 了解详细使用方法和配置说明。

## 🛠️ 技术栈

- **后端**: Flask + Logstash 8.14.2
- **前端**: 原生 HTML/CSS/JavaScript  
- **部署**: Docker + Docker Compose
- **数据**: 文件存储 (NDJSON)

## 📁 项目结构

```
logstash-lab/
├── docker-compose.yml     # Docker 编排
├── start.sh              # 启动脚本
├── web/                  # Web 应用
├── logstash/             # Logstash 配置
└── data/                 # 数据输出
```

## 🔧 常用命令

```bash
# 启动
./start.sh

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重启
docker-compose restart
```

## ⚠️ 注意事项

- 仅用于测试环境，不要在生产环境暴露端口
- 需要至少 1GB 可用内存
- 确保端口 19000 和 15515 未被占用

---

🎉 **开始你的 Logstash 规则测试之旅吧！**