"""Reescreve a descrição de cada produto via Claude Vision (Anthropic).

Para CADA Product com foto principal (Product.image), envia a imagem + os
metadados (nome, categoria, material, dimensões) ao Claude e grava em
Product.description uma descrição curta (2-3 frases) em pt-br, única por produto
— sem o template repetido "impresso sob demanda em PLA pela L3D Labz...".

Por que VISION: o modelo enxerga a peça e descreve o que ela realmente é,
gerando texto natural e variado em vez de boilerplate. Produtos sem foto são
pulados (nada para o modelo olhar).

Segurança: a chave vem de ANTHROPIC_API_KEY no ambiente e NUNCA é logada.
Roda no SERVER, depois do rebuild do container (ver runbook no SUMMARY) —
NÃO rodar localmente nem contra produção sem --dry-run + inspeção antes.

Uso:
    python manage.py gerar_descricoes --dry-run --limit 5
    python manage.py gerar_descricoes --limit 20
    python manage.py gerar_descricoes
    python manage.py gerar_descricoes --model claude-opus-4-8
"""
from __future__ import annotations

import base64
import os
import time

from django.core.management.base import BaseCommand

from apps.catalog.models import Product

# ---------------------------------------------------------------------------
# Modelo Claude com visão (constante de módulo, overridável por --model)
# ---------------------------------------------------------------------------
# Claude Opus 4.8 — modelo atual com visão. Descrição de produto é tarefa
# simples, então NÃO usamos "thinking" (mais barato/rápido).
MODELO_PADRAO = "claude-opus-4-8"

# Throttle leve entre chamadas para não estourar rate limit em lote.
THROTTLE_S = 0.4

# Teto de tokens da resposta — 2-3 frases cabem folgado em ~400.
MAX_TOKENS = 400

SYSTEM_PROMPT = (
    "Você é um copywriter de e-commerce de impressão 3D da loja L3D Labz. "
    "Escreve descrições curtas, claras e calorosas em português brasileiro. "
    "Cada descrição deve soar diferente — varie a estrutura das frases, "
    "não use um template fixo. Nunca invente material, medidas ou função "
    "que não estejam na imagem ou nos dados fornecidos."
)


class Command(BaseCommand):
    help = (
        "Reescreve Product.description via Claude Vision (2-3 frases pt-br únicas por produto). "
        "Pula produtos sem foto. Chave via ANTHROPIC_API_KEY. "
        "Use --dry-run para ver as descrições sem salvar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Imprime a descrição proposta por produto e NÃO salva.",
        )
        parser.add_argument(
            "--limit", type=int, default=0,
            help="Processa no máximo N produtos (0 = sem limite).",
        )
        parser.add_argument(
            "--model", default=MODELO_PADRAO,
            help=f"Model id do Claude (default: {MODELO_PADRAO}).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        model_id = options["model"].strip() or MODELO_PADRAO
        prefixo = "[DRY-RUN] " if dry_run else ""

        # --- chave de API (env, nunca logada) ---
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.stderr.write(self.style.ERROR(
                "ANTHROPIC_API_KEY ausente no ambiente — defina a chave antes de rodar "
                "(ela nunca é impressa). Abortando."
            ))
            return

        # import tardio: o pacote só existe após o rebuild do container no server
        try:
            import anthropic
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "pacote 'anthropic' não instalado — rode pip install -r requirements.txt "
                "(no server, via rebuild do container). Abortando."
            ))
            return

        client = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

        produtos = Product.objects.select_related("category").order_by("id")
        if limit:
            produtos = produtos[:limit]

        processados = 0
        atualizados = 0
        sem_foto = 0
        falhas = 0

        for p in produtos:
            # pula produtos sem foto principal (nada para o modelo olhar)
            if not p.image:
                sem_foto += 1
                self.stdout.write(f"  · {p.name}: sem foto — pulando")
                continue

            processados += 1
            try:
                img_bytes, media_type = self._ler_imagem(p)
                texto = self._descrever(client, model_id, p, img_bytes, media_type)
                if not texto:
                    falhas += 1
                    self.stderr.write(self.style.ERROR(
                        f"  ! {p.name}: resposta vazia do modelo — pulando"
                    ))
                    continue

                self.stdout.write(f"  · {p.name}: {texto}")

                if not dry_run:
                    p.description = texto
                    p.save(update_fields=["description"])
                    atualizados += 1
            except Exception as e:
                # falha num produto (API/timeout/imagem ilegível) não aborta o batch
                falhas += 1
                self.stderr.write(self.style.ERROR(
                    f"  ! {p.name}: falha ao gerar descrição: {e} — pulando"
                ))
            finally:
                time.sleep(THROTTLE_S)

        self.stdout.write(self.style.SUCCESS(
            f"{prefixo}Descrições: {processados} processados, {atualizados} atualizados, "
            f"{sem_foto} sem foto, {falhas} falhas"
        ))

    # ---- leitura da imagem (storage-agnóstica) ----
    def _ler_imagem(self, p: Product) -> tuple[bytes, str]:
        """Lê os bytes da foto principal via storage e detecta o media_type.

        Funciona em FileSystemStorage local e remoto — não assume caminho de
        filesystem. PNG por extensão; o resto (jpg/jpeg/sem extensão) → JPEG.
        """
        f = p.image.open("rb")
        try:
            data = f.read()
        finally:
            f.close()
        nome = (p.image.name or "").lower()
        media_type = "image/png" if nome.endswith(".png") else "image/jpeg"
        return data, media_type

    # ---- chamada Vision ao Claude ----
    def _descrever(self, client, model_id, p, img_bytes, media_type) -> str:
        """Monta o bloco de imagem base64 + texto e retorna a descrição limpa."""
        img_b64 = base64.standard_b64encode(img_bytes).decode("utf-8")

        categoria = p.category.name if p.category_id else "produto 3D"
        dims = f", dimensões {p.dimensions}" if p.dimensions else ""
        user_prompt = (
            "Escreva uma descrição de e-commerce em português brasileiro para esta peça "
            "impressa em 3D. Diga em 2 ou 3 frases o que é a peça, para quem ela serve e "
            "um detalhe legal dela, fechando de forma natural. Não repita um template fixo; "
            "varie a estrutura. Responda SOMENTE a descrição, sem aspas e sem rótulos.\n\n"
            f"Nome: {p.name}\n"
            f"Categoria: {categoria}\n"
            f"Material: {p.material}{dims}"
        )

        resp = client.messages.create(
            model=model_id,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }],
        )
        texto = next((b.text for b in resp.content if b.type == "text"), "")
        return texto.strip().strip('"')
