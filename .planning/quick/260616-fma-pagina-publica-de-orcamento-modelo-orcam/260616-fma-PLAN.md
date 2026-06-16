---
phase: quick-260616-fma
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/calculator/models.py
  - apps/calculator/migrations/__init__.py
  - apps/calculator/migrations/0001_initial.py
  - apps/calculator/services.py
  - apps/calculator/mappers.py
  - apps/calculator/queries.py
  - apps/calculator/views.py
  - apps/calculator/urls.py
  - apps/calculator/admin.py
  - apps/calculator/templates/calculator/orcamento.html
  - apps/calculator/templates/calculator/orcamento_publico.html
autonomous: true
requirements: [QUICK-260616-FMA]
must_haves:
  truths:
    - "Ao gerar um orçamento (staff POST), o orçamento é persistido com um token UUID e a página do staff mostra um link público compartilhável copiável + botão de baixar PDF"
    - "Qualquer pessoa (sem login) abre /calculadora/orcamento/<token>/ e vê uma página read-only elegante com os dados do orçamento (cliente, peça, qtd, prazo, preço unitário, total, condições)"
    - "A página pública e a rota /pdf/ NÃO expõem nenhum custo interno (material, energia, depreciação, mão de obra, subtotal, margem, taxa de falha)"
    - "A rota /calculadora/orcamento/<token>/pdf/ devolve um PDF (%PDF) gerado a partir dos dados PERSISTIDOS"
    - "Token inexistente devolve 404 nas rotas pública e pdf"
  artifacts:
    - path: "apps/calculator/models.py"
      provides: "Modelo Orcamento (TimeStampedModel) com SOMENTE dados públicos + token UUID"
      contains: "class Orcamento"
    - path: "apps/calculator/migrations/0001_initial.py"
      provides: "Migração inicial da tabela orcamento"
      contains: "Orcamento"
    - path: "apps/calculator/services.py"
      provides: "OrcamentoService.criar — única camada que escreve no DB, @transaction.atomic"
      contains: "class OrcamentoService"
    - path: "apps/calculator/mappers.py"
      provides: "OrcamentoMapper.to_public — Model->dict display-ready, allowlist pública"
      contains: "class OrcamentoMapper"
    - path: "apps/calculator/queries.py"
      provides: "OrcamentoQuery.by_token — leitura read-only por token"
      contains: "by_token"
    - path: "apps/calculator/templates/calculator/orcamento_publico.html"
      provides: "Página pública read-only com identidade L3D"
      min_lines: 40
  key_links:
    - from: "apps/calculator/views.py (orcamento POST)"
      to: "OrcamentoService.criar"
      via: "persiste dados públicos e obtém token"
      pattern: "OrcamentoService\\.criar"
    - from: "apps/calculator/views.py (orcamento_publico / orcamento_pdf)"
      to: "OrcamentoQuery.by_token"
      via: "leitura por token"
      pattern: "OrcamentoQuery\\.by_token"
    - from: "apps/calculator/views.py (orcamento_pdf)"
      to: "gerar_orcamento_pdf"
      via: "rebuild do dict público a partir do model persistido"
      pattern: "gerar_orcamento_pdf"
---

<objective>
Persistir o orçamento gerado pela calculadora staff e expor um link público read-only
compartilhável (HTML + PDF) que o cliente abre no navegador, sem login.

Purpose: hoje o orçamento só existe como download de PDF efêmero. O cliente precisa de um
link estável e bonito para visualizar/aprovar; o staff precisa de um link copiável para enviar.

Output: modelo `Orcamento` (só dados públicos), service de escrita, query/mapper de leitura,
duas rotas públicas (HTML + PDF) por token UUID, página pública elegante e a página do staff
mostrando o link gerado. Segurança: nenhuma camada expõe custos internos (espelha a allowlist
da trava do pdf.py — os 7 campos públicos).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@apps/calculator/views.py
@apps/calculator/services.py
@apps/calculator/forms.py
@apps/calculator/pdf.py
@apps/calculator/mappers.py
@apps/calculator/urls.py
@apps/calculator/admin.py
@apps/core/models.py
@apps/core/layers.py
@apps/core/formatting.py
@apps/calculator/templates/calculator/orcamento.html

<interfaces>
Allowlist PÚBLICA (os ÚNICOS campos que podem sair de qualquer camada — espelha pdf.py linhas 6-18):
  cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes, preco_venda, total
PROIBIDO em model/mapper/template/rota: custo_material, custo_energia, custo_depreciacao,
  custo_maoobra, subtotal, ajuste_falha, custo_total, taxa_falha_pct, margem_pct.

