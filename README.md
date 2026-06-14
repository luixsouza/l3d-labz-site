# L3D Labz — Impressão 3D sob demanda

Loja e portfólio de uma fábrica de impressão 3D chamada **L3D Labz**.
Identidade visual inspirada no verde/branco/azul do Luigi — minimalista e elegante, com suporte a tema claro/escuro.

O diferencial técnico é o **visualizador 3D embutido**: o cliente abre e manipula o modelo GLB do produto
(rotacionar, zoom, pan) diretamente no navegador via `<model-viewer>`, sem plugin.

## Features

| Módulo | Descrição | Rota |
|--------|-----------|------|
| **Catálogo** | Categorias, listagem com filtros e busca, detalhe de produto | `/catalogo/` |
| **Visualizador 3D** | `<model-viewer>` com galeria de fotos e download GLB/STL | `/catalogo/<slug>/` |
| **Fale meu Lithophane** | Gera lithophane personalizada a partir de foto enviada | `/lithophane/` |
| **Promoções** | Banners promocionais e cupons de desconto | `/promocoes/` |
| **Carrinho** | Carrinho em sessão com aplicação de cupom | `/carrinho/` |
| **Checkout & pedidos** | Endereço de entrega, pagamento simulado, histórico e detalhe | `/pedidos/` |
| **Contas** | Cadastro, login por e-mail, endereços | `/conta/` |
| **Calculadora 3D** | Precificação pública em tempo real com presets de impressora/filamento e bandeiras ANEEL | `/calculadora/` |
| **Orçamento PDF** | Versão privada (is_staff) que gera PDF de orçamento sem expor custos | `/calculadora/orcamento/` |

## Stack

- **Django 5.2** + DRF 3.16 (serializers como scaffolding de API futura)
- **HTML + CSS** puro com design tokens — sem Tailwind, Bootstrap ou bundler
- **JavaScript vanilla** (IIFE, `defer`, sem npm) — `app.js` + `calculator.js`
- **`<model-viewer>`** — web component para visualização 3D (1 script, zero build)
- **SQLite** em dev · **PostgreSQL** em produção (troca por variável de ambiente)
- **Cache**: LocMem em dev · **Redis** (`django-redis`) em produção (opcional)
- **reportlab** — geração de PDF de orçamento
- **Pillow** — upload e redimensionamento de imagens
- **whitenoise** — serving de estáticos em produção
- **gunicorn** — servidor WSGI de produção

## Arquitetura — camadas por app

Cada app em `apps/` segue a mesma divisão de responsabilidades:

| Camada          | Arquivo            | Responsabilidade                                        |
|-----------------|--------------------|---------------------------------------------------------|
| **Model**       | `models.py`        | Schema + propriedades de negócio sem efeito colateral   |
| **Queries**     | `queries.py`       | Só ORM. Querysets otimizados (`select_related`) + cache |
| **Services**    | `services.py`      | Regra de negócio e **única camada que escreve** no banco|
| **Mappers**     | `mappers.py`       | `Model → dict/DTO` para template e serializer           |
| **Serializers** | `serializers.py`   | Entrada/saída da API (DRF, camelCase)                   |
| **Views**       | `views.py`         | Finas: request → service → resposta                     |
| **Templates**   | `templates/<app>/` | Apresentação                                            |

Apps: `core` (base/home/layout), `accounts` (usuário e endereços),
`catalog` (categorias/produtos/3D), `promotions` (banners/cupons),
`cart` (carrinho em sessão), `orders` (checkout, pedidos e pagamento),
`lithophane` (geração de lithophane), `calculator` (precificação 3D).

Base das camadas em `apps/core/layers.py`; helpers de cache em `apps/core/cache.py`.

## Calculadora de Precificação 3D

Ferramenta disponível em `/calculadora/`:

- **Presets genéricos**: 14 impressoras FDM (Creality, Bambu Lab, Elegoo, Prusa) com potência ativa média medida por wattímetro, valor e vida útil pré-carregados; 10 filamentos (PLA, PETG, ABS, ASA, TPU, Nylon, PC, PLA-CF, PETG-CF) com preço/kg sugerido e densidade.
- **Bandeiras ANEEL**: tarifa efetiva = tarifa base da distribuidora + adicional da bandeira (Verde/Amarela/Vermelha P1/P2). Atualizado em 2026-06-14 (bandeira vigente: Amarela).
- **Cálculo em tempo real** (client-side, espelha `PricingService.calcular`): breakdown com barras proporcionais, custo por hora, total por quantidade, permalink compartilhável e botão Copiar resultado.
- **Orçamento PDF privado** (`/calculadora/orcamento/`, requer `is_staff`): mesmo formulário com cálculo server-side; o PDF exibe apenas o preço ao cliente, sem expor custos internos.

## Rodando em desenvolvimento

```bash
# 1. ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. dependências
pip install -r requirements.txt

# 3. banco (SQLite por padrão)
python manage.py migrate

# 4. dados de demonstração (opcional)
python manage.py seed_demo         # categorias, produtos, promoções e cupons

# 5. superusuário (para /admin e /calculadora/orcamento/)
python manage.py createsuperuser

# 6. servidor
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` · Admin em `/admin/`.

## Configuração via variáveis de ambiente

Copie `.env.example` para `.env` e ajuste conforme necessário.
Em desenvolvimento, os defaults (SQLite + LocMem) funcionam sem nenhuma variável configurada.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | `dev-insecure-...` | Chave secreta do Django (obrigatório em produção) |
| `DEBUG` | `True` | Desligar em produção |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos |
| `DATABASE_ENGINE` | `sqlite` | `postgres` para PostgreSQL |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | — | Conexão com PostgreSQL |
| `REDIS_URL` | — | Ativa Redis como cache (ex.: `redis://127.0.0.1:6379/1`) |

Settings: `config/settings/base.py` (comum), `dev.py` (desenvolvimento), `prod.py` (produção com HTTPS/HSTS/WhiteNoise).

## Deploy

O site roda em servidor próprio via Docker + Cloudflare Tunnel.
Deploy = push na branch `main` → CI (GitHub Actions) reinicia os containers.
Detalhes de infraestrutura em `.planning/`.

## Checkout, pedidos e pagamento

- Checkout em `/pedidos/checkout/` (exige login): endereço de entrega + método de pagamento, com resumo do pedido sticky.
- **Pagamento simulado** em `apps/orders/payments.py` (`PaymentService`):
  - **PIX** e **cartão** → aprovados na hora; cartão guarda só os 4 últimos dígitos.
  - **Boleto** → fica "Aguardando pagamento" com linha digitável simulada.
  - Para integrar um gateway real (Mercado Pago/Stripe), basta trocar `PaymentService.process()`.
- **Ao fechar o pedido** (`OrderService.create_from_cart`, transação atômica): cria `Order`/`OrderItem` com snapshots (preço, nome, endereço, totais), dá baixa no estoque, consome o cupom e esvazia o carrinho.
- Histórico em `/pedidos/meus-pedidos/` e detalhe do pedido com badges de status.

## Próximos passos

Rastreamento de entrega, favoritos, avaliações, e-mail transacional, API pública versionada e suíte de testes automatizados.
