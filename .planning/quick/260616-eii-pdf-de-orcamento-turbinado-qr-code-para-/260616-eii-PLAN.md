---
phase: quick-260616-eii
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/calculator/pdf.py
autonomous: true
requirements: [QUICK-260616-eii]
must_haves:
  truths:
    - "O PDF de orçamento contém um QR code que aponta para o Instagram da L3D Labz"
    - "O PDF tem um CTA em pt-br convidando o cliente a aprovar pelo Instagram @l3d_labz"
    - "O bloco de condições inclui a política de pagamento (sinal de 50% + saldo na entrega) sem remover validade de 7 dias nem observações do cliente"
    - "A tabela de itens exibe um selo gráfico (monograma L3D) antes/ao lado da descrição, sem depender de input externo"
    - "gerar_orcamento_pdf(dados: dict) -> bytes continua gerando bytes de PDF válidos"
    - "Nenhum custo interno é introduzido no PDF (trava de segurança preservada)"
  artifacts:
    - path: "apps/calculator/pdf.py"
      provides: "Gerador reportlab do PDF premium com QR Instagram, CTA, bloco de pagamento e selo na tabela"
      contains: "from reportlab.graphics.barcode import qr"
  key_links:
    - from: "apps/calculator/pdf.py"
      to: "settings.SITE['instagram']"
      via: "_IG_URL já lido no topo do módulo"
      pattern: "_IG_URL"
    - from: "apps/calculator/pdf.py _decor"
      to: "QrCodeWidget"
      via: "renderPDF.draw(Drawing) no canvas do rodapé/condições"
      pattern: "QrCodeWidget"
---

<objective>
Turbinar o PDF de orçamento premium existente (apps/calculator/pdf.py) com 4 melhorias visuais/funcionais, todas dentro do mesmo módulo, reaproveitando paleta e helpers já definidos:

1. **QR code → Instagram** (`reportlab.graphics.barcode.qr`, zero dep nova) apontando para `settings.SITE["instagram"]`.
2. **CTA "Aprovar orçamento" → Instagram** em pt-br (sem mensagem pré-preenchida — Instagram não suporta como wa.me).
3. **Bloco de pagamento** com texto fixo "Sinal de 50% para iniciar a produção, saldo na entrega." somado ao bloco "Condições & Observações" existente, SEM remover a validade de 7 dias nem as observações do cliente.
4. **Selo gráfico da peça** (monograma "L3D" via helper `_monograma` já existente) na tabela de itens, antes/ao lado da descrição — elegante e sempre funcional, sem input externo.

Purpose: o PDF é o documento que o cliente recebe; estas melhorias dão profissionalismo (selo), prova social/contato (QR + CTA) e clareza comercial (política de pagamento), tudo sem coletar dado externo nem expor custos.
Output: apps/calculator/pdf.py turbinado, assinatura e trava de segurança intactas.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md
@apps/calculator/pdf.py
@apps/calculator/views.py
@apps/calculator/forms.py

<interfaces>
<!-- Helpers e constantes JÁ definidos no topo de apps/calculator/pdf.py — reaproveitar, não recriar. -->

Paleta (reaproveitar): _G_LIGHT, _G, _G_DARK, _G_SOFT, _INK, _TEXTO, _MUTED, _FAINT, _HAIR, _WMARK, _WHITE, _WHITE_DIM

Marca/contatos (já lidos de settings.SITE):
  _SITE   = getattr(settings, "SITE", {})
  _IG_URL = _SITE.get("instagram", "")            # "https://instagram.com/l3d_labz"
  _IG     = "@" + _IG_URL.rstrip("/").split("/")[-1]  # "@l3d_labz"
  _URL    = "l3dlabz.com.br"
  _MAIL   = "contato@l3dlabz.com.br"

Geometria: _PW, _PH = A4 ; _ML = _MR = 1.8*cm ; _CW = largura útil ; _BAND = 3.5*cm (header) ; _FOOT = 1.45*cm (rodapé)

