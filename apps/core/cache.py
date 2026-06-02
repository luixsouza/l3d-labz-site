"""Helpers de cache compartilhados pela camada queries/ de cada app.

Centralizamos a montagem de chave e o get-or-set para que toda a aplicação
cacheie de forma consistente e com TTLs vindos de settings.CACHE_TTL.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable, TypeVar

from django.conf import settings
from django.core.cache import cache

T = TypeVar("T")


def build_key(namespace: str, *parts: Any) -> str:
    """Monta uma chave de cache estável a partir de partes arbitrárias."""
    raw = ":".join(str(p) for p in parts)
    if len(raw) > 180:  # evita chaves gigantes (ex.: filtros longos)
        raw = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return f"{namespace}:{raw}" if raw else namespace


def ttl(bucket: str = "medium") -> int:
    return settings.CACHE_TTL.get(bucket, 300)


def get_or_set(key: str, producer: Callable[[], T], bucket: str = "medium") -> T:
    """Retorna o valor cacheado ou executa `producer`, cacheando o resultado."""
    sentinel = object()
    cached = cache.get(key, sentinel)
    if cached is not sentinel:
        return cached  # type: ignore[return-value]
    value = producer()
    cache.set(key, value, timeout=ttl(bucket))
    return value


def invalidate(*keys: str) -> None:
    cache.delete_many(list(keys))