apps/core/models.py:
  class TimeStampedModel(models.Model)  # abstract; created_at, updated_at; ordering ["-created_at"]

apps/core/layers.py:
  class BaseMapper(Generic[M]): classmethod to_dict(cls, instance) -> dict; to_list(...)
  class BaseService  # marcador
  class BaseQuery    # marcador

apps/core/formatting.py:
  def format_brl(value: Decimal | float | int | None) -> str   # aceita Decimal; None -> "—"

apps/calculator/pdf.py:
  def gerar_orcamento_pdf(dados: dict) -> bytes
    # dados deve conter SOMENTE: cliente_nome, peca_descricao, quantidade(int),
    #   prazo_entrega(str), observacoes(str), preco_venda(float), total(float)
    # internamente usa _format_brl que espera float -> converter Decimal->float no rebuild

apps/calculator/views.py (estado atual, a alterar):
  orcamento(request)  # @user_passes_test(is_staff); POST hoje devolve HttpResponse(pdf, application/pdf)
    # já monta dados_pdf com EXATAMENTE os 7 campos públicos (linhas 52-60)

settings.SITE = {"name","tagline","accent","instagram"}  # instagram = https://instagram.com/l3d_labz
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Modelo Orcamento + migração inicial + service de escrita + query/mapper de leitura</name>
  <files>apps/calculator/models.py, apps/calculator/migrations/__init__.py, apps/calculator/migrations/0001_initial.py, apps/calculator/services.py, apps/calculator/mappers.py, apps/calculator/queries.py</files>
  <action>
Criar o modelo de persistência e as camadas de leitura/escrita seguindo a arquitetura em camadas (CLAUDE.md). Copy/labels/verbose_name em pt-br.

1. apps/calculator/models.py (NOVO): class Orcamento(TimeStampedModel) herdando de apps.core.models.TimeStampedModel (import absoluto). Docstring de módulo pt-br explicando que o modelo guarda SOMENTE dados públicos (espelho da trava do pdf.py), NUNCA custos internos. Campos (verbose_name pt-br como primeiro argumento, padrão do projeto):
   - token: models.UUIDField com default=uuid.uuid4, unique=True, editable=False, db_index=True (import uuid no topo). verbose_name "token público".
   - cliente_nome: CharField max_length=120, verbose_name "nome do cliente".
   - peca_descricao: CharField max_length=240, verbose_name "descrição da peça".
   - quantidade: PositiveIntegerField default=1, verbose_name "quantidade".
   - prazo_entrega: CharField max_length=80, verbose_name "prazo de entrega".
   - observacoes: TextField blank=True, default="", verbose_name "observações".
   - preco_venda: DecimalField max_digits=10, decimal_places=2, verbose_name "preço unitário".
   - total: DecimalField max_digits=12, decimal_places=2, verbose_name "total".
   - class Meta com verbose_name "orçamento", verbose_name_plural "orçamentos" (NÃO redefinir ordering — herda "-created_at"; se redefinir, manter ["-created_at"]).
   - __str__ retornando algo como "Orçamento {cliente_nome} — {token}".
   NÃO adicionar nenhum campo de custo interno nem property que derive de custos.

2. apps/calculator/migrations/__init__.py (NOVO): arquivo vazio (a app ainda não tem o pacote migrations).

3. apps/calculator/migrations/0001_initial.py: gerar via makemigrations (NÃO escrever à mão). Conferir que cria a tabela Orcamento com os 8 campos acima + created_at/updated_at.

4. apps/calculator/queries.py (NOVO): docstring pt-br. class OrcamentoQuery(BaseQuery) (import absoluto from apps.core.layers import BaseQuery; import relativo from .models import Orcamento). Método estático by_token(token) que retorna Orcamento.objects.filter(token=token).first() (Orcamento | None). Só ORM, sem regra de negócio, sem cache (orçamento é dado individual/mutável), sem HTTP.

5. apps/calculator/services.py (EDITAR — adicionar, NÃO remover PricingService): adicionar imports from django.db import transaction e from .models import Orcamento (Decimal já está importado). Criar class OrcamentoService(BaseService) com método estático e @transaction.atomic criar(*, cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes, preco_venda, total) -> Orcamento: recebe SOMENTE os 7 campos públicos (keyword-only), converte preco_venda/total para Decimal (usar o helper _d existente ou Decimal(str(...))) e cria via Orcamento.objects.create(...), retornando a instância. Docstring pt-br deixando explícito que NÃO recebe custos internos. É a ÚNICA camada que escreve no DB.

