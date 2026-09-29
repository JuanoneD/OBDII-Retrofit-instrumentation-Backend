"""Rotas principais: tudo da API fica em /api/."""

from django.contrib import admin
from django.urls import include, path

from telemetry.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/", include("telemetry.urls")),
    path("api/", include("fuel.urls")),
]
