"""Views da calculadora de precificação — finas.

publica(request)  — calculadora pública (aberta a qualquer visitante, GET).
orcamento(request) — calculadora privada is_staff: GET mostra form; POST gera PDF.
"""
from __future__ import annotations

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render

from .forms import CalcForm, OrcamentoForm
from .services import CustoDefaults, PricingService

_DEF = CustoDefaults()


def publica(request):
    """Calculadora pública — exibe o form com defaults; cálculo ocorre client-side (JS)."""
    form = CalcForm()
    return render(request, "calculator/publica.html", {
        "form": form,
        "defaults": _DEF,
    })


@user_passes_test(lambda u: u.is_staff)
def orcamento(request):
    """Calculadora privada (is_staff): GET mostra form; POST calcula server-side e gera PDF."""
    if request.method == "POST":
        form = OrcamentoForm(request.POST)
        if form.is_valid():
            # cálculo server-side via PricingService — fonte única da verdade (decisão D-01)
            resultado = PricingService.calcular(**form.to_calc_data())
            preco_venda = resultado["preco_venda"]
            quantidade = form.cleaned_data["quantidade"]
            total = round(preco_venda * quantidade, 2)

            dados_pdf = {
                "cliente_nome":    form.cleaned_data["cliente_nome"],
                "peca_descricao":  form.cleaned_data["peca_descricao"],
                "quantidade":      quantidade,
                "prazo_entrega":   form.cleaned_data["prazo_entrega"],
                "observacoes":     form.cleaned_data.get("observacoes", ""),
                "preco_venda":     preco_venda,
                "total":           total,
            }
            from .pdf import gerar_orcamento_pdf  # importação diferida (pdf.py criado na Task 3)
            pdf_bytes = gerar_orcamento_pdf(dados_pdf)
            nome_arquivo = form.cleaned_data["cliente_nome"].lower().replace(" ", "-")
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="orcamento-{nome_arquivo}.pdf"'
            )
            return response
    else:
        form = OrcamentoForm()

    return render(request, "calculator/orcamento.html", {"form": form})
