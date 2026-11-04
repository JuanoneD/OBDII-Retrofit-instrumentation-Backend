"""Rotas do app de códigos de erro (DTCs)."""

from django.urls import path

from . import views

urlpatterns = [
    path("devices/sendDTCs", views.send_dtcs),
    path("devices/getDTCs", views.get_dtcs),
]
