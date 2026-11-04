# OBDII Retrofit Instrumentation — Backend (v1.1)

API em Python/Django que recebe os dados de combustível enviados pela ESP32,
guarda num banco MySQL/MariaDB e os entrega para o site (Frontend em React na Vercel).

```
ESP32 ──(HTTP/JSON)──► Backend (Django) ──► MySQL / MariaDB
                              ▲
Site (React, Vercel) ─────────┘
```

Na versão 1.0, a ESP32 envia os dados apenas com o carro desligado. Por isso o
backend trabalha só com os dados persistentes de combustível, além das contas
de usuário.

A versão 1.1 acrescenta o **modo diagnóstico**: o usuário liga o modo pelo site
e a ESP passa a ler os códigos de erro (DTCs) do carro. A versão 1.0 continua
disponível na release `v1.0` do GitHub.

## Estrutura do projeto

| Pasta      | O que tem                                                         |
|------------|-------------------------------------------------------------------|
| `config/`  | Configurações do projeto: banco de dados, CORS, rotas principais  |
| `users/`   | Contas de usuário, login e logout                                 |
| `devices/` | Dados das ESP32 e vínculo entre usuário e ESP                     |
| `dtcs/`    | Códigos de erro (DTCs) lidos do carro e a base de erros           |

Dentro de cada app:

| Arquivo          | Para que serve                                              |
|------------------|-------------------------------------------------------------|
| `models.py`      | Tabelas do banco                                            |
| `serializers.py` | Validação do JSON que chega e montagem do JSON de resposta  |
| `views.py`       | O que cada endpoint faz                                     |
| `urls.py`        | O endereço (rota) de cada endpoint                          |

## Tabelas

| Tabela               | Campos                                                                                                      |
|----------------------|-------------------------------------------------------------------------------------------------------------|
| **User**             | ID_USER, name, password, email, isAdm                                                                       |
| **User-VehicleData** | ID, ID_ESP, ID_USER (liga um usuário a uma ESP)                                                             |
| **VehicleData**      | ID_ESP (MAC), name, gasolineLevel, tankCapacity, fuelConsumptionFactor, totalDistance, tripConsumption, sync_version, diagnoseMode |

| **DTC**              | ID, ID_ESP, code, receivedAt (os códigos de erro que a ESP leu do carro)                                    |
| **DTCDescription**   | code, title, description (base de erros, em português)                                                     |

Um usuário pode ter várias ESPs, e uma ESP pode estar ligada a mais de um usuário.

## Endpoints

| Método | Rota                                       | Quem usa | O que faz                                                    | Situação     |
|--------|--------------------------------------------|----------|--------------------------------------------------------------|--------------|
| GET    | `/user`                                    | ADM      | Lista todos os usuários                                      | A implementar |
| POST   | `/user`                                    | Site     | Cria a conta e devolve o Token (login automático)            | Pronto       |
| POST   | `/user/login`                              | Site     | Faz login e devolve o Token                                  | Pronto       |
| POST   | `/user/logout`                             | Site     | Invalida o Token                                             | Pronto       |
| POST   | `/user/addDevice`                          | Site     | Liga uma ESP à conta do usuário                              | Pronto       |
| GET    | `/devices?idDevice=`                       | Site     | Lista as ESPs do usuário (o ADM vê todas)                    | Pronto       |
| PUT    | `/devices?idDevice=`                       | Site     | Altera o nome e/ou a capacidade do tanque da ESP             | Pronto (v1.1) |
| POST   | `/devices/<idDevice>`                      | ESP32    | Envia os dados e recebe de volta os valores do banco         | Pronto       |
| POST   | `/devices/resetAndRecalculate?idDevice=`   | Site     | Recalcula o fator de consumo e volta o tanque para cheio     | Pronto       |
| POST   | `/devices/resetTrip?idDevice=`             | Site     | Zera a distância e o consumo da viagem                       | Pronto       |
| POST   | `/devices/setOperationMode?idDevice=`      | Site     | Liga ou desliga o modo diagnóstico                           | Pronto (v1.1) |
| POST   | `/devices/sendDTCs?idDevice=`              | ESP32    | Envia os códigos de erro lidos do carro                      | Pronto (v1.1) |
| GET    | `/devices/getDTCs?idDevice=`               | Site     | Lista os códigos de erro, com título e descrição             | Pronto (v1.1) |

