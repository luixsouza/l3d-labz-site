"""Settings de produção."""
from .base import *  # noqa: F401,F403
from config.env import env_bool, env_list

DEBUG = False

# Origens confiáveis p/ CSRF — obrigatório atrás de proxy HTTPS (login, checkout).
# Ex.: CSRF_TRUSTED_ORIGINS=https://l3dlabz.com.br,https://www.l3dlabz.com.br
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", [])

# Atrás de Cloudflare Tunnel o HTTPS é da borda; deixe o redirect com a Cloudflare
# ("Always Use HTTPS") p/ evitar loop. Em A-record + Let's Encrypt, ligue via env.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
