# Dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir requests bencodepy

COPY scraper.py .

CMD ["python", "scraper.py"]