### Identificação da ESP

Cada ESP32 é identificada pelo seu **MAC address**, no formato `AA:BB:CC:DD:EE:FF`.
O MAC já vem gravado de fábrica na placa e é único, então não precisa ser gerado
nem configurado. O backend também aceita o MAC em minúsculas ou com outros
separadores (`aa-bb-cc-dd-ee-ff`, `AABBCCDDEEFF`) e o salva sempre no formato padrão.

### Token (login)

Criar conta e fazer login devolvem um **Token**. Nos endpoints que exigem login,
o site envia o Token no cabeçalho da requisição:

```
Authorization: Token <token>
```

Sem o Token (ou com um Token inválido), a resposta é **401**.

### Códigos de resposta

| Código | Quando                                     |
|--------|--------------------------------------------|
| 200    | Deu certo                                  |
| 400    | Dados inválidos ou faltando                |
| 401    | Sem Token ou Token inválido                |
| 403    | Usuário sem permissão (não é ADM)          |
| 404    | ESP não encontrada                         |

### POST `/user` — criar conta

Envia:
```json
{ "name": "Nome do usuário", "password": "senha", "email": "email@exemplo.com" }
```
Recebe (200):
```json
{ "Token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" }
```
Erro 400 se faltar algum campo ou se o e-mail já tiver conta.

### POST `/user/login` — login

Envia:
```json
{ "email": "email@exemplo.com", "password": "senha" }
```
Recebe (200):
```json
{ "Token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" }
```
Erro 400 se o e-mail ou a senha estiverem errados.

### POST `/user/logout` — logout

Exige o Token. Não envia corpo. Recebe 200, e o Token deixa de funcionar.

### POST `/user/addDevice` — ligar uma ESP à conta

Exige o Token. Envia o MAC da ESP e o nome que o usuário quer dar a ela:
```json
{ "idDevice": "AA:BB:CC:DD:EE:FF", "name": "Gol do Rafael" }
```
Recebe 200. Erro 400 se o MAC for inválido ou se faltar o `name`, e 404 se a ESP
não existir no banco (a ESP passa a existir quando envia os dados pela primeira vez).

### GET `/devices?idDevice=` — listar as ESPs

Exige o Token. O usuário comum recebe só as ESPs ligadas à conta dele; o ADM
recebe todas. Com `?idDevice=<MAC>`, a resposta traz só aquela ESP.

Recebe (200):
```json
{
  "device": [
    {
      "idDevice": "AA:BB:CC:DD:EE:FF",
      "name": "Gol do Rafael",
      "gasolineLevel": 38.2,
      "tankCapacity": 55.0,
      "fuelConsumptionFactor": 0.008,
      "totalDistance": 120.3,
      "tripConsumption": 9.8,
      "diagnoseMode": false
    }
  ],
  "totalDevice": 1
}
```
Erro 404 se o `idDevice` informado não estiver entre as ESPs que o usuário pode ver.

### POST `/devices/<idDevice>` — envio da ESP32

Não exige Token: a ESP se identifica pelo MAC no endereço. Ela envia os 5 dados
de combustível e o seu `sync_version`:

```json
{
  "gasolineLevel": 38.2,
  "tankCapacity": 55,
  "fuelConsumptionFactor": 0.008,
  "totalDistance": 120.3,
  "tripConsumption": 9.8,
  "sync_version": 0
}
```

Recebe (200) os valores que estão no banco, no mesmo formato, e mais o
`diagnoseMode` (`true` ou `false`). Quando vier `true`, a ESP lê os códigos de
erro (DTCs) do carro. A ESP não envia o `diagnoseMode`: quem o altera é o site.
Erro 400 se faltar algum campo ou se o MAC for inválido.

**Como funciona a sincronização:**

- Se a ESP ainda não existe no banco, ela é cadastrada com os dados enviados.
- Se o `sync_version` enviado é **igual** ao do banco, o banco salva os dados da ESP.
- Se é **diferente** (porque o site alterou os dados, por exemplo num reset),
  o banco ignora os dados da ESP.
