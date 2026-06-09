# L3D Labz — imagem de produção (Django + gunicorn)
# Base enxuta; deps de sistema só o necessário para Pillow/numpy/trimesh e fontes.
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# Deps de sistema:
# - fonts-dejavu-core: fontes reais p/ os cards de branding (branding.py) no Linux
# - curl: healthcheck
# - libpq5: runtime do Postgres (psycopg[binary] já traz libpq, mantido por segurança)
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Camada de deps separada p/ cache de build
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código
COPY . .

# Usuário não-root + scripts executáveis (git no Windows pode não preservar +x)
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/media /app/staticfiles \
    && chmod +x /app/docker/*.sh \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
