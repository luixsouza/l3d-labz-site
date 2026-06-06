"""Views do catálogo — finas, delegam ao CatalogService."""
from __future__ import annotations

from django.http import Http404
from django.shortcuts import render

from .services import CatalogService


def product_list(request):
    page = request.GET.get("page", 1)
    context = CatalogService.browse(request.GET, page=page)
    return render(request, "catalog/product_list.html", context)


def product_detail(request, slug):
    context = CatalogService.get_detail(slug)
    if context is None:
        raise Http404("Produto não encontrado.")
    return render(request, "catalog/product_detail.html", context)


def models_3d(request):
    return render(request, "catalog/models_3d.html", CatalogService.gallery())
