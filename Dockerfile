FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LEXIS_MODO_LIGERO=1 \
    PORT=8501

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; p = os.getenv('PORT', '8501'); urllib.request.urlopen(f'http://127.0.0.1:{p}/_stcore/health')" || exit 1

CMD ["sh", "-c", "streamlit run Code/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
