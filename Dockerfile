FROM --platform=linux/amd64 python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-cloudrun.txt ./
RUN pip install --no-cache-dir -r requirements-cloudrun.txt \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

COPY . .

RUN mkdir -p /app/reports /app/data/processed/samsung_health/pre_sleep_stage1

EXPOSE 8080

CMD streamlit run prototype/samsung_sleep_forecasting_app.py \
    --server.address=0.0.0.0 \
    --server.port=${PORT} \
    --server.headless=true \
    --server.fileWatcherType=none \
    --server.runOnSave=false
