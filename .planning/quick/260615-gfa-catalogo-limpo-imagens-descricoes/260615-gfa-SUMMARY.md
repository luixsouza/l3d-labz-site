---
phase: quick-260615-gfa
plan: 01
subsystem: catalog
tags: [catalog, management-command, anthropic, claude-vision, cleanup]
requires:
  - apps.catalog.models.Product
  - apps.catalog.models.ProductImage
provides:
  - "apps/catalog/management/commands/podar_galeria.py — poda idempotente da galeria"
  - "apps/catalog/management/commands/gerar_descricoes.py — descrições via Claude Vision"
  - "importar_makerworld cap de 3 fotos/produto"
  - "anthropic==0.109.1 pinado em requirements.txt"
affects:
  - apps/catalog/management/commands/importar_makerworld.py
  - requirements.txt
tech-stack:
  added:
    - "anthropic==0.109.1 (SDK oficial Anthropic, Claude Vision)"
  patterns:
    - "management command BaseCommand no estilo importar_makerworld (docstring pt-br + Uso:, self.stdout/self.style)"
    - "leitura de ImageField storage-agnóstica via .open('rb').read()"
    - "try/except por item para não abortar batch; --dry-run + --limit"
key-files:
  created:
    - apps/catalog/management/commands/podar_galeria.py
    - apps/catalog/management/commands/gerar_descricoes.py
  modified:
    - apps/catalog/management/commands/importar_makerworld.py
    - requirements.txt
decisions:
  - "Cap travado em 3 fotos (1 principal + 2 extras) via MAX_FOTOS/MAX_EXTRAS; foto 03+ descartada"
  - "podar_galeria espelha o cap (MANTER_EXTRAS=2) para limpar galerias importadas ANTES do cap"
  - "MODELO_PADRAO=claude-opus-4-8 (constante overridável por --model), sem 'thinking' (tarefa simples)"
  - "import tardio do anthropic dentro do handle — pacote só existe após rebuild do container no server"
  - "NADA executado contra produção: entrega é código + runbook; execução é manual no server"
metrics:
  duration_min: 2
  completed: "2026-06-15T15:00:07Z"
  tasks: 3
  files: 4
---

# Phase quick-260615-gfa Plan 01: Catálogo limpo (imagens + descrições) Summary

Três comandos de management entregues e commitados LOCALMENTE — cap de 3 fotos no importador, `podar_galeria` (poda idempotente da galeria existente) e `gerar_descricoes` (reescreve descrições via Claude Vision) — com `anthropic==0.109.1` pinado; nada executado contra produção.

## What Was Built

### Task 1 — Cap de 3 fotos no importador + anthropic no requirements (commit a224a8e)
- `importar_makerworld.py`: constantes de módulo `MAX_FOTOS = 3` e `MAX_EXTRAS = 2` (comentário pt-br explicando o porquê: catálogo limpo, galerias inchadas poluem o card).
- Loop da galeria passou de `fotos[1:]` para `fotos[1 : 1 + MAX_EXTRAS]` — 1 principal (`Product.image`, foto 00) + 2 extras (`ProductImage` order=1,2); foto 03+ descartada.
- Todo o resto do pipeline (JPEG quadrado via `_foto_para_jpeg_quadrado`, `p.gallery.all().delete()` idempotente, pipeline 3D, tradução de nome) **inalterado**.
- `requirements.txt`: nova seção pt-br `# --- Descrições por IA (Claude Vision) ---` com `anthropic==0.109.1`. **Não instalado** — o install acontece no rebuild do container no server.

### Task 2 — Comando `podar_galeria` (commit 4959a2f)
- Migração in-place, idempotente, reversível (só dados). Para cada `Product`: mantém `Product.image` (NUNCA tocada) + as 2 primeiras `ProductImage` por `order`; remove o resto (linha + arquivo).
- Remoção via `img.image.delete(save=False)` (arquivo do storage) seguido de `img.delete()` (linha). Só ORM/storage — sem SQL cru, sem manipular caminho de filesystem.
- Flags: `--dry-run` (simula, não apaga) e `--limit N` (default 0 = sem limite, conta produtos processados).
- Idempotência: produtos com `<= 2` imagens são no-op. `try/except` por produto: falha não aborta o batch. Resumo final via `self.style.SUCCESS` (prefixo `[DRY-RUN]` quando simulando).

### Task 3 — Comando `gerar_descricoes` (Claude Vision) (commit 39e10a7)
- Reescreve `Product.description` com 2-3 frases pt-br únicas por produto via Claude Vision: envia a foto principal (base64) + nome, categoria, material, dimensões.
- `MODELO_PADRAO = "claude-opus-4-8"` (constante de módulo, overridável por `--model`); sem `thinking` (tarefa simples → mais barato/rápido); `max_tokens=400`, não-streaming.
- Bloco de imagem base64: `{"type": "image", "source": {"type": "base64", "media_type": ..., "data": ...}}` + bloco `text`; resposta lida via `next((b.text for b in resp.content if b.type == "text"), "")`.
- Leitura da imagem storage-agnóstica (`p.image.open("rb").read()` com `close()`), `media_type` por extensão (`image/png` p/ `.png`, senão `image/jpeg`).
- Chave via `os.environ["ANTHROPIC_API_KEY"]` — validada cedo, abortando com mensagem pt-br no stderr se ausente; **nunca logada**. Import tardio do `anthropic` (pacote só existe após rebuild).
- Flags: `--dry-run` (imprime e não salva), `--limit N`, `--model M`. Pula produtos sem foto. `throttle` (`time.sleep(0.4)`) entre chamadas + `try/except` por produto (API/timeout/imagem ilegível não aborta o batch). Salva via `p.save(update_fields=["description"])`.

## Verification

