"""Funções pequenas usadas pelos dois apps (telemetry e fuel)."""

from rest_framework import status
from rest_framework.response import Response

from .models import Vehicle, normalize_device_id


def error_response(code, message, http_status, errors=None):
    """Formato padrão de erro da API: {"status": "error", "code": ..., "message": ...}."""
    body = {"status": "error", "code": code, "message": message}
    if errors:
        body["errors"] = errors
    return Response(body, status=http_status)


def get_vehicle(device_id, for_update=False):
    """
    Busca o veículo pelo MAC da ESP32.

    Retorna (vehicle, None) se achou, ou (None, resposta_de_erro) se não achou.
    """
    if not device_id:
        return None, error_response(
            "device_id_required",
            "Informe o device_id (MAC da ESP32).",
            status.HTTP_400_BAD_REQUEST,
        )

    qs = Vehicle.objects.select_for_update() if for_update else Vehicle.objects
    vehicle = qs.filter(device_id=normalize_device_id(device_id), is_active=True).first()
    if vehicle is None:
        return None, error_response(
            "device_not_registered",
            "Dispositivo não cadastrado ou inativo. Cadastre em /api/devices/.",
            status.HTTP_404_NOT_FOUND,
        )
    return vehicle, None