- Nos dois casos, a resposta traz os valores do banco. Se o `sync_version` da
  resposta for diferente do dela, a ESP grava esses valores na memória dela.

### POST `/devices/resetAndRecalculate?idDevice=` — recalcular o fator

Exige o Token. Pode ser usado pelo dono da ESP ou por um ADM. Depois de encher o tanque, o usuário
informa quantos litros colocou:

```json
{ "refueledGas": 33 }
```

O backend então:

1. calcula os litros gastos no sistema: `tankCapacity − gasolineLevel`;
2. calcula o novo fator:
   `Novo Fator = Fator Antigo × (refueledGas / Litros Gastos no Sistema)`;
3. volta o tanque para cheio (`gasolineLevel = tankCapacity`);
4. aumenta o `sync_version`, para a ESP receber os valores novos.

O `tripConsumption` não é zerado aqui: ele serve para o km/L da viagem.

Recebe 200 (sem corpo). Erro 400 se faltar o `refueledGas`, se ele não for maior
que zero ou se o tanque já estiver cheio no sistema (não há consumo para recalcular),
e 404 se a ESP não existir ou não estiver ligada à conta do usuário (para o ADM, só se não existir).

**Exemplo:** tanque de 55 L com 25 L no sistema (o sistema acha que gastou 30 L).
O usuário colocou 33 L para encher. Novo fator = 0.008 × 33 / 30 = 0.0088.

### POST `/devices/resetTrip?idDevice=` — zerar a viagem

Exige o Token. Pode ser usado pelo dono da ESP ou por um ADM. Não envia corpo.
Zera o `totalDistance` e o `tripConsumption` e aumenta o `sync_version`, para a
ESP receber os valores zerados.

Recebe 200 (sem corpo). Erro 404 se a ESP não existir ou não estiver ligada à conta do usuário (para o ADM, só se não existir).

### PUT `/devices?idDevice=` — alterar a ESP

Exige o Token. Pode ser usado pelo dono da ESP ou por um ADM. Envia o nome e/ou a
capacidade do tanque (pelo menos um dos dois):

```json
{ "name": "Gol do Rafael", "tankCapacity": 50 }
```

- Se a `tankCapacity` mudar, o `sync_version` aumenta, para a ESP receber o valor novo.
- Se a gasolina passar da nova capacidade, ela é ajustada para a capacidade.

Recebe 200 (sem corpo). Erro 400 se não enviar nenhum campo ou se a `tankCapacity`
não for maior que zero, e 404 se a ESP não existir ou não estiver ligada à conta
do usuário (para o ADM, só se não existir).

### POST `/devices/setOperationMode?idDevice=` — modo diagnóstico

Exige o Token. Pode ser usado pelo dono da ESP ou por um ADM. Liga ou desliga o
modo diagnóstico:

```json
{ "diagnoseMode": true }
```

A ESP fica sabendo na resposta do próximo envio dela. O modo só é desligado pelo
site (`{ "diagnoseMode": false }`).

Recebe 200 (sem corpo). Erro 400 se faltar o `diagnoseMode` e 404 se a ESP não
existir ou não estiver ligada à conta do usuário (para o ADM, só se não existir).

### Modo diagnóstico: como funciona

1. O usuário liga o modo pelo site (`POST /devices/setOperationMode`).
2. A ESP recebe `diagnoseMode: true` na resposta do envio de dados dela.
3. A ESP lê os códigos de erro (DTCs) do carro e os envia (`POST /devices/sendDTCs`).
4. O site mostra os erros, com título e descrição (`GET /devices/getDTCs`).

### POST `/devices/sendDTCs?idDevice=` — envio dos DTCs pela ESP32

Não exige Token: a ESP se identifica pelo MAC no `idDevice`. Ela envia a lista de
códigos de erro que leu do carro:

```json
{ "dtcs": ["P0301", "P0420"] }
```

- A lista nova **substitui** a anterior: o carro sempre informa todos os erros
  ativos, então um erro que não vier mais já foi resolvido.
