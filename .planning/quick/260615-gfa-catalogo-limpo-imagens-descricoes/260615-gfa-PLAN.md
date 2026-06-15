---
phase: quick-260615-gfa
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/catalog/management/commands/importar_makerworld.py
  - apps/catalog/management/commands/podar_galeria.py
  - apps/catalog/management/commands/gerar_descricoes.py
  - requirements.txt
autonomous: true
requirements: [QUICK-260615-gfa]
user_setup:
  - service: anthropic
    why: "gerar_descricoes usa Claude Vision para reescrever descrições — RODA NO SERVER, não local"
    env_vars:
      - name: ANTHROPIC_API_KEY
        source: "Anthropic Console -> Settings -> API Keys (https://console.anthropic.com)"

must_haves:
  truths:
    - "importar_makerworld limita a 3 fotos por produto (1 principal + 2 extras), descartando foto 03+"
    - "podar_galeria remove galeria além das 2 primeiras imagens, com --dry-run e --limit, sem tocar Product.image"
    - "gerar_descricoes reescreve Product.description via Claude Vision com --dry-run, --limit, --model e skip de produtos sem foto"
    - "anthropic está em requirements.txt com versão pinada"
    - "NADA executa contra produção — o plano entrega comandos + runbook de deploy"
  artifacts:
    - path: "apps/catalog/management/commands/podar_galeria.py"
      provides: "Comando de poda de galeria idempotente"
      contains: "class Command(BaseCommand)"
    - path: "apps/catalog/management/commands/gerar_descricoes.py"
      provides: "Comando de geração de descrições via Claude Vision"
      contains: "class Command(BaseCommand)"
    - path: "requirements.txt"
      provides: "Dependência anthropic pinada"
      contains: "anthropic"
  key_links:
    - from: "importar_makerworld.py"
      to: "ProductImage gallery"
      via: "loop fotos[1:1+MAX_EXTRAS]"
      pattern: "MAX_EXTRAS|MAX_FOTOS"
    - from: "podar_galeria.py"
      to: "media/products/gallery"
      via: ".image.delete(save=False) + row delete"
      pattern: "image\\.delete"
    - from: "gerar_descricoes.py"
      to: "Anthropic Messages API"
      via: "base64 image block + texto"
      pattern: "anthropic|messages\\.create"
---

<objective>
Bloco A — Catálogo limpo. Entregar TRÊS comandos de management escritos e commitados LOCALMENTE, sem executar nada contra produção:

1. Cap de imagens no importador (3 fotos/produto: 1 principal + 2 extras).
2. Novo comando `podar_galeria` — poda idempotente da galeria existente (roda no server depois).
3. Novo comando `gerar_descricoes` — reescreve descrições via Claude Vision (roda no server depois).

Mais: adicionar `anthropic` ao requirements.txt e entregar um RUNBOOK DE DEPLOY no SUMMARY.

Purpose: limpar o catálogo (galerias inchadas, descrições genéricas repetidas) sem risco a produção — o código vai pronto, a execução fica para o operador no server.
Output: 1 arquivo modificado + 2 comandos novos + requirements.txt + runbook de deploy no SUMMARY.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@apps/catalog/models.py
@apps/catalog/management/commands/importar_makerworld.py

<interfaces>
<!-- Contratos já no codebase. Use diretamente, sem explorar. -->

Product (apps/catalog/models.py):
  image = ImageField(upload_to="products/")        # foto principal
  description = TextField(blank=True)
  name, material (default "PLA"), dimensions (str ex.: "12.0×8.0×3.0 cm")
  category = FK -> Category (usar category.name)
  related_name "gallery" -> ProductImage (reverse)

ProductImage (apps/catalog/models.py):
  product = FK(Product, related_name="gallery", on_delete=CASCADE)
  image = ImageField(upload_to="products/gallery/")
  order = PositiveSmallIntegerField(default=0)
  Meta.ordering = ("order",)

