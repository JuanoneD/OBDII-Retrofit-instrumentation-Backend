"""
Carrega a base de erros (dtcs/dtc_base.py) na tabela DTCDescription.

Roda sozinha no `python manage.py migrate`. Se um código já existir, o título e
a descrição são atualizados (update_or_create), então pode rodar mais de uma vez.
"""

from django.db import migrations

from dtcs.dtc_base import DTC_BASE


def carregar_base(apps, schema_editor):
    DTCDescription = apps.get_model("dtcs", "DTCDescription")
    for code, title, description in DTC_BASE:
        DTCDescription.objects.update_or_create(
            code=code, defaults={"title": title, "description": description}
        )


def apagar_base(apps, schema_editor):
    """Usado só se alguém desfizer esta migration."""
    apps.get_model("dtcs", "DTCDescription").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dtcs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(carregar_base, apagar_base),
    ]
