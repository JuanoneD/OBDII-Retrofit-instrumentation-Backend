"""
Rotas principais do projeto.

Cada app guarda as suas próprias rotas no arquivo urls.py dele:
- users/urls.py   -> rotas que começam com /user
- devices/urls.py -> rotas que começam com /devices
"""

from django.urls import include, path

urlpatterns = [
    path("", include("users.urls")),
    path("", include("devices.urls")),
]
