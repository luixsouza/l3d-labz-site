from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("modelos-3d/", views.models_3d, name="models_3d"),
    path("sugestoes/", views.search_suggest, name="search_suggest"),
    path("favoritos/", views.wishlist, name="wishlist"),
    path("favoritos/<int:product_id>/", views.favorite_toggle, name="favorite_toggle"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("avaliar/<int:product_id>/", views.review_create, name="review_create"),
    path("perguntar/<int:product_id>/", views.question_create, name="question_create"),
    path("responder/<int:question_id>/", views.answer_create, name="answer_create"),
]
