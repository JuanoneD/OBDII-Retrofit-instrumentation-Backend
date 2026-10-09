"""
Tabelas (modelos) do app de dispositivos.

- VehicleData: os dados de cada ESP32.
- User-VehicleData: liga um usuário a uma ESP.

Identificação da ESP: cada ESP32 é identificada pelo seu MAC address
(ex.: AA:BB:CC:DD:EE:FF). Ele já vem gravado de fábrica na placa e é único,
então não precisa ser gerado nem configurado.
"""

import re

from django.conf import settings
from django.db import models


def normalize_mac(value):
    """
    Valida o MAC da ESP e o padroniza no formato AA:BB:CC:DD:EE:FF.

    Aceita letras minúsculas e outros separadores, por exemplo:
    "aa:bb:cc:dd:ee:ff", "AA-BB-CC-DD-EE-FF" ou "AABBCCDDEEFF".
    Devolve None se o valor não for um MAC válido.
    """
    # Um MAC são 6 pares de caracteres hexadecimais (0-9, A-F),
    # que podem vir separados por ":" ou "-"
    if not re.fullmatch(r"[0-9A-Fa-f]{2}([:-]?[0-9A-Fa-f]{2}){5}", str(value).strip()):
        return None
    # Remove os separadores, coloca em maiúsculas e junta com ":"
    hex_only = re.sub(r"[:-]", "", str(value).strip()).upper()
    return ":".join(hex_only[i : i + 2] for i in range(0, 12, 2))


class VehicleData(models.Model):
    """Dados de uma ESP32 (os mesmos que ela guarda na memória dela)."""

    id = models.CharField(primary_key=True, max_length=17, db_column="ID_ESP")  # MAC
    name = models.CharField(max_length=100, blank=True, default="")
    gasolineLevel = models.FloatField(default=0)  # litros no tanque
    tankCapacity = models.FloatField(default=0)  # capacidade do tanque em litros
    fuelConsumptionFactor = models.FloatField(default=0)  # fator usado no cálculo de consumo
    totalDistance = models.FloatField(default=0)  # distância da viagem
    tripConsumption = models.FloatField(default=0)  # consumo da viagem

    # Número que controla a sincronização entre o banco e a ESP.
    # Aumenta quando o site altera os dados (reset/recálculo).
    sync_version = models.IntegerField(default=0)

    class Meta:
        db_table = "VehicleData"

    def __str__(self):
        return self.id


class UserVehicleData(models.Model):
    """Liga um usuário a uma ESP. Um usuário pode ter várias ESPs e vice-versa."""

    id = models.BigAutoField(primary_key=True, db_column="ID")
    device = models.ForeignKey(VehicleData, on_delete=models.CASCADE, db_column="ID_ESP")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="ID_USER")

    class Meta:
        db_table = "User-VehicleData"
        # Impede ligar a mesma ESP ao mesmo usuário duas vezes
        constraints = [
            models.UniqueConstraint(fields=["device", "user"], name="unique_user_device"),
        ]

    def __str__(self):
        return f"{self.user} - {self.device}"
