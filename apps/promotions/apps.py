from django.apps import AppConfig


class PromotionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.promotions"
    verbose_name = "Promoções"

    def ready(self):
        from . import signals  # noqa: F401
