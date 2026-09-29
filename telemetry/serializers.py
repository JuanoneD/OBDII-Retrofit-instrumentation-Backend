from rest_framework import serializers

from .models import Reading, Vehicle, normalize_device_id, validate_device_id


class DeviceIdField(serializers.CharField):
    """Campo de MAC da ESP32, já padronizado para AA:BB:CC:DD:EE:FF."""

    def to_internal_value(self, data):
        value = normalize_device_id(super().to_internal_value(data))
        try:
            validate_device_id(value)
        except Exception as exc:
            raise serializers.ValidationError(exc.messages[0])
        return value


# --- BE-05: cadastro do dispositivo/veículo ----------------------------------
class VehicleSerializer(serializers.ModelSerializer):
    device_id = DeviceIdField()
    fuel_percent = serializers.FloatField(read_only=True)
    pending_sync = serializers.BooleanField(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "device_id",
            "name",
            "plate",
            "model",
            "owner_name",
            "is_active",
            "tank_capacity",
            "gasoline_level",
            "fuel_percent",
            "fuel_consumption_factor",
            "total_distance",
            "trip_consumption",
            "pending_sync",
            "sync_version",
            "last_seen_at",
            "created_at",
        ]
        # Estes campos são atualizados pela ESP32/backend, não pelo cadastro.
        read_only_fields = [
            "gasoline_level",
            "fuel_consumption_factor",
            "total_distance",
            "trip_consumption",
            "sync_version",
            "last_seen_at",
            "created_at",
        ]

    def validate_device_id(self, value):
        qs = Vehicle.objects.filter(device_id=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Este dispositivo já está cadastrado.")
        return value

    def validate_tank_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("A capacidade do tanque deve ser maior que zero.")
        return value

    def create(self, validated_data):
        # Carro novo começa com o tanque cheio (a ESP32 corrige no primeiro envio).
        validated_data.setdefault("gasoline_level", validated_data.get("tank_capacity", 45.0))
        return super().create(validated_data)


# --- BE-02: JSON que a ESP32 envia -------------------------------------------
class IngestSerializer(serializers.Serializer):
    device_id = DeviceIdField()
    timestamp = serializers.DateTimeField(required=False, allow_null=True)

    # Voláteis (obrigatórios)
    rpm = serializers.IntegerField(min_value=0)
    speed = serializers.IntegerField(min_value=0)
    coolant_temp = serializers.IntegerField()
    engine_load = serializers.FloatField(min_value=0)
    throttle_position = serializers.FloatField(min_value=0)
    ltft = serializers.FloatField()

    # Voláteis (opcionais)
    timing_advance = serializers.FloatField(required=False, allow_null=True)
    module_voltage = serializers.FloatField(required=False, allow_null=True)
    map_pressure = serializers.FloatField(required=False, allow_null=True)

    # Persistentes (NVS da ESP32)
    gasoline_level = serializers.FloatField(min_value=0)
    tank_capacity = serializers.FloatField(min_value=0.1)
    fuel_consumption_factor = serializers.FloatField(min_value=0)
    total_distance = serializers.FloatField(min_value=0)
    trip_consumption = serializers.FloatField(min_value=0)

    # Última versão de sincronização que a ESP32 aplicou (0 se nunca aplicou)
    sync_version = serializers.IntegerField(min_value=0, required=False, default=0)


# --- BE-03: leituras para o dashboard ----------------------------------------
class ReadingSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source="vehicle.device_id", read_only=True)

    class Meta:
        model = Reading
        fields = [
            "id",
            "device_id",
            "sent_at",
            "received_at",
            "rpm",
            "speed",
            "coolant_temp",
            "engine_load",
            "throttle_position",
            "ltft",
            "timing_advance",
            "module_voltage",
            "map_pressure",
            "gasoline_level",
            "fuel_percent",
        ]