| Check | Resultado |
|-------|-----------|
| `ast.parse` nos 3 comandos | PASS |
| `podar_galeria --help` lista `--dry-run` e `--limit` | PASS |
| `gerar_descricoes --help` lista `--dry-run`, `--limit`, `--model` | PASS |
| `requirements.txt` tem `anthropic==` pinado | PASS |
| `importar_makerworld` fatia `fotos[1 : 1 + MAX_EXTRAS]` | PASS |
| Nada executado contra produção | Confirmado — só `--help` + `ast.parse` |

Observação de ambiente: o `python` "pelado" do Git Bash não tem Django; a verificação `--help` usou o interpretador do venv do projeto (`.venv/Scripts/python.exe`) com settings dev/SQLite. Nenhum comando foi executado contra dados reais ou produção, e a Anthropic API **não foi chamada**.

## Threat Model — Mitigações aplicadas

| Threat ID | Mitigação no código |
|-----------|---------------------|
| T-gfa-01 (Info Disclosure — API key) | Chave só via `os.environ`; validação cedo; nunca impressa em stdout/stderr |
| T-gfa-02 (Tampering — poda) | `--dry-run`; só remove galeria além das 2 primeiras; `Product.image` nunca tocado; `try/except` por produto |
| T-gfa-03 (DoS — rajada API) | `time.sleep` throttle entre chamadas; `--limit`; `try/except` por produto |
| T-gfa-04 (execução acidental em prod) | Plano não executa nada; runbook exige `--dry-run` + inspeção antes de qualquer escrita |
| T-gfa-SC (install do anthropic) | Pacote oficial Anthropic (verificado em pypi.org/project/anthropic); pinado com `==` |

## Deviations from Plan

**1. [Rule 3 — Blocking] Interpretador para `manage.py --help`**
- **Found during:** Task 2 (verificação).
- **Issue:** `python manage.py ... --help` falhou com `ModuleNotFoundError: No module named 'django'` — o `python` do Git Bash não tem as deps; o projeto usa um venv em `/c/dev/l3d-labz-site/.venv`.
- **Fix:** Verificações `--help` rodadas com `.venv/Scripts/python.exe` (settings dev/SQLite). Nenhuma alteração de código necessária. Não é um install de pacote (exclusão da Rule 3 não se aplica).
- **Files modified:** nenhum.

**2. [Override do prompt] Model id / API shape do Anthropic não consultados via Context7**
- **Found during:** Task 3.
- **Issue:** O PLAN pedia consultar Context7 para o model id e o shape da Messages API. O prompt de execução forneceu detalhes autoritativos (`AUTHORITATIVE_API_DETAILS`) com instrução explícita de NÃO confiar em um model id mais antigo do Context7.
- **Fix:** Usado o model id fixo `claude-opus-4-8` (constante `MODELO_PADRAO`, overridável por `--model`) e o shape de bloco de imagem base64 exatamente como especificado no override. Context7 não consultado.
- **Files modified:** `gerar_descricoes.py` (conforme especificado).

## Known Stubs

Nenhum. Os comandos são funcionais e completos. `gerar_descricoes` depende do pacote `anthropic` (instalado no server via rebuild) e da `ANTHROPIC_API_KEY` (no ambiente do server) — ambos cobertos pelo runbook, não são stubs.

## RUNBOOK DE DEPLOY (pt-br)

> **Tudo abaixo roda NO SERVER, manualmente, pelo operador. NADA foi executado por este plano — nem localmente, nem contra produção. A Anthropic API NÃO foi chamada.**

1. **Local — commit + push.** Os 3 commits de código já estão na branch; faça o push para `origin/main` (via fluxo normal do projeto).

2. **No server — atualizar o repo:**
   ```bash
   git fetch && git reset --hard origin/main
   ```

3. **No server — rebuild do container** (instala `anthropic==0.109.1` do `requirements.txt`):
   ```bash
   # conforme o setup Docker do server (ex.: docker compose build && docker compose up -d)
   ```

4. **No server — garantir a chave no ambiente** (nunca commitar a chave; usar `.env`/secret do server):
   ```bash
   # ANTHROPIC_API_KEY deve estar no ambiente do container
   # origem: Anthropic Console -> Settings -> API Keys (https://console.anthropic.com)
   ```

5. **Poda da galeria — simular, inspecionar, depois aplicar:**
   ```bash
   python manage.py podar_galeria --dry-run        # inspecione quantas imagens seriam removidas
   python manage.py podar_galeria                  # aplica de verdade (após conferir o dry-run)
   ```

6. **Descrições via Claude Vision — começar pequeno, inspecionar, depois ampliar:**
   ```bash
   python manage.py gerar_descricoes --dry-run --limit 5   # leia as 5 descrições propostas
   python manage.py gerar_descricoes --limit 5             # grava só essas 5 (confiança)
   python manage.py gerar_descricoes --dry-run             # simula o catálogo todo
   python manage.py gerar_descricoes                       # grava tudo (após conferir)
   ```

**Reforço:** rodar sempre `--dry-run` antes de qualquer escrita; `podar_galeria` apaga arquivos e `gerar_descricoes` sobrescreve descrições. Os comandos são idempotentes/resilientes (erro por item não aborta o batch), mas a primeira execução real deve ser sempre precedida de inspeção do dry-run.

## Self-Check: PASSED

- `apps/catalog/management/commands/podar_galeria.py` — FOUND
- `apps/catalog/management/commands/gerar_descricoes.py` — FOUND
- `apps/catalog/management/commands/importar_makerworld.py` (modificado) — FOUND
- `requirements.txt` (anthropic pinado) — FOUND
- Commit a224a8e (Task 1) — FOUND
- Commit 4959a2f (Task 2) — FOUND
- Commit 39e10a7 (Task 3) — FOUND
