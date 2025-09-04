#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres
python - <<'PY'
import os, time, sys
import psycopg2
host=os.environ.get('DB_HOST','db')
port=int(os.environ.get('DB_PORT','5432'))
user=os.environ.get('DB_USER','leads')
password=os.environ.get('DB_PASSWORD','leads')
dbname=os.environ.get('DB_NAME','leads')
for i in range(60):
    try:
        psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname).close()
        print('DB is up')
        break
    except Exception as e:
        print('Waiting for DB...', e)
        time.sleep(1)
else:
    sys.exit('DB not available')
PY

# Make and apply migrations
python manage.py makemigrations --noinput
python manage.py migrate --noinput

if [ "${INGEST_ON_START:-0}" = "1" ]; then
  echo "Running initial ingestion..."
  if [ -n "${INGEST_GLOB:-}" ]; then
    python manage.py ingest_local --root "${INGEST_ROOT:-data/USA Database Business Leads}" --glob "${INGEST_GLOB}" || true
  else
    python manage.py ingest_local --root "${INGEST_ROOT:-data/USA Database Business Leads}" || true
  fi
fi

python manage.py runserver 0.0.0.0:8000
