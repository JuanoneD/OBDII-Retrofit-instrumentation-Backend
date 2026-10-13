"""
Views do app de dispositivos.

Uma view é a função que executa um endpoint: recebe a requisição, faz o
trabalho e devolve a resposta.

Endpoints deste app:
- GET  /devices                                  lista as ESPs do usuário (o ADM vê todas)
- POST /devices/<idDevice>                       a ESP32 envia os seus dados
- POST /devices/resetAndRecalculate?idDevice=    recalcula o fator e enche o tanque
- POST /devices/resetTrip?idDevice=              zera a distância e o consumo da viagem
"""

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import VehicleData, normalize_mac
from .serializers import FUEL_FIELDS, DeviceSerializer, DeviceSyncSerializer, RecalculateSerializer


@api_view(["GET"])
def list_devices(request):
    """
    Lista as ESPs que o usuário pode ver:
    - usuário comum: só as ESPs ligadas à conta dele;
    - ADM: todas as ESPs.

    Com ?idDevice=<MAC>, devolve só aquela ESP (404 se ela não estiver na lista).
    """
    if request.user.isAdm:
        devices = VehicleData.objects.all()
    else:
        # As ESPs ligadas ao usuário pela tabela User-VehicleData
        devices = VehicleData.objects.filter(uservehicledata__user=request.user)

    id_device = request.query_params.get("idDevice")
    if id_device is not None:
        devices = devices.filter(id=normalize_mac(id_device))
        if not devices.exists():
            return Response({"detail": "ESP não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "device": DeviceSerializer(devices, many=True).data,
        "totalDevice": devices.count(),
    })


@api_view(["POST"])
@permission_classes([AllowAny])  # a ESP não faz login, ela se identifica pelo MAC
def sync_device(request, idDevice):
    """
    A ESP envia os 5 dados de combustível + sync_version e recebe de volta
    os valores que estão no banco.

    Regra da sincronização:
    - sync_version da ESP IGUAL ao do banco: o banco salva os dados da ESP;
    - sync_version DIFERENTE (o site alterou os dados, ex.: um reset):
      o banco ignora os dados da ESP.
    Nos dois casos, a resposta traz os valores do banco. Se o sync_version da
    resposta for diferente do dela, a ESP grava esses valores na memória dela.
    """
    mac = normalize_mac(idDevice)
    if mac is None:
        return Response(
            {"detail": "idDevice deve ser o MAC da ESP, ex.: AA:BB:CC:DD:EE:FF"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = DeviceSyncSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # campo faltando ou inválido -> 400
    data = serializer.validated_data

    # transaction + select_for_update: se o site fizer um reset ao mesmo tempo
    # que a ESP envia, um espera o outro terminar (nenhum dado se perde)
    with transaction.atomic():
        device = VehicleData.objects.select_for_update().filter(id=mac).first()

        if device is None:
            # ESP nova: é cadastrada com os dados que ela enviou
            device = VehicleData.objects.create(id=mac, **data)
        elif data["sync_version"] == device.sync_version:
            # Mesma versão: os dados da ESP são os mais novos, então são salvos
            for field in FUEL_FIELDS:
                setattr(device, field, data[field])
            device.save()
        # Versão diferente: não salva nada (os dados do banco é que valem)

    return Response(DeviceSyncSerializer(device).data)


def get_own_device(request):
    """
    Busca a ESP do ?idDevice= entre as ESPs ligadas à conta do usuário.

    Só o dono pode alterar a ESP: se ela não existir ou não estiver ligada
    à conta dele, devolve None (e o endpoint responde 404).
    select_for_update trava a ESP até o fim da alteração, para que um envio
    da ESP feito ao mesmo tempo não desfaça o reset.
    """
    mac = normalize_mac(request.query_params.get("idDevice", ""))
    return (
        VehicleData.objects.select_for_update()
        .filter(id=mac, uservehicledata__user=request.user)
        .first()
    )


@api_view(["POST"])
def reset_and_recalculate(request):
    """
    O usuário encheu o tanque e informa quantos litros colocou (refueledGas).

    1. Litros gastos no sistema = tankCapacity - gasolineLevel
       (quanto o sistema acha que foi consumido até agora).
    2. Novo fator = fator antigo * (refueledGas / litros gastos no sistema).
       Se foram colocados mais litros do que o sistema calculou, o fator
       aumenta; se foram menos, diminui. Assim o cálculo fica mais preciso.
    3. O tanque volta para cheio (gasolineLevel = tankCapacity).
    4. sync_version aumenta, para a ESP receber os valores novos.
    """
    serializer = RecalculateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    refueled_gas = serializer.validated_data["refueledGas"]

    with transaction.atomic():
        device = get_own_device(request)
        if device is None:
            return Response({"detail": "ESP não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        liters_spent = device.tankCapacity - device.gasolineLevel
        if liters_spent <= 0:
            # Tanque cheio: o sistema não registrou consumo, então não há como recalcular
            return Response(
                {"detail": "O tanque já está cheio no sistema; não há consumo para recalcular o fator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device.fuelConsumptionFactor = device.fuelConsumptionFactor * (refueled_gas / liters_spent)
        device.gasolineLevel = device.tankCapacity
        device.sync_version += 1
        device.save()

    return Response()


@api_view(["POST"])
def reset_trip(request):
    """Zera a distância e o consumo da viagem (totalDistance e tripConsumption)."""
    with transaction.atomic():
        device = get_own_device(request)
        if device is None:
            return Response({"detail": "ESP não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        device.totalDistance = 0
        device.tripConsumption = 0
        device.sync_version += 1  # para a ESP receber os valores zerados
        device.save()

    return Response()
