"""Modelo de persistência de orçamentos da calculadora L3D Labz.

SEGURANÇA (T-fma-01): este modelo persiste SOMENTE os 7 dados públicos que
o cliente pode ver — espelho direto da allowlist de pdf.py (linhas 6-18).
NUNCA armazenar custo_material, custo_energia, custo_depreciacao, custo_maoobra,
subtotal, ajuste_falha, custo_total, taxa_falha_pct ou margem_pct.
"""
from __future__ import annotations

import uuid

from django.db import models

from apps.core.models import TimeStampedModel


class Orcamento(TimeStampedModel):
    """Orçamento gerado pelo staff — somente dados públicos + token de acesso."""

    token = models.UUIDField(
        "token público",
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    cliente_nome = models.CharField("nome do cliente", max_length=120)
    peca_descricao = models.CharField("descrição da peça", max_length=240)
    quantidade = models.PositiveIntegerField("quantidade", default=1)
    prazo_entrega = models.CharField("prazo de entrega", max_length=80)
    observacoes = models.TextField("observações", blank=True, default="")
    preco_venda = models.DecimalField(
        "preço unitário", max_digits=10, decimal_places=2
    )
    total = models.DecimalField("total", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "orçamento"
        verbose_name_plural = "orçamentos"
        # herda ordering = ["-created_at"] de TimeStampedModel

    def __str__(self) -> str:
        return f"Orçamento {self.cliente_nome} — {self.token}"