6. apps/calculator/mappers.py (EDITAR — adicionar, NÃO remover PricingMapper): adicionar class OrcamentoMapper(BaseMapper) com _CAMPOS_PUBLICOS (tuple documentando a allowlist); to_dict(cls, instance) delegando a to_public (satisfaz o contrato abstrato); to_public(cls, orcamento) -> dict retornando APENAS: token (str(orcamento.token)), cliente_nome, peca_descricao, quantidade (int), prazo_entrega, observacoes, preco_venda_display (format_brl(orcamento.preco_venda)), total_display (format_brl(orcamento.total)), created_at (orcamento.created_at). NUNCA incluir custos internos. format_brl já é importado no arquivo.
  </action>
  <verify>
    <automated>cd "C:/dev/l3d-labz-site" && python manage.py makemigrations calculator --noinput && python manage.py migrate calculator --noinput && python manage.py shell -c "from apps.calculator.services import OrcamentoService; from apps.calculator.mappers import OrcamentoMapper; from apps.calculator.queries import OrcamentoQuery; o=OrcamentoService.criar(cliente_nome='Maria Teste', peca_descricao='Vaso geometrico', quantidade=2, prazo_entrega='3 dias uteis', observacoes='entregar verde', preco_venda='51.69', total='103.38'); d=OrcamentoMapper.to_public(o); assert d['total_display']=='R$ 103,38', d; assert 'custo_material' not in d and 'margem_pct' not in d and 'subtotal' not in d; assert OrcamentoQuery.by_token(o.token).id==o.id; print('OK', d)"</automated>
  </verify>
  <done>Migração aplicada; criar um Orcamento via OrcamentoService funciona, OrcamentoMapper.to_public devolve só os campos públicos (sem custos internos) com valores BRL, e OrcamentoQuery.by_token recupera a instância.</done>
</task>

<task type="auto">
  <name>Task 2: Rotas públicas (HTML + PDF) por token, views finas, e wire do staff POST para persistir + mostrar link</name>
  <files>apps/calculator/urls.py, apps/calculator/views.py</files>
  <action>
1. apps/calculator/urls.py (EDITAR): adicionar DUAS rotas públicas (sem auth). Como a rota staff é "orcamento/" (bare) e as públicas têm <uuid:token>, não há conflito. Adicionar:
   - path("orcamento/<uuid:token>/", views.orcamento_publico, name="orcamento_publico")
   - path("orcamento/<uuid:token>/pdf/", views.orcamento_pdf, name="orcamento_pdf")
   Manter as rotas existentes ("" publica, "orcamento/" orcamento).

2. apps/calculator/views.py (EDITAR):
   a) Alterar a view orcamento (staff POST): após calcular resultado e montar o dict de 7 campos públicos (dados_pdf, linhas 52-60), em vez de devolver o PDF como download, PERSISTIR via service e re-renderizar a página do staff com o link. Adicionar OrcamentoService ao import de .services; importar reverse de django.urls. Substituir o bloco que gera/retorna o PDF por:
      - orcamento_obj = OrcamentoService.criar(**dados_pdf)  (dados_pdf já tem EXATAMENTE os 7 campos públicos — reaproveitar).
      - link_publico = request.build_absolute_uri(reverse("calculator:orcamento_publico", args=[orcamento_obj.token]))
      - link_pdf = request.build_absolute_uri(reverse("calculator:orcamento_pdf", args=[orcamento_obj.token]))
      - render de "calculator/orcamento.html" com contexto {form, presets_json(), orcamento_gerado: {link_publico, link_pdf, cliente_nome: orcamento_obj.cliente_nome}}.
      Remover a geração/download direto do PDF do fluxo staff (o PDF agora é servido pela rota pública /pdf/). Manter o gate @user_passes_test(lambda u: u.is_staff). NÃO quebrar o GET (form vazio).

   b) Adicionar def orcamento_publico(request, token): SEM decorator de auth (público). Fina: busca via OrcamentoQuery.by_token(token); se None -> raise Http404; senão dados = OrcamentoMapper.to_public(orcamento_obj) e render de "calculator/orcamento_publico.html" com {"orc": dados}. Imports: from django.http import Http404, from .queries import OrcamentoQuery, from .mappers import OrcamentoMapper.

   c) Adicionar def orcamento_pdf(request, token): SEM auth (público; seguro pois o modelo só tem dados públicos). Fina: busca via OrcamentoQuery.by_token(token); None -> Http404. Reconstruir o dict PÚBLICO que gerar_orcamento_pdf espera, convertendo Decimal->float (pdf.py usa _format_brl que espera float): {cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes, preco_venda: float(o.preco_venda), total: float(o.total)}. from .pdf import gerar_orcamento_pdf; pdf_bytes = gerar_orcamento_pdf(dados). Retornar HttpResponse(pdf_bytes, content_type="application/pdf") com Content-Disposition inline; filename derivado do cliente_nome (mesmo slug do código anterior: lower + espaços->hifens). Manter o import de HttpResponse.

   Atualizar a docstring do módulo views para refletir as 3 novas rotas/comportamento.
  </action>
  <verify>
    <automated>cd "C:/dev/l3d-labz-site" && python manage.py shell -c "from django.test import Client; from apps.calculator.models import Orcamento; o=Orcamento.objects.create(cliente_nome='Joao Verify', peca_descricao='Suporte de fone', quantidade=3, prazo_entrega='5 dias uteis', observacoes='cor azul', preco_venda='40.00', total='120.00'); c=Client(); r=c.get(f'/calculadora/orcamento/{o.token}/'); assert r.status_code==200, r.status_code; html=r.content.decode('utf-8'); assert 'Joao Verify' in html and 'Suporte de fone' in html and 'R$ 120,00' in html; banned=['custo_material','custo_energia','custo_depreciacao','custo_maoobra','subtotal','ajuste_falha','custo_total','taxa_falha','margem']; leaked=[b for b in banned if b in html.lower()]; assert not leaked, leaked; p=c.get(f'/calculadora/orcamento/{o.token}/pdf/'); assert p.status_code==200 and p['Content-Type']=='application/pdf' and p.content[:4]==b'%PDF', (p.status_code, p['Content-Type'], p.content[:4]); import uuid as _u; nf=c.get(f'/calculadora/orcamento/{_u.uuid4()}/'); assert nf.status_code==404, nf.status_code; print('OK publico+pdf+404 sem vazamento')"</automated>
  </verify>
  <done>GET na URL pública (200) mostra os dados do orçamento e nenhum termo de custo interno; rota /pdf/ devolve %PDF (application/pdf); token inexistente devolve 404; o staff POST persiste e re-renderiza a página com o link.</done>
