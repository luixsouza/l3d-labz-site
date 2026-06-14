"""Configuração do app de calculadora de precificação de impressão 3D."""
from django.apps import AppConfig


class CalculatorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.calculator"
    verbose_name = "Calculadora"
