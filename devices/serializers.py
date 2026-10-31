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
    A resposta também traz o diagnoseMode, para a ESP saber se deve ler
    os códigos de erro (DTCs) do carro. A ESP não envia esse campo.
    """

    class Meta:
        model = VehicleData
        fields = FUEL_FIELDS + ["sync_version", "diagnoseMode"]
        # Os campos de combustível e o sync_version são obrigatórios no envio da ESP
        extra_kwargs = {field: {"required": True} for field in FUEL_FIELDS + ["sync_version"]}
        # O diagnoseMode só aparece na resposta (quem altera é o site)
        read_only_fields = ["diagnoseMode"]


class RecalculateSerializer(serializers.Serializer):
    """JSON do recálculo: {refueledGas} = litros colocados para encher o tanque."""

    refueledGas = serializers.FloatField()

    def validate_refueledGas(self, value):
        if value <= 0:
            raise serializers.ValidationError("refueledGas deve ser maior que zero.")
        return value


class UpdateDeviceSerializer(serializers.Serializer):
    """
    JSON para o site alterar a ESP: {name, tankCapacity}.
    Os dois são opcionais, mas é preciso enviar pelo menos um.
    """

    name = serializers.CharField(max_length=100, required=False)
    tankCapacity = serializers.FloatField(required=False)

    def validate_tankCapacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("tankCapacity deve ser maior que zero.")
        return value

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Envie pelo menos um campo: name ou tankCapacity.")
        return data


class OperationModeSerializer(serializers.Serializer):
    """JSON para ligar ou desligar o modo diagnóstico: {diagnoseMode: true/false}."""

    diagnoseMode = serializers.BooleanField()


class DeviceSerializer(serializers.ModelSerializer):
    """Informações de uma ESP mostradas no site (GET /devices)."""

    idDevice = serializers.CharField(source="id")  # o ID da ESP é o MAC

    class Meta:
        model = VehicleData
        fields = ["idDevice", "name"] + FUEL_FIELDS + ["diagnoseMode"]
