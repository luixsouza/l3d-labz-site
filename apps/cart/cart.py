"""Carrinho persistido em sessão (sem modelo de banco).

Esta classe cuida APENAS do estado bruto na sessão ({id: quantidade} + cupom).
A hidratação com produtos, totais e descontos fica no CartService.
"""
from __future__ import annotations

SESSION_KEY = "cart"
COUPON_KEY = "cart_coupon"


class SessionCart:
    def __init__(self, request):
        self.session = request.session
        self._items: dict[str, int] = self.session.get(SESSION_KEY, {})

    # ---- mutações ----
    def add(self, product_id: int, quantity: int = 1, *, replace: bool = False) -> None:
        pid = str(product_id)
        current = 0 if replace else self._items.get(pid, 0)
        self._items[pid] = max(1, current + quantity if not replace else quantity)
        self._save()

    def set_quantity(self, product_id: int, quantity: int) -> None:
        pid = str(product_id)
        if quantity <= 0:
            self.remove(product_id)
            return
        if pid in self._items:
            self._items[pid] = quantity
            self._save()

    def remove(self, product_id: int) -> None:
        self._items.pop(str(product_id), None)
        self._save()

    def clear(self) -> None:
        self._items = {}
        self.session.pop(COUPON_KEY, None)
        self._save()

    # ---- cupom ----
    @property
    def coupon_code(self) -> str | None:
        return self.session.get(COUPON_KEY)

    def set_coupon(self, code: str | None) -> None:
        if code:
            self.session[COUPON_KEY] = code
        else:
            self.session.pop(COUPON_KEY, None)
        self.session.modified = True

    # ---- leitura ----
    def raw_items(self) -> dict[str, int]:
        return dict(self._items)

    @property
    def total_quantity(self) -> int:
        return sum(self._items.values())

    def _save(self) -> None:
        self.session[SESSION_KEY] = self._items
        self.session.modified = True
