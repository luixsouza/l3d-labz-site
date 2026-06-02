"""Anexa um SessionCart a cada request como request.cart."""
from __future__ import annotations

from .cart import SessionCart


class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.cart = SessionCart(request)
        return self.get_response(request)
