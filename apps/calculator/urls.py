"""URLs do app calculadora de precificação."""
from django.urls import path

from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.publica, name="publica"),
    path("orcamento/", views.orcamento, name="orcamento"),
]
