"""Rotas do app de dispositivos (todas começam com /devices)."""

from django.urls import path

from . import views

urlpatterns = [
    path("devices", views.list_devices),
    path("devices/<str:idDevice>", views.sync_device),
]
