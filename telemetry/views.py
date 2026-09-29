from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Reading, Vehicle, normalize_device_id
from .serializers import IngestSerializer, ReadingSerializer, VehicleSerializer
from .utils import error_response, get_vehicle

HISTORY_DEFAULT_LIMIT = 50
HISTORY_MAX_LIMIT = 500


@api_view(["GET"])
def health(request):
    """Usado pela AWS para saber se o servidor está no ar."""
    return Response({"status": "ok"})


# =============================================================================
# BE-05 — Cadastro / identificação do dispositivo (ESP32 = MAC address)
# =============================================================================
class VehicleListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/devices/  -> lista os veículos cadastrados
    POST /api/devices/  -> cadastra um veículo vinculado ao MAC da ESP32
    """

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class VehicleDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/devices/<device_id>/  -> dados de um veículo (serve para validar o ID)
    PATCH /api/devices/<device_id>/  -> altera nome, placa, capacidade etc.
    """

    serializer_class = VehicleSerializer

    def get_object(self):
        return get_object_or_404(
            Vehicle, device_id=normalize_device_id(self.kwargs["device_id"])
        )


# =============================================================================
# BE-02 — Ingestão: a ESP32 envia os dados
# =============================================================================
@api_view(["POST"])
def ingest(request):
    """
    POST /api/telemetry/ingest/

    1. Valida o JSON (se faltar campo -> 400).
    2. Confere se o dispositivo está cadastrado (se não -> 404).
    3. Salva os campos voláteis como uma nova leitura (histórico).
    4. Atualiza os campos persistentes no veículo.
    5. Responde 201 confirmando o recebimento (+ valores a sincronizar, se houver).
    """
    serializer = IngestSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            "invalid_payload",
            "JSON incompleto ou com valores inválidos.",
            status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors,
        )
    data = serializer.validated_data

    with transaction.atomic():
        vehicle, error = get_vehicle(data["device_id"], for_update=True)
        if error:
            return error

        # A ESP32 confirma que aplicou o recálculo enviando o mesmo sync_version.
        if data["sync_version"] >= vehicle.sync_version:
            vehicle.esp_sync_version = vehicle.sync_version

        # Se ainda há um recálculo pendente, os valores de combustível do
        # backend valem mais que os da ESP32 (ela ainda está com os antigos).
        if not vehicle.pending_sync:
            vehicle.gasoline_level = data["gasoline_level"]
            vehicle.tank_capacity = data["tank_capacity"]
            vehicle.fuel_consumption_factor = data["fuel_consumption_factor"]
            vehicle.trip_consumption = data["trip_consumption"]

        now = timezone.now()
        vehicle.total_distance = data["total_distance"]
        vehicle.last_seen_at = now
        vehicle.save()

        reading = Reading.objects.create(
            vehicle=vehicle,
            sent_at=data.get("timestamp") or now,
            rpm=data["rpm"],
            speed=data["speed"],
            coolant_temp=data["coolant_temp"],
            engine_load=data["engine_load"],
            throttle_position=data["throttle_position"],
            ltft=data["ltft"],
            timing_advance=data.get("timing_advance"),
            module_voltage=data.get("module_voltage"),
            map_pressure=data.get("map_pressure"),
            gasoline_level=vehicle.gasoline_level,
            fuel_percent=vehicle.fuel_percent,
        )

    return Response(
        {
            "status": "ok",
            "reading_id": reading.id,
            "received_at": reading.received_at,
            "sync": vehicle.sync_payload(),
        },
        status=status.HTTP_201_CREATED,
    )


# =============================================================================
# BE-03 — Leitura: o Frontend consulta os dados
# =============================================================================
@api_view(["GET"])
def latest(request):
    """
    GET /api/telemetry/latest/?device_id=AA:BB:CC:DD:EE:FF

    Retorna a leitura mais recente + o estado atual do veículo.
    """
    vehicle, error = get_vehicle(request.query_params.get("device_id"))
    if error:
        return error

    reading = vehicle.readings.first()
    return Response(
        {
            "vehicle": VehicleSerializer(vehicle).data,
            "reading": ReadingSerializer(reading).data if reading else None,
        }
    )


@api_view(["GET"])
def history(request):
    """
    GET /api/telemetry/history/?device_id=AA:BB:CC:DD:EE:FF&limit=50

    Retorna as últimas N leituras, da mais antiga para a mais nova (bom para gráficos).
    """
    vehicle, error = get_vehicle(request.query_params.get("device_id"))
    if error:
        return error

    try:
        limit = int(request.query_params.get("limit", HISTORY_DEFAULT_LIMIT))
    except ValueError:
        return error_response(
            "invalid_limit", "limit deve ser um número inteiro.", status.HTTP_400_BAD_REQUEST
        )
    limit = max(1, min(limit, HISTORY_MAX_LIMIT))

    readings = list(vehicle.readings.all()[:limit])
    readings.reverse()
    return Response(
        {
            "device_id": vehicle.device_id,
            "count": len(readings),
            "results": ReadingSerializer(readings, many=True).data,
        }
    )
