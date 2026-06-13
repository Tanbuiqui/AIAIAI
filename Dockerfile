FROM python:3.11-slim

WORKDIR /app

# cài deps trước để tận dụng cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source
COPY pipeline.py llm.py main.py ./
COPY static ./static

EXPOSE 8080
ENV PORT=8080

# AgentBase yêu cầu listen 0.0.0.0:8080 + GET /health
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
