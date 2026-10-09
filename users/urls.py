"""Rotas do app de usuários (todas começam com /user)."""

from django.urls import path

from . import views

urlpatterns = [
    path("user", views.create_user),
    path("user/login", views.login),
    path("user/logout", views.logout),
    path("user/addDevice", views.add_device),
]