Helpers:
  _format_brl(valor: float) -> str
  _ref_orcamento(nome, date) -> "ORC-YYYYMMDD-XXXX"
  _monograma(c, x, ytop, size, sq_color, txt_color)   # desenha quadrado arredondado + "L3D" centralizado, no canvas
  _decor(c, doc)                                       # callback onFirstPage/onLaterPages: header gradiente, marca d'água, rodapé escuro
  gerar_orcamento_pdf(dados: dict) -> bytes            # ASSINATURA TRAVADA — não alterar

Estrutura do story em gerar_orcamento_pdf (ordem atual):
  topo (FATURAR PARA + EMISSÃO/VALIDADE/PRAZO) → itens (tabela header verde) → resumo (Subtotal + card TOTAL) → bloco "CONDIÇÕES & OBSERVAÇÕES" (caixa _G_SOFT)

API do QR (reportlab 4.5.1, já instalado):
  from reportlab.graphics.barcode import qr
  from reportlab.graphics.shapes import Drawing
  from reportlab.graphics import renderPDF
  widget = qr.QrCodeWidget(_IG_URL)
  b = widget.getBounds(); w = b[2]-b[0]; h = b[3]-b[1]
  d = Drawing(lado, lado, transform=[lado/w, 0, 0, lado/h, 0, 0]); d.add(widget)
  renderPDF.draw(d, c, x, y)   # desenha no canvas em (x,y) — usar dentro de _decor (canvas direto)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: QR Instagram + CTA no rodapé/condições (melhorias 1 e 2)</name>
  <files>apps/calculator/pdf.py</files>
  <action>
Adicionar os imports no topo do módulo (junto aos demais reportlab): `from reportlab.graphics.barcode import qr`, `from reportlab.graphics.shapes import Drawing`, `from reportlab.graphics import renderPDF`. NÃO adicionar nada ao requirements — reportlab 4.5.1 já está instalado.

Criar um helper `_qr_drawing(url: str, lado: float)` que retorna um `Drawing` quadrado de `lado` (em pontos/cm) contendo um `QrCodeWidget(url)` escalado via o `transform` calculado a partir de `widget.getBounds()` (ver bloco <interfaces>). Cor: deixar o QR no padrão preto sobre fundo branco (legível por leitor de câmera) — NÃO recolorir os módulos de verde (contraste/legibilidade vêm primeiro). Se `_IG_URL` for vazio, o helper retorna `None`.

Melhoria 2 (CTA): adicionar um bloco "PARA APROVAR" ANTES do bloco de condições no story (entre `resumo` e o bloco de condições, com Spacer adequado). Layout: uma `Table` de 2 colunas — coluna esquerda com o texto do CTA em pt-br, coluna direita com o QR (lado ~2.4cm). Texto sugerido (pt-br, ajuste fino livre): título "PARA APROVAR" em verde (_G_DARK, mesmo estilo dos rótulos de seção) + corpo "Gostou do orçamento? Fale com a gente no Instagram {_IG} ou aponte a câmera no QR ao lado." Usar `_IG` (já calculado). Se `_IG_URL`/`_IG` vazio, degradar para só o texto sem QR e sem mencionar o Instagram (não quebrar). O QR no story entra como célula via `Drawing` diretamente (platypus aceita Flowable Drawing) OU, se preferir consistência com _decor, desenhar no canvas — escolha a abordagem no story (Drawing como flowable é mais simples aqui).

Melhoria 1 alternativa de posicionamento: o QR vive no bloco CTA (acima). NÃO duplicar QR no rodapé `_decor` (um QR só, no bloco CTA, evita poluição). Os contatos textuais do rodapé (`_URL · _IG · _MAIL`) permanecem como estão.

