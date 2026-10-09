"""
Ponto de entrada do backend no servidor (AWS).

O servidor web (gunicorn) usa este arquivo para iniciar o Django:
    gunicorn config.wsgi:application
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
