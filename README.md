# Nexora — E-commerce de Impressão 3D

Loja de produtos impressos em 3D (action figures, utensílios, decoração, gadgets,
cosplay e itens nerds). Tema **dark + azul**, visual clean e moderno, com animações.

> Esta fase entrega a **experiência do usuário**: cadastro/login, catálogo com
> filtros, detalhe de produto, promoções, cupons e carrinho.

## Stack

- **Django 5.2** + **DRF**
- **SQLite** em dev · **PostgreSQL** em produção (troca por variável de ambiente)
- **Cache**: LocMem em dev · **Redis** (django-redis) em produção
- HTML + CSS puro (sem framework front), ícones SVG, animações com IntersectionObserver

## Arquitetura — camadas por app ("cada macaco no seu galho")

Cada app em `apps/` segue a mesma divisão de responsabilidades:

| Camada          | Arquivo            | Responsabilidade                                        |
|-----------------|--------------------|---------------------------------------------------------|
| **Model**       | `models.py`        | Schema + propriedades de negócio sem efeito colateral   |
| **Queries**     | `queries.py`       | Só ORM. Querysets otimizados (`select_related`) + cache |
| **Services**    | `services.py`      | Regra de negócio e **única camada que escreve** no banco|
| **Mappers**     | `mappers.py`       | `Model -> dict/DTO` para template e serializer          |
| **Serializers** | `serializers.py`   | Entrada/saída da API (DRF)                              |
| **Views**       | `views.py`         | Finas: request → service → resposta                     |
| **Templates**   | `templates/<app>/` | Apresentação                                            |

Apps: `core` (base/home/layout), `accounts` (usuário e endereços),
`catalog` (categorias/produtos), `promotions` (banners/cupons), `cart` (carrinho em sessão),
`orders` (checkout, pedidos e pagamento).

Base das camadas em `apps/core/layers.py`; helpers de cache em `apps/core/cache.py`.

## Rodando em desenvolvimento

```bash
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo          # popula categorias, produtos, promoções e cupons
python manage.py createsuperuser    # opcional, para o /admin
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ · Admin em `/admin/`.

Cupons de demonstração: `NERD10` (10%), `CUBO20` (20%, mín. R$150), `MENOS30` (R$30, mín. R$120).

## Trocando para PostgreSQL + Redis

Copie `.env.example` para `.env` e preencha:

```env
DATABASE_ENGINE=postgres
POSTGRES_DB=nexora
POSTGRES_USER=nexora
POSTGRES_PASSWORD=nexora
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/1
```

Nenhuma mudança de código é necessária — `config/settings/base.py` detecta as variáveis.
Depois: `python manage.py migrate && python manage.py seed_demo`.

## Cache

- Listagens estáveis (categorias, destaques, lançamentos, promoções) são cacheadas
  via `apps/core/cache.py` com TTLs de `settings.CACHE_TTL`.
- Signals em `catalog/signals.py` e `promotions/signals.py` invalidam o cache em
  qualquer `save`/`delete`, mantendo os dados sempre corretos.

## Settings

- `config/settings/base.py` — comum
- `config/settings/dev.py` — debug toolbar, e-mail no console, estáticos sem manifest
- `config/settings/prod.py` — HTTPS, HSTS, cookies seguros, whitenoise manifest

## Checkout, pedidos e pagamento

- **Checkout** (`/pedidos/checkout/`, exige login): endereço de entrega + método
  de pagamento, com resumo do pedido sticky. Pré-preenche o endereço padrão do usuário.
- **Pagamento simulado** isolado em `apps/orders/payments.py` (`PaymentService`):
  - **PIX** e **cartão** → aprovados na hora (pedido entra "Em produção"); cartão guarda só os 4 últimos dígitos.
  - **Boleto** → fica "Aguardando pagamento" com linha digitável.
  - Para integrar um gateway real (Mercado Pago/Stripe), basta trocar o corpo de `PaymentService.process()`.
- **Ao fechar o pedido** (`OrderService.create_from_cart`, transação atômica):
  cria `Order`/`OrderItem` com *snapshots* (preço, nome, endereço, totais),
  dá baixa no estoque, soma vendas, consome o cupom e esvazia o carrinho.
- **Confirmação** com instruções de pagamento, **histórico** (`/pedidos/meus-pedidos/`)
  e **detalhe** do pedido, com badges de status.

## Próximos passos (não incluídos)

Rastreamento de entrega, favoritos, avaliações, e-mail transacional, API pública
versionada e suíte de testes.
