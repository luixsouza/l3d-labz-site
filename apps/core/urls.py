from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("sobre/", views.AboutView.as_view(), name="about"),
    # páginas estáticas institucionais (footer)
    path(
        "privacidade/",
        TemplateView.as_view(template_name="core/static_page.html", extra_context={"page": "privacidade"}),
        name="privacidade",
    ),
    path(
        "termos/",
        TemplateView.as_view(template_name="core/static_page.html", extra_context={"page": "termos"}),
        name="termos",
    ),
]
