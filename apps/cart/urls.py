from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("adicionar/<int:product_id>/", views.add, name="add"),
    path("atualizar/<int:product_id>/", views.update, name="update"),
    path("remover/<int:product_id>/", views.remove, name="remove"),
    path("cupom/", views.apply_coupon, name="apply_coupon"),
    path("limpar/", views.clear, name="clear"),
]
