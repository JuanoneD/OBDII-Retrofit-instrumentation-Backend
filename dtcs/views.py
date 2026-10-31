"""
Views do app de códigos de erro (DTCs).

Uma view é a função que executa um endpoint: recebe a requisição, faz o
trabalho e devolve a resposta.

Endpoints deste app:
- POST /devices/sendDTCs?idDevice=   a ESP32 envia os códigos de erro lidos do carro
- GET  /devices/getDTCs?idDevice=    o site busca os erros, com título e descrição

Como funciona o modo diagnóstico:
1. o usuário liga o modo pelo site (POST /devices/setOperationMode);
2. a ESP recebe diagnoseMode = true na resposta do envio de dados dela;
3. a ESP lê os códigos de erro do carro e os envia (POST /devices/sendDTCs);
4. o site mostra os erros (GET /devices/getDTCs).
"""

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from devices.models import VehicleData, normalize_mac

from .models import DTC, DTCDescription
from .serializers import SendDTCsSerializer

# Título usado quando o código não está na base de erros
UNKNOWN_TITLE = "Código não encontrado na base"


@api_view(["POST"])
@permission_classes([AllowAny])  # a ESP não faz login, ela se identifica pelo MAC
def send_dtcs(request):
    """
    A ESP envia a lista de códigos de erro que leu do carro.

    A lista nova SUBSTITUI a anterior: o carro sempre informa todos os erros
    ativos, então um erro que não vier mais na lista já foi resolvido.
    """
    mac = normalize_mac(request.query_params.get("idDevice", ""))
    if mac is None:
        return Response(
            {"detail": "idDevice deve ser o MAC da ESP, ex.: AA:BB:CC:DD:EE:FF"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = SendDTCsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # lista faltando ou código inválido -> 400
    codes = serializer.validated_data["dtcs"]

    device = VehicleData.objects.filter(id=mac).first()
    if device is None:
        return Response({"detail": "ESP não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    # Apaga a lista antiga e grava a nova, tudo de uma vez
    with transaction.atomic():
        DTC.objects.filter(device=device).delete()
        DTC.objects.bulk_create([DTC(device=device, code=code) for code in codes])

    return Response()


@api_view(["GET"])
def get_dtcs(request):
    """
    Devolve os códigos de erro da ESP, com o título e a descrição de cada um
    (buscados na base de erros).

    Pode ser usado pelo dono da ESP ou por um ADM.
    """
    mac = normalize_mac(request.query_params.get("idDevice", ""))
    devices = VehicleData.objects.filter(id=mac)
    if not request.user.isAdm:
        devices = devices.filter(uservehicledata__user=request.user)
    device = devices.first()
    if device is None:
        return Response({"detail": "ESP não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    dtcs = list(DTC.objects.filter(device=device))
    # Busca na base de erros, de uma vez, as descrições dos códigos recebidos
    descriptions = DTCDescription.objects.in_bulk([dtc.code for dtc in dtcs])

    result = []
    for dtc in dtcs:
        info = descriptions.get(dtc.code)
        result.append({
            "code": dtc.code,
            "title": info.title if info else UNKNOWN_TITLE,
            "description": info.description if info else "",
            "receivedAt": dtc.receivedAt,
        })

    return Response({"dtcs": result, "totalDtcs": len(result)})
