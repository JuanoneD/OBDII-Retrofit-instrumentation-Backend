"""Rotas do app de dispositivos (todas começam com /devices)."""

from django.urls import path

from . import views

urlpatterns = [
    path("devices", views.list_devices),
    # As rotas com nome fixo vêm antes de "devices/<idDevice>",
    # senão "resetTrip" seria entendido como o MAC de uma ESP
    path("devices/resetAndRecalculate", views.reset_and_recalculate),
    path("devices/resetTrip", views.reset_trip),
    path("devices/<str:idDevice>", views.sync_device),
]
