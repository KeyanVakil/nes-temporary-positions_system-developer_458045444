FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "httpx>=0.28.0"

COPY src/ /app/src/

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "simulator.main"]
