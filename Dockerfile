# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

# Normalize line endings so scripts created on Windows run in Linux containers.
RUN sed -i 's/\r$//' /app/entrypoint.sh /app/scripts/obtain_certbot.sh \
    && chmod +x /app/entrypoint.sh

RUN mkdir -p /app/logs \
    /app/staticfiles \
    /app/media \
    && touch /app/logs/clickid.log

RUN useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "clickid_core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