</task>

<task type="auto">
  <name>Task 3: Template público read-only elegante + bloco de link no template staff + registro no admin</name>
  <files>apps/calculator/templates/calculator/orcamento_publico.html, apps/calculator/templates/calculator/orcamento.html, apps/calculator/admin.py</files>
  <action>
1. apps/calculator/templates/calculator/orcamento_publico.html (NOVO): página pública read-only, {% extends "base.html" %}, copy pt-br, usando os design tokens do tema (static/css/theme.css — usar var(--accent), var(--bg-card), var(--border), var(--text), var(--text-muted), var(--radius) etc.; NÃO inventar tokens novos). Consome o dict orc (de OrcamentoMapper.to_public) — NÃO acessar o model cru. Espelhar o visual do PDF/marca:
   - {% block title %}Orçamento {{ orc.cliente_nome }} — L3D Labz{% endblock %}
   - Header com a marca (monograma/nome L3D em verde) e a palavra "Orçamento" (faixa/destaque verde, nome {{ SITE.name }}).
   - Bloco "Faturar para": {{ orc.cliente_nome }}; emissão = {{ orc.created_at|date:"d/m/Y" }}; prazo = {{ orc.prazo_entrega }}.
   - Linha de item: descrição {{ orc.peca_descricao }}, quantidade {{ orc.quantidade }}, preço unit. {{ orc.preco_venda_display }}, total {{ orc.total_display }}.
   - TOTAL em destaque (card grande, verde): {{ orc.total_display }}.
   - Bloco "Condições & observações": se orc.observacoes -> mostrar; sempre mostrar "Sinal de 50% para iniciar a produção, saldo na entrega." e "Validade de 7 dias corridos a partir da emissão. Valores em reais (BRL)." (espelha o PDF).
   - Ações: botão "Baixar PDF" -> {% url 'calculator:orcamento_pdf' orc.token %} (target=_blank) e CTA "Aprovar via Instagram" -> {{ SITE.instagram }} ({% if SITE.instagram %}), com @l3d_labz no texto.
   - PROIBIDO: qualquer custo interno, qualquer campo fora de orc. Sem form, sem login. Mobile-first (tema já é responsivo).

2. apps/calculator/templates/calculator/orcamento.html (EDITAR): no topo do {% block content %} (logo após .page-head, antes do <form>), adicionar bloco condicional {% if orcamento_gerado %} mostrando um card de sucesso com:
   - título "Orçamento gerado para {{ orcamento_gerado.cliente_nome }}".
   - input de texto readonly com value {{ orcamento_gerado.link_publico }} + botão "Copiar link" (onclick mínimo vanilla navigator.clipboard.writeText, padrão do projeto). O link copiável é o link_publico.
   - link/botão "Abrir página pública" (href link_publico, target=_blank) e "Baixar PDF" (href {{ orcamento_gerado.link_pdf }}, target=_blank).
   Usar classes/tokens existentes (.card, .btn, .btn-primary). Copy pt-br. NÃO remover o form. O bloco só aparece após POST bem-sucedido.

