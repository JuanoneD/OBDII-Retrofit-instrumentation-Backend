"""Rotas do app de códigos de erro (DTCs e falhas detectadas)."""

from django.urls import path

from . import views

urlpatterns = [
    path("devices/sendDTCs", views.send_dtcs),
    path("devices/getDTCs", views.get_dtcs),
    path("devices/getDetectErrors", views.get_detect_errors),
    path("devices/<str:idDevice>/addDetectError", views.add_detect_error),
]