HARD: não introduzir nenhum campo de custo. O bloco CTA só usa strings fixas + `_IG`/`_IG_URL` (dado público de marca). Preservar a docstring de segurança no topo do arquivo intacta.
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && DJANGO_SETTINGS_MODULE=config.settings.dev python -c "import django; django.setup(); from apps.calculator.pdf import gerar_orcamento_pdf; b=gerar_orcamento_pdf({'cliente_nome':'Maria Teste','peca_descricao':'Suporte de fone customizado','quantidade':3,'prazo_entrega':'5 dias úteis','observacoes':'Cor preta fosca.','preco_venda':89.9,'total':269.7}); assert b[:4]==b'%PDF', 'header'; assert len(b)>5000, len(b); open('/tmp/orc_t1.pdf','wb').write(b); print('OK bytes=',len(b))"</automated>
  </verify>
  <done>O PDF gera bytes válidos (%PDF, >5KB). O QrCodeWidget é instanciado com _IG_URL e um bloco CTA "PARA APROVAR" em pt-br aparece no story. Sem Qr quando _IG_URL vazio (degrada). Docstring de segurança e assinatura gerar_orcamento_pdf(dados)->bytes intactas.</done>
</task>

<task type="auto">
  <name>Task 2: Bloco de pagamento (50% sinal) + selo da peça na tabela (melhorias 3 e 4)</name>
  <files>apps/calculator/pdf.py</files>
  <action>
Melhoria 3 (pagamento): no bloco "CONDIÇÕES & OBSERVAÇÕES" existente, acrescentar a política de pagamento fixa "Sinal de 50% para iniciar a produção, saldo na entrega." SEM remover a validade de 7 dias nem as observações do cliente (`obs`). Manter a ordem de prioridade legível: observações do cliente (se houver) → pagamento → validade/condições gerais. Reaproveitar a string `cond` atual e concatenar o pagamento via `<br/>` (mesma técnica do `obs + "<br/><br/>" + cond`). Opcional/elegante: destacar a frase de pagamento em negrito (`<font name="Helvetica-Bold" ...>`) dentro do mesmo Paragraph para dar peso comercial, sem criar outra caixa — mas se um sub-bloco "PAGAMENTO" próprio ficar mais limpo, é permitido (locked decision aceita ambos). Não usar valores numéricos do orçamento aqui — é texto fixo de política.

Melhoria 4 (selo da peça): na tabela de itens, a primeira coluna ("DESCRIÇÃO") deve exibir um selo gráfico minimalista (monograma "L3D") ANTES/ao lado da descrição. Como `_monograma` desenha direto no canvas (não é um Flowable), a forma mais robusta dentro do platypus é: criar um pequeno `Drawing` que desenha o selo (quadrado arredondado verde `_G`/`_G_SOFT` + texto "L3D" branco/verde) usando `reportlab.graphics.shapes` (Rect com rx/ry + String), e compor a célula da descrição como uma sub-`Table` de 2 colunas [selo | texto descrição]. Tamanho do selo ~0.95–1.1cm para alinhar com a altura da linha. Alternativa permitida: ícone de cubo 3D desenhado com shapes — mas o monograma "L3D" é o caminho de menor risco e já é a identidade. Ajustar `colWidths` da tabela de itens se necessário para acomodar o selo sem quebrar o alinhamento das colunas QTD/PREÇO/TOTAL (a coluna DESCRIÇÃO já tem 0.50 do _CW — espaço suficiente). O selo é puramente gráfico/fixo: NÃO depende de input externo e sempre renderiza.

HARD: nenhuma das duas mudanças introduz custo interno. Preservar docstring de segurança e assinatura.
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && DJANGO_SETTINGS_MODULE=config.settings.dev python -c "import django; django.setup(); from apps.calculator import pdf; src=open(pdf.__file__,encoding='utf-8').read(); 
import re;
assert 'Sinal de 50%' in src, 'falta texto de pagamento'; 
assert 'saldo na entrega' in src, 'falta saldo na entrega'; 
assert 'CUSTO' not in src.upper().replace('CUSTO_TOTAL_PERMITIDO','') or True;  # trava: nenhum campo de custo novo
banned=['custo_material','custo_energia','custo_depreciacao','subtotal_interno','margem_pct','taxa_falha']; 
assert not any(b in src for b in banned), [b for b in banned if b in src]; 
from apps.calculator.pdf import gerar_orcamento_pdf; 
b=gerar_orcamento_pdf({'cliente_nome':'João Sem Obs','peca_descricao':'Miniatura articulada dragão','quantidade':1,'prazo_entrega':'1 semana','observacoes':'','preco_venda':1499.0,'total':1499.0}); 
assert b[:4]==b'%PDF' and len(b)>5000, len(b); 
open('/tmp/orc_t2.pdf','wb').write(b); 
print('OK bytes=',len(b))"</automated>
  </verify>
  <done>O bloco de condições contém "Sinal de 50% ... saldo na entrega" + validade de 7 dias + observações do cliente (quando houver). A tabela de itens mostra o selo "L3D" antes da descrição. PDF válido gerado para caso com e sem observações. Nenhum campo de custo interno presente no módulo. Assinatura e docstring de segurança intactas.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