3. apps/calculator/admin.py (REESCREVER — hoje só comenta que não há models): registrar Orcamento read-only-ish.
   - from django.contrib import admin; from .models import Orcamento.
   - @admin.register(Orcamento) class OrcamentoAdmin(admin.ModelAdmin) com:
     list_display = ("token", "cliente_nome", "peca_descricao", "quantidade", "total", "created_at")
     search_fields = ("cliente_nome", "peca_descricao", "token")
     readonly_fields = ("token", "created_at", "updated_at")
     list_filter = ("created_at",)
     ordering = ("-created_at",)
   Não expor custos (o model não os tem). Docstring pt-br.
  </action>
  <verify>
    <automated>cd "C:/dev/l3d-labz-site" && python manage.py check && python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from django.template.loader import get_template; get_template('calculator/orcamento_publico.html'); get_template('calculator/orcamento.html'); from django.contrib import admin; from apps.calculator.models import Orcamento; assert admin.site.is_registered(Orcamento); print('templates+admin OK')"</automated>
  </verify>
  <done>Template público renderiza com os dados de orc e os CTAs (PDF + Instagram); a página staff mostra o card com link copiável após gerar; Orcamento aparece registrado no admin com list_display de token/cliente/total/created. `manage.py check` sem erros.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| visitante anônimo → rotas públicas /orcamento/<token>/ e /pdf/ | qualquer pessoa com o link acessa; sem auth por design |
| staff POST → persistência | dado de cliente entra no DB via service |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-fma-01 | Information Disclosure | modelo Orcamento / OrcamentoMapper.to_public / template público / rota /pdf/ | mitigate | O modelo NUNCA persiste custos internos (espelha a allowlist do pdf.py); mapper e template só consomem os 7 campos públicos; verify do Task 2 faz allowlist negativa (grep dos termos custo_*/subtotal/margem/taxa_falha no HTML servido) |
| T-fma-02 | Information Disclosure | enumeração de tokens | accept | token é UUID4 (122 bits de entropia) — não enumerável; rotas devolvem 404 para token inexistente (verificado) |
| T-fma-03 | Elevation of Privilege | geração de orçamento | mitigate | a criação permanece atrás de @user_passes_test(is_staff); rotas públicas são read-only (GET), nenhuma escrita exposta sem auth |
| T-fma-SC | Tampering | npm/pip/cargo installs | accept | nenhuma dependência nova (reusa Django/reportlab já presentes) |
</threat_model>

<verification>
1. makemigrations + migrate criam a tabela Orcamento (Task 1).
2. OrcamentoService.criar persiste; OrcamentoMapper.to_public devolve só campos públicos; OrcamentoQuery.by_token recupera (Task 1).
3. GET /calculadora/orcamento/<token>/ = 200 com os dados, sem nenhum termo de custo interno (allowlist negativa); GET .../pdf/ = %PDF; token inexistente = 404 (Task 2).
4. Templates carregam, admin registrado, manage.py check limpo (Task 3).
5. Verificação no browser (orquestrador, Playwright): gerar orçamento como staff → copiar link → abrir a página pública anônima → conferir render bonito + botão PDF + CTA Instagram; confirmar visualmente que nenhum custo interno aparece.
</verification>

<success_criteria>
- Modelo Orcamento existe e persiste SOMENTE os 7 campos públicos + token UUID.
- Escrita só via OrcamentoService.criar (@transaction.atomic); leitura via OrcamentoQuery.by_token; Model→dict via OrcamentoMapper.to_public.
- Rotas /calculadora/orcamento/<token>/ (HTML) e /.../pdf/ (PDF) funcionam sem login; token inexistente = 404.
- Página pública elegante com identidade L3D, total em destaque, condições 50/50, botão PDF e CTA Instagram; nenhum custo interno em nenhuma camada.
- Página staff (POST) persiste e exibe o link público copiável + botão PDF; gate is_staff mantido.
- Orcamento registrado no admin (token/cliente/peça/qtd/total/created), read-only-ish.
- Copy pt-br em tudo; Decimal para dinheiro no modelo.
</success_criteria>

<output>
Create `.planning/quick/260616-fma-pagina-publica-de-orcamento-modelo-orcam/260616-fma-SUMMARY.md` when done
</output>