Estilo dos comandos existentes (importar_makerworld.py):
  - docstring de módulo em pt-br (bloco "Uso:" no fim)
  - class Command(BaseCommand) com help pt-br
  - add_arguments com flags curtas/pt-br
  - self.stdout.write(...) e self.stdout.write(self.style.SUCCESS/ERROR(...))
  - self.stderr.write(self.style.ERROR(...)) p/ falhas
  - galeria reconstruída idempotente: p.gallery.all().delete() + loop ProductImage(product=p, order=idx)
  - ProductImage salvo via gi.image.save(f"{slug}-{idx}.jpg", ContentFile(bytes), save=True)
  - leitura de bytes do ImageField (local FileSystemStorage e remoto): instance.image.open("rb").read() (lembrar de fechar / usar context) — NÃO assumir caminho de filesystem
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Cap de 3 fotos no importar_makerworld + anthropic no requirements.txt</name>
  <files>apps/catalog/management/commands/importar_makerworld.py, requirements.txt</files>
  <action>
    Em importar_makerworld.py, adicionar duas constantes de módulo no topo (junto aos outros markers de seção, com comentário pt-br explicando o PORQUÊ): MAX_FOTOS = 3 e MAX_EXTRAS = 2. Interpretação TRAVADA: 1 principal (Product.image, foto 00) + 2 extras (ProductImage order=1,2) = 3 total; foto 03+ é descartada.

    Aplicar o cap APENAS no loop da galeria (hoje `for idx, foto_extra in enumerate(fotos[1:], start=1):`, por volta da linha 354). Trocar a fatia `fotos[1:]` por `fotos[1:1+MAX_EXTRAS]` usando a constante. Foto principal (fotos[0]) e TODO o resto do comportamento (conversão JPEG quadrada via _foto_para_jpeg_quadrado, p.gallery.all().delete() idempotente, pipeline 3D, tradução de nome) ficam INALTERADOS.

    Adicionar um comentário pt-br no estilo do arquivo (# ---- ... ----) marcando que a galeria é limitada a MAX_EXTRAS por produto e o porquê (catálogo limpo / 3 fotos). Não introduzir lógica fora desse loop.

    Em requirements.txt, adicionar uma seção pt-br nova (ex.: "# --- Descrições por IA (Claude Vision) ---") com a linha `anthropic==0.109.1` pinada, perto das outras integrações. NÃO instalar nada agora (o install acontece no server, no rebuild do container).
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python -c "import ast; ast.parse(open('apps/catalog/management/commands/importar_makerworld.py', encoding='utf-8').read())" && grep -q "MAX_EXTRAS" apps/catalog/management/commands/importar_makerworld.py && grep -q "fotos\[1:1+MAX_EXTRAS\]\|fotos\[1 : 1 + MAX_EXTRAS\]" apps/catalog/management/commands/importar_makerworld.py && grep -q "^anthropic==" requirements.txt && echo PASS</automated>
  </verify>
  <done>importar_makerworld parseia sem erro, tem MAX_EXTRAS=2 e fatia a galeria em fotos[1:1+MAX_EXTRAS]; requirements.txt tem `anthropic==` pinado; comportamento de import (JPEG quadrado, idempotência, pipeline 3D) preservado.</done>
</task>

<task type="auto">
  <name>Task 2: Novo comando podar_galeria (poda idempotente, dry-run, limit)</name>
  <files>apps/catalog/management/commands/podar_galeria.py</files>
  <action>
    Criar apps/catalog/management/commands/podar_galeria.py seguindo o estilo dos comandos existentes (docstring de módulo pt-br com bloco "Uso:", class Command(BaseCommand), help pt-br, self.stdout/self.style).

    Comportamento: migração in-place, idempotente, reversível (apenas dados). Para CADA Product, manter Product.image (NUNCA tocar) + as 2 primeiras ProductImage por `order`; remover as ProductImage restantes (order além das 2 primeiras) E os arquivos órfãos sob media/products/gallery/.

    Lógica por produto:
    - Iterar produtos via Product.objects.all() (respeitar --limit; aplicar como contagem de produtos PROCESSADOS, e usar .iterator() ou slice se útil).
    - Para o produto, obter a galeria ordenada: list(p.gallery.order_by("order", "id")). Manter os 2 primeiros; o "resto" = galeria[2:].
    - Para cada ProductImage do resto: deletar o arquivo via img.image.delete(save=False) (remove o arquivo do storage sem salvar o model) e em seguida img.delete() (remove a linha). Contar removidos por produto e total.
    - Idempotência: produtos com <=2 imagens não geram remoção (no-op).

    Flags:
    - --dry-run: NÃO altera nada; apenas reporta por produto quantas imagens SERIAM removidas (só os produtos com remoção pendente) + totais (produtos afetados, imagens a remover).
    - --limit N (int, default 0 = sem limite): processa no máximo N produtos.

    Saída pt-br no estilo do arquivo: linha por produto afetado (ex.: "  · {nome}: removendo {n} imagem(ns) da galeria"), e um resumo final via self.style.SUCCESS (ex.: "Poda: {x} produtos afetados, {y} imagens removidas" — em dry-run, prefixar "[DRY-RUN] " e dizer "seriam removidas"). Tratar erro por produto sem abortar o batch (try/except por produto, self.stderr.write em falha).

    Usar SOMENTE Django ORM/storage — nada de SQL cru, nada de manipular caminho de filesystem direto (deixar o storage cuidar via .image.delete).
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python manage.py podar_galeria --help >/dev/null 2>&1 && python -c "import ast; ast.parse(open('apps/catalog/management/commands/podar_galeria.py', encoding='utf-8').read())" && grep -q "dry-run\|dry_run" apps/catalog/management/commands/podar_galeria.py && grep -q "image.delete" apps/catalog/management/commands/podar_galeria.py && grep -q "\-\-limit" apps/catalog/management/commands/podar_galeria.py && echo PASS</automated>
  </verify>
  <done>`python manage.py podar_galeria --help` lista --dry-run e --limit; o comando mantém Product.image e as 2 primeiras ProductImage, remove o resto + arquivos órfãos via .image.delete(save=False); idempotente; dry-run não altera nada; erro por produto não aborta o batch.</done>
</task>

<task type="auto">
  <name>Task 3: Novo comando gerar_descricoes (Claude Vision) + runbook de deploy no SUMMARY</name>
  <files>apps/catalog/management/commands/gerar_descricoes.py</files>
  <action>
    ANTES de codar a chamada à API: consultar a documentação ATUAL do SDK Anthropic Python via Context7 (resolve-library-id "anthropic python sdk" -> get-library-docs com query "messages create vision base64 image block model id"). NÃO adivinhar o model id, o shape da Messages API nem o formato do bloco de imagem base64. Confirmar: (a) um model id atual com visão (ex.: família claude-opus-4 ou claude-sonnet — usar o id exato retornado pela doc), (b) a forma do client.messages.create(...) com content multimodal (bloco type "image" com source base64 + media_type, mais bloco type "text").

    Criar apps/catalog/management/commands/gerar_descricoes.py no estilo dos comandos existentes (docstring pt-br com "Uso:", class Command(BaseCommand), help pt-br, self.stdout/self.style).

    Comportamento: reescrever Product.description com 2-3 frases ÚNICAS em pt-br por produto usando Claude VISION. Entrada por produto: a FOTO PRINCIPAL (Product.image; PULAR produtos sem image) + name + category.name + material + dimensions.

    Prompt (system + user) em pt-br pedindo: descrição fácil de entender que diga o que é a peça / para quem serve / um detalhe legal, fechando de forma natural SEM repetir um template fixo (cada produto deve soar diferente — variar a estrutura das frases). 2-3 frases. Responder SOMENTE a descrição, sem aspas, sem rótulos.

    Leitura da imagem: ler os bytes do ImageField via storage (instance.image.open("rb").read(), fechar depois) — funciona em FileSystemStorage local e remoto; NÃO assumir caminho de filesystem. Codificar em base64 e detectar o media_type pelo conteúdo/extensão (as fotos importadas são JPEG; aceitar image/jpeg e image/png).

    Constantes de módulo: MODELO_PADRAO = "<id atual confirmado na doc>" (model id como constante, overridável por --model). Ler a chave de os.environ["ANTHROPIC_API_KEY"]; se ausente, abortar cedo com self.stderr + return (mensagem pt-br), NUNCA logar a chave.

    Flags:
    - --dry-run: imprime a descrição proposta por produto e NÃO salva.
    - --limit N (int, default 0 = sem limite).
    - --model M (str, default MODELO_PADRAO).

    Robustez: throttle leve entre chamadas (ex.: time.sleep curto) e try/except POR PRODUTO — uma falha (API/timeout/imagem ilegível) registra self.stderr e segue para o próximo, NUNCA aborta o batch. Salvar fora de dry-run via p.save(update_fields=["description"]). Resumo final pt-br via self.style.SUCCESS (processados, atualizados, pulados sem foto, falhas). Em dry-run, prefixar "[DRY-RUN] ".

    NÃO executar o comando contra dado real aqui — apenas escrever o código (a verificação é --help + parse, sem chamar a API).

    RUNBOOK DE DEPLOY (incluir como seção no SUMMARY ao final do plano, em pt-br): (1) commit + git push local; (2) no server: `git fetch && git reset --hard origin/main`; (3) rebuild do container (instala anthropic); (4) garantir ANTHROPIC_API_KEY no ambiente do server; (5) rodar `python manage.py podar_galeria --dry-run`, inspecionar, depois sem --dry-run; (6) rodar `python manage.py gerar_descricoes --dry-run --limit 5`, inspecionar, depois ampliar/rodar sem --dry-run. Reforçar: NADA disso roda localmente nem foi executado contra produção por este plano.
  </action>
  <verify>
    <automated>cd /c/dev/l3d-labz-site && python manage.py gerar_descricoes --help >/dev/null 2>&1 && python -c "import ast; ast.parse(open('apps/catalog/management/commands/gerar_descricoes.py', encoding='utf-8').read())" && grep -q "ANTHROPIC_API_KEY" apps/catalog/management/commands/gerar_descricoes.py && grep -q "\-\-model" apps/catalog/management/commands/gerar_descricoes.py && grep -q "dry-run\|dry_run" apps/catalog/management/commands/gerar_descricoes.py && grep -Eq "base64|b64" apps/catalog/management/commands/gerar_descricoes.py && echo PASS</automated>
  </verify>
  <done>`python manage.py gerar_descricoes --help` lista --dry-run, --limit e --model; usa o SDK anthropic com bloco de imagem base64 e model id confirmado na doc (constante overridável); pula produtos sem foto; falha por produto não aborta o batch; chave via env, nunca logada; SUMMARY contém o runbook de deploy pt-br e a nota de que nada rodou contra produção.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| comando local -> produção | Os comandos NÃO devem rodar contra prod neste plano; execução é manual no server via runbook |
| comando -> Anthropic API | bytes de imagem + metadados do produto saem para a API externa; resposta volta como texto da descrição |
| env -> processo | ANTHROPIC_API_KEY lido do ambiente |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-gfa-01 | Information Disclosure | ANTHROPIC_API_KEY | mitigate | Chave só via os.environ; nunca impressa em stdout/stderr; mensagens de erro não incluem a chave |
| T-gfa-02 | Tampering | podar_galeria deleta arquivos/linhas | mitigate | --dry-run obrigatório antes do real (runbook); só remove gallery além das 2 primeiras; Product.image nunca tocado; try/except por produto |
| T-gfa-03 | Denial of Service | rajada de chamadas à Anthropic | mitigate | throttle (sleep) entre chamadas; --limit; try/except por produto não aborta batch |
| T-gfa-04 | Tampering | execução acidental contra produção | mitigate | Plano não executa nada; runbook exige dry-run + inspeção antes de qualquer escrita no server |
| T-gfa-SC | Tampering | install do pacote anthropic (pip) | mitigate | anthropic é pacote oficial Anthropic (legítimo, verificado em pypi.org/project/anthropic); versão pinada com == |
</threat_model>

<verification>
- `python -c "import ast; ast.parse(...)"` passa nos 3 arquivos de comando.
- `python manage.py podar_galeria --help` e `python manage.py gerar_descricoes --help` listam as flags esperadas.
- requirements.txt contém `anthropic==` pinado.
- Nenhum comando foi executado contra dados de produção; SUMMARY contém o runbook de deploy.
</verification>

<success_criteria>
- importar_makerworld limita a galeria a MAX_EXTRAS (2) por produto, descartando foto 03+; resto do comportamento intacto.
- podar_galeria: idempotente, --dry-run, --limit; mantém Product.image + 2 primeiras ProductImage, remove o resto + arquivos órfãos; erro por produto não aborta.
- gerar_descricoes: Claude Vision, --dry-run, --limit, --model; pula produtos sem foto; chave via env; falha isolada por produto; model id e API shape confirmados via Context7 (não adivinhados).
- anthropic pinado em requirements.txt.
- Runbook de deploy entregue no SUMMARY; nada executado contra produção.
</success_criteria>

<output>
Create `.planning/quick/260615-gfa-catalogo-limpo-imagens-descricoes/260615-gfa-SUMMARY.md` when done. Incluir o RUNBOOK DE DEPLOY em pt-br como seção do SUMMARY.
</output>
