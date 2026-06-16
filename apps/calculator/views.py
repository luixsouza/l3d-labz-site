"""Views da calculadora de precificação — finas.

publica(request)            — calculadora pública (aberta a qualquer visitante, GET).
orcamento(request)          — calculadora privada is_staff: GET mostra form;
                              POST calcula, persiste e devolve link público compartilhável.
orcamento_publico(request, token) — página pública read-only por token UUID (sem auth).
orcamento_pdf(request, token)     — PDF público por token UUID (sem auth; só dados públicos).
"""
from __future__ import annotations

from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from .forms import CalcForm, OrcamentoForm
from .mappers import OrcamentoMapper
from .presets import presets_json
from .queries import OrcamentoQuery
from .services import CustoDefaults, OrcamentoService, PricingService

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
    """Calculadora privada (is_staff): GET mostra form; POST calcula, persiste e exibe link.

    Após o POST bem-sucedido, o orçamento é persistido via OrcamentoService.criar
    e a página é re-renderizada com o link público copiável e o botão de PDF.
    O PDF em si é servido pela rota pública /orcamento/<token>/pdf/.

    A soma tarifa_efetiva = tarifa_base + adicional_bandeira é feita em
    OrcamentoForm.to_calc_data() antes de chamar PricingService.calcular.
    Somente dados públicos são persistidos — T-calc-01 / T-fma-01.
    """
    if request.method == "POST":
        form = OrcamentoForm(request.POST)
        if form.is_valid():
            # cálculo server-side via PricingService — fonte única da verdade (decisão D-01)
            resultado = PricingService.calcular(**form.to_calc_data())
            preco_venda = resultado["preco_venda"]
            quantidade = form.cleaned_data["quantidade"]
            total = round(preco_venda * quantidade, 2)

            # somente dados públicos ao service — T-calc-01 / T-fma-01
            dados_publicos = {
                "cliente_nome":   form.cleaned_data["cliente_nome"],
                "peca_descricao": form.cleaned_data["peca_descricao"],
                "quantidade":     quantidade,
                "prazo_entrega":  form.cleaned_data["prazo_entrega"],
                "observacoes":    form.cleaned_data.get("observacoes", ""),
                "preco_venda":    preco_venda,
                "total":          total,
            }

            # persiste via service e monta links compartilháveis
            orcamento_obj = OrcamentoService.criar(**dados_publicos)
            link_publico = request.build_absolute_uri(
                reverse("calculator:orcamento_publico", args=[orcamento_obj.token])
            )
            link_pdf = request.build_absolute_uri(
                reverse("calculator:orcamento_pdf", args=[orcamento_obj.token])
            )

            return render(request, "calculator/orcamento.html", {
                "form": form,
                "presets_json": presets_json(),
                "orcamento_gerado": {
                    "link_publico": link_publico,
                    "link_pdf": link_pdf,
                    "cliente_nome": orcamento_obj.cliente_nome,
                },
            })
    else:
        form = OrcamentoForm()

    return render(request, "calculator/orcamento.html", {
        "form": form,
        "presets_json": presets_json(),
    })


def orcamento_publico(request, token):
    """Página pública read-only do orçamento identificado por token UUID.

    Sem autenticação: seguro pois o modelo só contém dados públicos (T-fma-01).
    Token inexistente devolve 404 (T-fma-02).
    """
    orcamento_obj = OrcamentoQuery.by_token(token)
    if orcamento_obj is None:
        raise Http404
    dados = OrcamentoMapper.to_public(orcamento_obj)
    return render(request, "calculator/orcamento_publico.html", {"orc": dados})


def orcamento_pdf(request, token):
    """PDF público do orçamento identificado por token UUID.

    Sem autenticação: seguro pois o modelo só contém dados públicos (T-fma-01).
    Reconstrói o dict que gerar_orcamento_pdf espera, convertendo Decimal->float.
    Token inexistente devolve 404 (T-fma-02).
    """
    from .pdf import gerar_orcamento_pdf

    orcamento_obj = OrcamentoQuery.by_token(token)
    if orcamento_obj is None:
        raise Http404

    # rebuild do dict público a partir dos dados persistidos; Decimal -> float para pdf.py
    dados_pdf = {
        "cliente_nome":   orcamento_obj.cliente_nome,
        "peca_descricao": orcamento_obj.peca_descricao,
        "quantidade":     int(orcamento_obj.quantidade),
        "prazo_entrega":  orcamento_obj.prazo_entrega,
        "observacoes":    orcamento_obj.observacoes,
        "preco_venda":    float(orcamento_obj.preco_venda),
        "total":          float(orcamento_obj.total),
    }

    pdf_bytes = gerar_orcamento_pdf(dados_pdf)
    nome_arquivo = orcamento_obj.cliente_nome.lower().replace(" ", "-")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="orcamento-{nome_arquivo}.pdf"'
    )
    return response
