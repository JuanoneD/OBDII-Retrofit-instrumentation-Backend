from django.urls import path

from . import views

urlpatterns = [
    # BE-04 — recálculo do fator de combustível
    path("fuel/status/", views.fuel_status, name="fuel-status"),
    path("fuel/recalculate/", views.recalculate, name="fuel-recalculate"),
]