- A lista pode ser vazia (`[]`): o carro não tem nenhum erro ativo.
- Os códigos são padronizados em maiúsculas, e os repetidos são ignorados.

Recebe 200 (sem corpo). Erro 400 se faltar a lista, se algum código não estiver no
formato (letra P, C, B ou U + 4 caracteres, ex.: `P0301`) ou se o MAC for inválido,
e 404 se a ESP não existir no banco.

### GET `/devices/getDTCs?idDevice=` — erros para o site

Exige o Token. Pode ser usado pelo dono da ESP ou por um ADM.

Recebe (200):
```json
{
  "dtcs": [
    {
      "code": "P0301",
      "title": "Falha de ignição no cilindro 1",
      "description": "A combustão está falhando no cilindro 1. Verificar vela, bobina/cabo e bico injetor desse cilindro.",
      "receivedAt": "2026-10-31T10:00:00-03:00"
    }
  ],
  "totalDtcs": 1
}
```

Se um código não estiver na base de erros, ele vem com o título
`"Código não encontrado na base"` e a descrição vazia.
Erro 404 se a ESP não existir ou não estiver ligada à conta do usuário
(para o ADM, só se não existir).

### Base de erros

A base fica em `dtcs/dtc_base.py`: códigos genéricos de OBD-II (padrão para
todos os carros), com título e descrição em português. Ela é carregada no banco
automaticamente pelo `migrate`. Para acrescentar códigos, inclua novos itens na
lista e crie uma nova migration de dados que carregue a lista de novo.

## Como rodar no computador

Pré-requisito: Python 3.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

O backend fica disponível em <http://127.0.0.1:8000>.

O `migrate` cria as tabelas no banco. Ele só precisa ser rodado na primeira vez
e sempre que surgir uma tabela ou coluna nova no código.

### Criar o administrador (ADM)

Não existe endpoint para criar um ADM. Ele é criado pelo terminal:

```bash
python manage.py createsuperuser
```

O comando pede o e-mail, o nome e a senha, e cria o usuário com `isAdm = True`.

## Configuração (`.env`)

As configurações ficam no arquivo `.env`, que **não vai para o GitHub** porque
guarda senhas. O modelo está em `.env.example`.

| Variável               | O que é                                                    |
|------------------------|------------------------------------------------------------|
| `DJANGO_SECRET_KEY`    | Chave secreta do Django (no servidor, usar uma nova)       |
| `DJANGO_DEBUG`         | `True` no computador, `False` no servidor                  |
| `DJANGO_ALLOWED_HOSTS` | Endereços pelos quais o backend pode ser acessado          |
| `CORS_ALLOWED_ORIGINS` | Endereços do site autorizados a chamar o backend (Vercel)  |
| `DB_HOST`              | Endereço do MySQL/MariaDB. **Vazio = usa o banco local (SQLite)** |
| `DB_PORT`              | Porta do MySQL (3306)                                      |
| `DB_NAME`              | Nome do banco (`obdii`)                                    |
| `DB_USER`              | Usuário do banco                                           |
| `DB_PASSWORD`          | Senha do banco                                             |
| `DB_SSL_CA`            | Certificado SSL do banco (ex.: `global-bundle.pem` da AWS). **Vazio = conecta sem certificado** |

### Usando o banco da AWS

1. Preencha `DB_HOST`, `DB_USER` e `DB_PASSWORD` no `.env`.
2. Baixe o certificado da AWS para a pasta do projeto:
   ```bash
   curl -o global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
   ```
3. Teste a conexão:
   ```bash
   python manage.py check --database default
   ```

Algumas redes (por exemplo, de faculdades) bloqueiam a porta 3306 do MySQL.
Nesse caso, use outra rede ou o banco local.

## Rodando no servidor (AWS)

1. Configure as variáveis do `.env.example` no servidor, com `DJANGO_DEBUG=False`,
   uma `DJANGO_SECRET_KEY` nova, o domínio da API em `DJANGO_ALLOWED_HOSTS` e o
   domínio da Vercel em `CORS_ALLOWED_ORIGINS`.
2. Instale as dependências: `pip install -r requirements.txt`
3. Inicie o servidor:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```
