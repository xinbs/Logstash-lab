FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/
COPY templates /app/templates
RUN pip install flask waitress
ENV PORT=19000
CMD ["python", "app.py"]
