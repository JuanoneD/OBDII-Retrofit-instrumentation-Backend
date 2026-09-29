from django.urls import path

from . import views

urlpatterns = [
    # BE-05 — dispositivos/veículos
    path("devices/", views.VehicleListCreateView.as_view(), name="device-list"),
    path("devices/<str:device_id>/", views.VehicleDetailView.as_view(), name="device-detail"),
    # BE-02 — ESP32 envia dados
    path("telemetry/ingest/", views.ingest, name="telemetry-ingest"),
    # BE-03 — Frontend lê dados
    path("telemetry/latest/", views.latest, name="telemetry-latest"),
    path("telemetry/history/", views.history, name="telemetry-history"),
]
