"""Consultas ORM read-only para orçamentos — só ORM, sem regra de negócio.

OrcamentoQuery.by_token(token) é o único ponto de leitura por token UUID.
Sem cache: orçamentos são dados individuais e podem ser atualizados.
"""
from __future__ import annotations

from apps.core.layers import BaseQuery

from .models import Orcamento


class OrcamentoQuery(BaseQuery):
    """Consultas read-only para o modelo Orcamento."""

    @staticmethod
    def by_token(token) -> Orcamento | None:
        """Retorna o Orcamento com o token dado, ou None se não encontrado."""
        return Orcamento.objects.filter(token=token).first()
