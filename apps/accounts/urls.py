from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("entrar/", views.NexoraLoginView.as_view(), name="login"),
    path("sair/", views.NexoraLogoutView.as_view(), name="logout"),
    path("cadastro/", views.register, name="register"),
    path("perfil/", views.profile, name="profile"),
]