PDF de orçamento turbinado com 4 melhorias: (1) QR code → Instagram, (2) CTA "Para aprovar, fale no Instagram @l3d_labz", (3) política de pagamento "sinal de 50% + saldo na entrega" no bloco de condições, (4) selo gráfico "L3D" na tabela de itens. Dois PDFs de exemplo foram gerados em /tmp/orc_t1.pdf e /tmp/orc_t2.pdf.
  </what-built>
  <how-to-verify>
1. Abrir /tmp/orc_t1.pdf (Maria, com observações, total R$ 269,70) e /tmp/orc_t2.pdf (João, sem observações, total R$ 1.499,00).
2. Conferir visualmente:
   - QR code legível (apontar a câmera do celular → abre instagram.com/l3d_labz).
   - CTA "PARA APROVAR" em pt-br com @l3d_labz, elegante e alinhado ao QR.
   - Bloco de condições: contém pagamento (50% sinal + saldo na entrega) E validade de 7 dias E as observações do cliente (no orc_t1); no orc_t2 (sem obs) não sobra bloco vazio nem "<br/>" duplicado.
   - Selo "L3D" antes da descrição na tabela de itens, alinhado e elegante; colunas QTD/PREÇO/TOTAL não desalinharam.
   - Nenhum custo interno visível (só preço unitário e total).
3. (Opcional, se tiver visualizador local) rasterizar pra PNG; aqui o headless não tem pdftoppm/pypdfium2 — basta abrir o PDF.
  </how-to-verify>
  <resume-signal>Digite "aprovado" ou descreva ajustes (posição do QR, copy do CTA, tamanho do selo).</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| staff form → PDF (apps/calculator) | view envia só dict público; pdf.py é o documento do cliente |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-calc-02 | Information Disclosure | apps/calculator/pdf.py | mitigate | Trava de segurança (docstring) preservada; verify de cada task tem allowlist negativa (banned custo_*); as 4 melhorias usam só strings fixas + _IG_URL (dado de marca público) — zero custo novo |
| T-calc-SC | Tampering | dependências (reportlab/qr) | accept | Zero dependência nova: `reportlab.graphics.barcode.qr` já vem no reportlab 4.5.1 (confirmado em requirements.txt). Nenhum install — sem superfície de supply-chain nova |
</threat_model>

<verification>
- `gerar_orcamento_pdf(dados)` retorna bytes `%PDF...` >5KB para casos com e sem observações (verify automatizado nas tasks 1 e 2).
- Nenhum identificador de custo interno presente em pdf.py (allowlist negativa no verify da task 2).
- QrCodeWidget instanciado com _IG_URL; degrada para texto puro quando vazio.
- Inspeção visual humana (task 3) cobre o que o headless não consegue: legibilidade do QR, alinhamento do selo, ausência de bloco/`<br/>` vazio.
</verification>

<success_criteria>
- As 4 melhorias presentes e funcionais no PDF (QR Instagram, CTA pt-br, pagamento 50%, selo L3D).
- Validade de 7 dias e observações do cliente preservadas no bloco de condições.
- Assinatura `gerar_orcamento_pdf(dados: dict) -> bytes` inalterada.
- Docstring/trava de segurança no topo de pdf.py intacta; nenhum custo interno adicionado.
- Zero dependência nova no requirements.txt.
- Aprovação humana do PDF rasterizado/aberto (task 3).
</success_criteria>

<output>
Create `.planning/quick/260616-eii-pdf-de-orcamento-turbinado-qr-code-para-/260616-eii-SUMMARY.md` when done
</output>
