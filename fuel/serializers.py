from rest_framework import serializers

from telemetry.serializers import DeviceIdField

from .models import Refuel


class RecalculateSerializer(serializers.Serializer):
    """JSON que o Frontend envia: {"device_id": "...", "litrosInseridos": 30.5}."""

    device_id = DeviceIdField()
    litrosInseridos = serializers.FloatField(min_value=0.01)


class RefuelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refuel
        fields = [
            "id",
            "liters_inserted",
            "liters_spent_system",
            "old_factor",
            "new_factor",
            "gasoline_level_before",
            "gasoline_level_after",
            "created_at",
        ]
