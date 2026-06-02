"""Classes base da arquitetura em camadas.

Convenção do projeto ("cada macaco no seu galho"):

    queries.py   -> só ORM. Monta querysets otimizados (select/prefetch) e
                    cacheia leituras. Não conhece HTTP nem regra de negócio.
    services.py  -> orquestra regras de negócio. Usa queries + mappers.
                    É o único lugar que escreve no banco.
    mappers.py   -> converte Model <-> dict/DTO para template e serializer.
    serializers.py -> (DRF) entrada/saída da API.
    views.py     -> fino: pega request, chama service, devolve resposta.
"""
from __future__ import annotations

from typing import Any, Generic, Iterable, TypeVar

from django.db.models import Model

M = TypeVar("M", bound=Model)


class BaseMapper(Generic[M]):
    """Converte instâncias de Model em dicionários prontos para a view."""

    @classmethod
    def to_dict(cls, instance: M) -> dict[str, Any]:  # pragma: no cover - abstrato
        raise NotImplementedError

    @classmethod
    def to_list(cls, instances: Iterable[M]) -> list[dict[str, Any]]:
        return [cls.to_dict(obj) for obj in instances]


class BaseService:
    """Marcador para serviços. Mantém a intenção explícita e padroniza imports."""

    pass


class BaseQuery:
    """Marcador para conjuntos de consultas reutilizáveis e cacheáveis."""

    pass
