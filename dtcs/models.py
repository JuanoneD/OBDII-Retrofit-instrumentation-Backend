"""
Tabelas (modelos) do app de códigos de erro (DTCs).

DTC = Diagnostic Trouble Code: o código de erro que a central do carro (ECU)
guarda quando detecta um problema. Exemplo: P0301 = falha de ignição no cilindro 1.

- DTC: os códigos de erro que cada ESP leu do carro.
- DTCDescription: a "base de erros", com o título e a descrição de cada código.
"""

import re

from django.db import models

from devices.models import VehicleData


def normalize_dtc(value):
    """
    Valida um código DTC e o deixa em maiúsculas. Ex.: "p0301" -> "P0301".

    Formato: 1 letra (P = motor/transmissão, C = chassi, B = carroceria,
    U = rede/comunicação) + 4 caracteres (o 1º de 0 a 3, os outros de 0-9 ou A-F).
    Devolve None se o valor não for um código válido.
    """
    code = str(value).strip().upper()
    return code if re.fullmatch(r"[PCBU][0-3][0-9A-F]{3}", code) else None


class DTCDescription(models.Model):
    """Base de erros: título e descrição de cada código DTC, em português."""

    code = models.CharField(primary_key=True, max_length=5)  # ex.: P0301
    title = models.CharField(max_length=200)
    description = models.TextField()

    class Meta:
        db_table = "DTCDescription"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class DTC(models.Model):
    """Um código de erro que a ESP leu do carro."""

    id = models.BigAutoField(primary_key=True, db_column="ID")
    device = models.ForeignKey(VehicleData, on_delete=models.CASCADE, db_column="ID_ESP")
    code = models.CharField(max_length=5)  # ex.: P0301
    receivedAt = models.DateTimeField(auto_now_add=True)  # quando o backend recebeu

    class Meta:
        db_table = "DTC"
        ordering = ["code"]
        # A mesma ESP não guarda o mesmo código duas vezes
        constraints = [
            models.UniqueConstraint(fields=["device", "code"], name="unique_device_dtc"),
        ]

    def __str__(self):
        return f"{self.device_id} - {self.code}"
