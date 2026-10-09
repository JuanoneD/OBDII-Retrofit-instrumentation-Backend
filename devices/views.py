"""
Views do app de dispositivos.

Uma view é a função que executa um endpoint: recebe a requisição, faz o
trabalho e devolve a resposta.

Endpoints deste app:
- GET  /devices                           lista as ESPs do usuário (ADM vê todas)
- POST /devices/<idDevice>                a ESP32 envia os seus dados
- POST /devices/resetAndRecalculate       recalcula o fator e enche o tanque
- POST /devices/resetTrip                 zera a distância e o consumo da viagem
"""
