FROM python:3.11-slim
WORKDIR /app

# 安装 docker 客户端
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

COPY app.py /app/
COPY templates /app/templates
RUN pip install flask waitress
ENV PORT=19000
CMD ["python", "app.py"]
