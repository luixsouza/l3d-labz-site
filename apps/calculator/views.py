"""Views da calculadora de precificação — finas.

publica(request)  — calculadora pública (aberta a qualquer visitante, GET).
orcamento(request) — calculadora privada is_staff: GET mostra form; POST gera PDF.
"""
from __future__ import annotations

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render

from .forms import CalcForm, OrcamentoForm
from .presets import presets_json
from .services import CustoDefaults, PricingService

_DEF = CustoDefaults()


def publica(request):
    """Calculadora pública — exibe o form com defaults e presets para o JS (json_script).

    O cálculo ocorre 100% client-side em tempo real (calculator.js).
    Os presets são passados via json_script para que o JS possa auto-preencher
    campos sem duplicar valores literais no template.
    """
    form = CalcForm()
    return render(request, "calculator/publica.html", {
        "form": form,
        "defaults": _DEF,
        "presets_json": presets_json(),
    })


@user_passes_test(lambda u: u.is_staff)
def orcamento(request):
    """Calculadora privada (is_staff): GET mostra form; POST calcula server-side e gera PDF.

    A soma tarifa_efetiva = tarifa_base + adicional_bandeira é feita em
    OrcamentoForm.to_calc_data() antes de chamar PricingService.calcular.
    O PDF recebe somente dados públicos (sem custos internos) — T-calc-01.
    """
    if request.method == "POST":
        form = OrcamentoForm(request.POST)
        if form.is_valid():
            # cálculo server-side via PricingService — fonte única da verdade (decisão D-01)
            resultado = PricingService.calcular(**form.to_calc_data())
            preco_venda = resultado["preco_venda"]
            quantidade = form.cleaned_data["quantidade"]
            total = round(preco_venda * quantidade, 2)

            # somente dados públicos ao PDF — T-calc-01 (Information Disclosure)
            dados_pdf = {
                "cliente_nome":   form.cleaned_data["cliente_nome"],
                "peca_descricao": form.cleaned_data["peca_descricao"],
                "quantidade":     quantidade,
                "prazo_entrega":  form.cleaned_data["prazo_entrega"],
                "observacoes":    form.cleaned_data.get("observacoes", ""),
                "preco_venda":    preco_venda,
                "total":          total,
            }
            from .pdf import gerar_orcamento_pdf
            pdf_bytes = gerar_orcamento_pdf(dados_pdf)
            nome_arquivo = form.cleaned_data["cliente_nome"].lower().replace(" ", "-")
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="orcamento-{nome_arquivo}.pdf"'
            )
            return response
    else:
        form = OrcamentoForm()

    return render(request, "calculator/orcamento.html", {
        "form": form,
        "presets_json": presets_json(),
    })
