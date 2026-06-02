from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("meus-pedidos/", views.order_list, name="list"),
    path("checkout/sucesso/<str:number>/", views.confirmation, name="confirmation"),
    path("<str:number>/", views.order_detail, name="detail"),
]
