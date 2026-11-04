"""
Rotas principais do projeto.

Cada app guarda as suas próprias rotas no arquivo urls.py dele:
- users/urls.py   -> rotas que começam com /user
- dtcs/urls.py    -> /devices/sendDTCs e /devices/getDTCs
- devices/urls.py -> as demais rotas que começam com /devices
"""

from django.urls import include, path

urlpatterns = [
    path("", include("users.urls")),
    # As rotas dos DTCs vêm antes das de devices, porque devices tem a rota
    # "devices/<idDevice>", que entenderia "sendDTCs" como o MAC de uma ESP
    path("", include("dtcs.urls")),
    path("", include("devices.urls")),
]
