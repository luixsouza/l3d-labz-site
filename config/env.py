"""Leitor minimalista de .env (sem dependências externas).

Carrega pares CHAVE=valor de um arquivo .env para os.environ e oferece
helpers tipados. Mantemos isso simples de propósito: nada de mágica, só o
suficiente para alternar SQLite -> Postgres e ligar/desligar o cache real.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    """Lê um arquivo .env e popula os.environ (sem sobrescrever o que já existe)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    try:
        return int(os.environ[key])
    except (KeyError, ValueError):
        return default


def env_list(key: str, default: list[str] | None = None) -> list[str]:
    val = os.environ.get(key)
    if not val:
        return default or []
    return [item.strip() for item in val.split(",") if item.strip()]
