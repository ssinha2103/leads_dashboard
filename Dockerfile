FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# Copy project (mounted again by volume in compose for dev)
COPY . /app

# Collect static assets at build time (safe to ignore failures in dev)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["/bin/bash", "-lc", "./docker/entrypoint.sh"]
