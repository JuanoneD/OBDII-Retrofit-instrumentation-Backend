from django.db import models

from telemetry.models import Vehicle


class Refuel(models.Model):
    """Registro de cada abastecimento/recálculo do fator (BE-04)."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="refuels")
    liters_inserted = models.FloatField("litros inseridos no carro")
    liters_spent_system = models.FloatField("litros gastos no sistema")
    old_factor = models.FloatField("fator antigo")
    new_factor = models.FloatField("fator novo")
    gasoline_level_before = models.FloatField("nível antes (L)")
    gasoline_level_after = models.FloatField("nível depois (L)")
    created_at = models.DateTimeField("data", auto_now_add=True)

    class Meta:
        verbose_name = "abastecimento"
        verbose_name_plural = "abastecimentos"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.vehicle.name}: {self.liters_inserted} L em {self.created_at:%d/%m/%Y}"
