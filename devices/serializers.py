"""
Serializers do app de dispositivos.

Um serializer converte os dados entre JSON e Python: valida o JSON que chega
nas requisições e monta o JSON das respostas. Se algum campo estiver faltando
ou for inválido, o endpoint responde 400 dizendo qual campo está errado.
"""

from rest_framework import serializers

from .models import VehicleData

# Os 5 dados de combustível que a ESP guarda na memória dela
FUEL_FIELDS = ["gasolineLevel", "tankCapacity", "fuelConsumptionFactor", "totalDistance", "tripConsumption"]


class DeviceSyncSerializer(serializers.ModelSerializer):
    """
    JSON trocado com a ESP no POST /devices/<idDevice>:
    os 5 dados de combustível + sync_version.

    É usado tanto para validar o que a ESP envia quanto para montar a resposta.
    """

    class Meta:
        model = VehicleData
        fields = FUEL_FIELDS + ["sync_version"]
        # Todos os campos são obrigatórios no envio da ESP
        extra_kwargs = {field: {"required": True} for field in fields}


class DeviceSerializer(serializers.ModelSerializer):
    """Informações de uma ESP mostradas no site (GET /devices)."""

    idDevice = serializers.CharField(source="id")  # o ID da ESP é o MAC

    class Meta:
        model = VehicleData
        fields = ["idDevice", "name"] + FUEL_FIELDS
