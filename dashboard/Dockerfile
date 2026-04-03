FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "streamlit>=1.40.0" \
    "httpx>=0.28.0" \
    "plotly>=5.24.0" \
    "pandas>=2.2.0"

COPY src/ /app/src/

ENV PYTHONPATH=/app/src

EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
