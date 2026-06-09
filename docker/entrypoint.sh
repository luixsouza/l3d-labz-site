#!/bin/sh
# Entrypoint da web: espera o Postgres, aplica migrações, coleta estáticos
# e então executa o CMD (gunicorn). O seed do catálogo NÃO roda aqui — é um
# passo explícito do deploy (ver .github/workflows/deploy.yml), pra ser
# deliberado e visível.
set -e

echo "[entrypoint] aguardando o banco em ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
python <<'PY'
import os, time, sys
import psycopg
host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
db   = os.environ.get("POSTGRES_DB", "nexora")
user = os.environ.get("POSTGRES_USER", "nexora")
pwd  = os.environ.get("POSTGRES_PASSWORD", "nexora")
for i in range(60):
    try:
        psycopg.connect(host=host, port=port, dbname=db, user=user, password=pwd, connect_timeout=2).close()
        print("[entrypoint] banco pronto.")
        sys.exit(0)
    except Exception as e:
        print(f"[entrypoint] tentativa {i+1}/60: {e}")
        time.sleep(2)
print("[entrypoint] banco não respondeu a tempo.", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] migrando..."
python manage.py migrate --noinput

echo "[entrypoint] coletando estáticos..."
python manage.py collectstatic --noinput

echo "[entrypoint] subindo: $*"
exec "$@"
