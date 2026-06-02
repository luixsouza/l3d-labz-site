"""Settings de desenvolvimento."""
from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ["127.0.0.1"]

# Toolbar instalada, porém oculta por padrão (não polui a tela).
# Para reativar pontualmente, troque o callback por: lambda r: True
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: False}

# Em dev servimos estáticos direto (sem manifest/hash), senão o runserver
# exigiria collectstatic. O manifest comprimido fica só em produção.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# E-mail vai para o console em dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
