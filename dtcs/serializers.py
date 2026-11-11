"""
Serializers do app de códigos de erro (DTCs).

Um serializer converte os dados entre JSON e Python: valida o JSON que chega
nas requisições e monta o JSON das respostas. Se algum campo estiver faltando
ou for inválido, o endpoint responde 400 dizendo qual campo está errado.
"""

from rest_framework import serializers

from .models import DetectedError, normalize_dtc


class SendDTCsSerializer(serializers.Serializer):
    """
    JSON que a ESP envia: {dtcs: ["P0301", "P0420"]}.

    A lista pode ser vazia: significa que o carro não tem nenhum erro ativo.
    """

    dtcs = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    def validate_dtcs(self, value):
        codes = []
        for item in value:
            code = normalize_dtc(item)
            if code is None:
                raise serializers.ValidationError(
                    f"Código inválido: {item!r}. Formato esperado: letra P, C, B ou U + 4 caracteres (ex.: P0301)."
                )
            if code not in codes:  # ignora códigos repetidos na mesma lista
                codes.append(code)
        return codes


class AddDetectErrorSerializer(serializers.Serializer):
    """JSON que a ESP envia ao detectar uma falha: {title, description}."""

    title = serializers.CharField(max_length=200)
    description = serializers.CharField()


class DetectedErrorSerializer(serializers.ModelSerializer):
    """Uma falha detectada, como o site recebe (GET /devices/getDetectErrors)."""

    class Meta:
        model = DetectedError
        fields = ["title", "description", "detectedAt"]
