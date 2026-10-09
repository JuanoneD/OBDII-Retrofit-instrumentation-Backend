"""
Views do app de usuários.

Uma view é a função que executa um endpoint: recebe a requisição, faz o
trabalho e devolve a resposta.

Endpoints deste app:
- GET  /user            lista todos os usuários (somente ADM)
- POST /user            cria uma conta e devolve o Token
- POST /user/login      faz login e devolve o Token
- POST /user/logout     invalida o Token
- POST /user/addDevice  liga uma ESP à conta do usuário
"""
