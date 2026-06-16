"""Admin do app calculadora — registra o modelo Orcamento."""
from django.contrib import admin

from .models import Orcamento


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    """Administração dos orçamentos emitidos — dados públicos apenas."""

    list_display = ("token", "cliente_nome", "peca_descricao", "quantidade", "total", "created_at")
    search_fields = ("cliente_nome", "peca_descricao", "token")
    readonly_fields = ("token", "created_at", "updated_at")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
