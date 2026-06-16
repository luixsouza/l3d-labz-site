"""URLs do app calculadora de precificação."""
from django.urls import path

from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.publica, name="publica"),
    path("orcamento/", views.orcamento, name="orcamento"),
    # Rotas públicas por token UUID (sem auth — seguro pois o modelo só tem dados públicos)
    path("orcamento/<uuid:token>/", views.orcamento_publico, name="orcamento_publico"),
    path("orcamento/<uuid:token>/pdf/", views.orcamento_pdf, name="orcamento_pdf"),
]
