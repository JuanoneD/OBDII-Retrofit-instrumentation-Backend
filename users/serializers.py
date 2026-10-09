"""
Serializers do app de usuários.

Um serializer converte os dados entre JSON e Python: valida o JSON que chega
nas requisições e monta o JSON das respostas. Se algum campo estiver faltando
ou for inválido, o endpoint responde 400 dizendo qual campo está errado.
"""

from rest_framework import serializers

from devices.models import normalize_mac

from .models import User


class CreateUserSerializer(serializers.ModelSerializer):
    """JSON para criar conta: {name, password, email}."""

    class Meta:
        model = User
        fields = ["name", "password", "email"]
        # A senha só é recebida, nunca devolvida nas respostas
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # create_user guarda a senha criptografada
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """JSON de login: {email, password}."""

    email = serializers.EmailField()
    password = serializers.CharField()


class AddDeviceSerializer(serializers.Serializer):
    """JSON para ligar uma ESP à conta: {idDevice}."""

    idDevice = serializers.CharField()

    def validate_idDevice(self, value):
        mac = normalize_mac(value)
        if mac is None:
            raise serializers.ValidationError("idDevice deve ser o MAC da ESP, ex.: AA:BB:CC:DD:EE:FF")
        return mac
