from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from telemetry.utils import error_response, get_vehicle

from .models import Refuel
from .serializers import RecalculateSerializer, RefuelSerializer


def calculate_new_factor(old_factor, liters_inserted, liters_spent_system):
    """Novo Fator = Fator Antigo × (Litros Inseridos no Carro / Litros Gastos no Sistema)."""
    return old_factor * (liters_inserted / liters_spent_system)


@api_view(["GET"])
def fuel_status(request):
    """
    GET /api/fuel/status/?device_id=AA:BB:CC:DD:EE:FF

    Dados atuais usados no recálculo (fator antigo e litros gastos) + últimos abastecimentos.
    """
    vehicle, error = get_vehicle(request.query_params.get("device_id"))
    if error:
        return error

    return Response(
        {
            "device_id": vehicle.device_id,
            "fuel_consumption_factor": vehicle.fuel_consumption_factor,
            "liters_spent_system": vehicle.trip_consumption,
            "gasoline_level": vehicle.gasoline_level,
            "tank_capacity": vehicle.tank_capacity,
            "fuel_percent": vehicle.fuel_percent,
            "pending_sync": vehicle.pending_sync,
            "last_refuels": RefuelSerializer(vehicle.refuels.all()[:10], many=True).data,
        }
    )


@api_view(["POST"])
def recalculate(request):
    """
    POST /api/fuel/recalculate/   body: {"device_id": "...", "litrosInseridos": 30.5}

    1. Lê o fator antigo e os litros gastos no sistema desde o último abastecimento.
    2. Aplica a fórmula e salva o novo fator.
    3. Zera o contador de litros gastos e soma os litros inseridos ao tanque.
    4. Marca para a ESP32 receber os novos valores no próximo envio.
    """
    serializer = RecalculateSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            "invalid_payload",
            "Informe device_id e litrosInseridos (maior que zero).",
            status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors,
        )
    liters_inserted = serializer.validated_data["litrosInseridos"]

    with transaction.atomic():
        vehicle, error = get_vehicle(serializer.validated_data["device_id"], for_update=True)
        if error:
            return error

        if liters_inserted > vehicle.tank_capacity:
            return error_response(
                "liters_above_capacity",
                f"Não cabem {liters_inserted} L num tanque de {vehicle.tank_capacity} L.",
                status.HTTP_400_BAD_REQUEST,
            )

        liters_spent = vehicle.trip_consumption
        if liters_spent <= 0:
            return error_response(
                "no_consumption_recorded",
                "O sistema ainda não registrou consumo desde o último abastecimento; "
                "não é possível recalcular o fator.",
                status.HTTP_400_BAD_REQUEST,
            )

        old_factor = vehicle.fuel_consumption_factor
        new_factor = calculate_new_factor(old_factor, liters_inserted, liters_spent)
        level_before = vehicle.gasoline_level
        level_after = min(vehicle.tank_capacity, level_before + liters_inserted)

        vehicle.fuel_consumption_factor = new_factor
        vehicle.trip_consumption = 0.0
        vehicle.gasoline_level = level_after
        vehicle.sync_version += 1
        vehicle.save()

        refuel = Refuel.objects.create(
            vehicle=vehicle,
            liters_inserted=liters_inserted,
            liters_spent_system=liters_spent,
            old_factor=old_factor,
            new_factor=new_factor,
            gasoline_level_before=level_before,
            gasoline_level_after=level_after,
        )

    return Response(
        {
            "status": "ok",
            "message": "Fator de consumo recalculado com sucesso.",
            "device_id": vehicle.device_id,
            "old_factor": old_factor,
            "new_factor": new_factor,
            "liters_inserted": liters_inserted,
            "liters_spent_system": liters_spent,
            "gasoline_level": level_after,
            "fuel_percent": vehicle.fuel_percent,
            "refuel_id": refuel.id,
        }
    )
