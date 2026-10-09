"""
Views do app de usuários.

Uma view é a função que executa um endpoint: recebe a requisição, faz o
trabalho e devolve a resposta.

Endpoints deste app:
- POST /user            cria uma conta e devolve o Token
- POST /user/login      faz login e devolve o Token
- POST /user/logout     invalida o Token
- POST /user/addDevice  liga uma ESP à conta do usuário

O Token é a "chave" do usuário logado. O site guarda o Token e o envia
nas próximas requisições no cabeçalho: Authorization: Token <token>
"""

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from devices.models import UserVehicleData, VehicleData

from .models import User
from .serializers import AddDeviceSerializer, CreateUserSerializer, LoginSerializer


@api_view(["POST"])
@permission_classes([AllowAny])  # qualquer pessoa pode criar uma conta
def create_user(request):
    """Cria a conta e já faz o login, devolvendo o Token."""
    serializer = CreateUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # dados inválidos -> 400
    user = serializer.save()

    token = Token.objects.create(user=user)
    return Response({"Token": token.key})


@api_view(["POST"])
@permission_classes([AllowAny])  # o login é feito justamente por quem ainda não tem Token
def login(request):
    """Confere o e-mail e a senha e devolve o Token do usuário."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = User.objects.filter(email=serializer.validated_data["email"]).first()
    if user is None or not user.check_password(serializer.validated_data["password"]):
        return Response({"detail": "E-mail ou senha inválidos."}, status=status.HTTP_400_BAD_REQUEST)

    # Reaproveita o Token se o usuário já tiver um; se não, cria um novo
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"Token": token.key})


@api_view(["POST"])
def logout(request):
    """Apaga o Token: a partir daí ele não serve mais para acessar o sistema."""
    request.auth.delete()  # request.auth é o Token enviado no cabeçalho
    return Response()


@api_view(["POST"])
def add_device(request):
    """Liga uma ESP (pelo MAC) à conta do usuário dono do Token."""
    serializer = AddDeviceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # A ESP precisa já existir no banco (ela é criada quando envia os dados)
    device = VehicleData.objects.filter(id=serializer.validated_data["idDevice"]).first()
    if device is None:
        return Response({"detail": "ESP não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    # get_or_create: se a ESP já estiver ligada a este usuário, não duplica
    UserVehicleData.objects.get_or_create(user=request.user, device=device)
    return Response()
