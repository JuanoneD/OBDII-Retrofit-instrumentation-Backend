# OBDII Retrofit Instrumentation — Backend

API em Django que recebe a telemetria da ESP32 (lida via OBD-II), armazena no MySQL (AWS RDS) e a disponibiliza para o Frontend (React/Vercel). Também controla o nível de combustível do veículo e recalcula o fator de consumo a cada abastecimento.

## Sumário

- [Arquitetura](#arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Início rápido](#início-rápido)
- [Configuração](#configuração)
- [Identificação do dispositivo (BE-05)](#identificação-do-dispositivo-be-05)
- [Referência da API](#referência-da-api)
  - [Formato de erro](#formato-de-erro)
  - [Dispositivos](#dispositivos)
  - [Ingestão de telemetria (ESP32)](#ingestão-de-telemetria-esp32)
  - [Leitura de telemetria](#leitura-de-telemetria)
  - [Combustível](#combustível)
- [Sincronização após abastecimento](#sincronização-após-abastecimento)
- [Testes](#testes)
- [Deploy na AWS](#deploy-na-aws)

## Arquitetura

```
ESP32 --(POST JSON)--> Backend (Django, AWS) --> MySQL (AWS RDS)
                              ^
Frontend (Vercel) --(GET/POST)-+
```

| Componente | Papel                                                          |
|------------|----------------------------------------------------------------|
| ESP32      | Lê os dados do carro e envia leituras periódicas via HTTP      |
| Backend    | Valida, armazena e serve os dados; calcula o combustível       |
| Frontend   | Painel do usuário (cadastro de veículos, telemetria, abastecimento) |

## Estrutura do projeto

| Pasta        | Conteúdo                                                          |
|--------------|-------------------------------------------------------------------|
| `config/`    | Configurações do projeto (banco, CORS, variáveis de ambiente)     |
| `telemetry/` | Veículos/dispositivos (BE-05), ingestão (BE-02) e leitura (BE-03) |
| `fuel/`      | Recálculo do fator de combustível (BE-04)                         |

## Início rápido

**Pré-requisito:** Python 3.

<details open>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser   # usuário para o painel /admin
python manage.py runserver
```

</details>

<details>
<summary><strong>Linux / macOS</strong></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser   # usuário para o painel /admin
python manage.py runserver
```

</details>

Depois de subir o servidor:

- API (dá para testar pelo navegador): <http://127.0.0.1:8000/api/devices/>
- Painel administrativo (ver/editar dados): <http://127.0.0.1:8000/admin/>

## Configuração

As variáveis ficam no arquivo `.env` (modelo em `.env.example`).

| Variável                | Descrição                                              | Produção                    |
|-------------------------|--------------------------------------------------------|-----------------------------|
| `DJANGO_DEBUG`          | Modo debug                                             | `False`                     |
| `DJANGO_SECRET_KEY`     | Chave secreta do Django                                | Gerar uma nova              |
| `DJANGO_ALLOWED_HOSTS`  | Domínios permitidos                                    | Domínio da API              |
| `CORS_ALLOWED_ORIGINS`  | Origens permitidas pelo CORS                           | Domínio da Vercel           |
| `DB_HOST`               | Host do MySQL. **Se vazio, usa SQLite** (`db.sqlite3`) | Endpoint do RDS             |
| `DB_NAME`               | Nome do banco                                          |                             |
| `DB_USER`               | Usuário do banco                                       |                             |
| `DB_PASSWORD`           | Senha do banco                                         |                             |

### Usando o MySQL da AWS (RDS)

1. Preencha `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` no `.env`.
2. Baixe o certificado [`global-bundle.pem`](https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem) para a pasta do projeto.
3. Rode `python manage.py migrate` para criar as tabelas.

## Identificação do dispositivo (BE-05)

Opções avaliadas:

| Opção                          | Prós                                  | Contras                                |
|--------------------------------|---------------------------------------|----------------------------------------|
| **MAC address da ESP32** ✅    | Já vem de fábrica, único, zero config | Pode ser copiado por quem souber o MAC |
| UUID gerado e salvo na NVS     | Único                                 | Some se a NVS for apagada; precisa ser gerado |
| ID cadastrado manualmente      | Controle total                        | Precisa gravar o ID em cada ESP32      |

**Decisão:** o MAC (`WiFi.macAddress()` / `ESP.getEfuseMac()`) é o `device_id`.

- O dispositivo precisa ser cadastrado antes (`POST /api/devices/`, tela FE-04), vinculando o MAC a um veículo.
- Todo envio da ESP32 é recusado se o MAC não estiver cadastrado e ativo.
- O MAC é aceito em qualquer formato (`aa-bb-cc-dd-ee-ff`, `aabbccddeeff`) e é salvo como `AA:BB:CC:DD:EE:FF`.

## Referência da API

Base: `/api/`

| Método | Rota                                             | Card  | Quem usa |
|--------|--------------------------------------------------|-------|----------|
| GET    | `/api/health/`                                   | BE-01 | AWS      |
| GET    | `/api/devices/`                                  | BE-05 | Frontend |
| POST   | `/api/devices/`                                  | BE-05 | Frontend |
| GET    | `/api/devices/<device_id>/`                      | BE-05 | Frontend |
| PATCH  | `/api/devices/<device_id>/`                      | BE-05 | Frontend |
| POST   | `/api/telemetry/ingest/`                         | BE-02 | ESP32    |
| GET    | `/api/telemetry/latest/?device_id=...`           | BE-03 | Frontend |
| GET    | `/api/telemetry/history/?device_id=...&limit=50` | BE-03 | Frontend |
| GET    | `/api/fuel/status/?device_id=...`                | BE-04 | Frontend |
| POST   | `/api/fuel/recalculate/`                         | BE-04 | Frontend |

### Formato de erro

Todos os erros seguem o mesmo formato:

```json
{ "status": "error", "code": "...", "message": "...", "errors": { } }
```

Códigos conhecidos:

| HTTP | `code`                   | Onde ocorre          | Significado                                   |
|------|--------------------------|----------------------|-----------------------------------------------|
| 400  | `invalid_payload`        | ingest               | JSON incompleto/inválido (`errors` diz o campo) |
| 400  | `no_consumption_recorded`| fuel/recalculate     | Nenhum consumo registrado ainda               |
| 400  | `liters_above_capacity`  | fuel/recalculate     | Litros inseridos acima da capacidade do tanque |
| 404  | `device_not_registered`  | ingest, fuel         | MAC não cadastrado ou inativo                 |

### Dispositivos

#### Cadastrar — `POST /api/devices/`

```json
{
  "device_id": "AA:BB:CC:DD:EE:FF",
  "name": "Gol do Juan",
  "plate": "ABC1D23",
  "model": "Gol 1.0 2012",
  "owner_name": "Juan",
  "tank_capacity": 45
}
```

- Obrigatórios: `device_id`, `name`.
- Resposta `201` com o veículo; `400` se o MAC for inválido ou já cadastrado.

```bash
curl -X POST http://127.0.0.1:8000/api/devices/ \
  -H "Content-Type: application/json" \
  -d '{"device_id": "AA:BB:CC:DD:EE:FF", "name": "Gol do Juan", "tank_capacity": 45}'
```

### Ingestão de telemetria (ESP32)

`POST /api/telemetry/ingest/` — contrato para o ESP-03.

```json
{
  "device_id": "AA:BB:CC:DD:EE:FF",
  "timestamp": "2026-10-03T12:00:00-03:00",
  "rpm": 850,
  "speed": 0,
  "coolant_temp": 90,
  "engine_load": 25.5,
  "throttle_position": 12.0,
  "ltft": -2.3,
  "timing_advance": 10.0,
  "module_voltage": 13.8,
  "map_pressure": 35.0,
  "gasoline_level": 30.2,
  "tank_capacity": 45.0,
  "fuel_consumption_factor": 0.008,
  "total_distance": 1234.5,
  "trip_consumption": 4.2,
  "sync_version": 0
}
```

| Campo                     | Origem na ESP32 (`VehicleData`)            | Obrigatório               |
|---------------------------|--------------------------------------------|---------------------------|
| `device_id`               | MAC da ESP32                               | sim                       |
| `timestamp`               | hora do envio (se souber)                  | não (usa hora de chegada) |
| `rpm`                     | `getEngineRPM()`                           | sim                       |
| `speed`                   | `getVehicleSpeed()`                        | sim                       |
| `coolant_temp`            | `getCoolantTemp()`                         | sim                       |
| `engine_load`             | `getEngineLoad()`                          | sim                       |
| `throttle_position`       | `getThrottlePosition()`                    | sim                       |
| `ltft`                    | `getLongTermFuelTrim()`                    | sim                       |
| `timing_advance`          | `getTimingAdvance()`                       | não                       |
| `module_voltage`          | `getModuleVoltage()`                       | não                       |
| `map_pressure`            | `getMapPressure()`                         | não                       |
| `gasoline_level`          | `getGasolineLevel()` (NVS)                 | sim                       |
| `tank_capacity`           | `getTankCapacity()` (NVS)                  | sim                       |
| `fuel_consumption_factor` | `getFuelConsumptionFactor()` (NVS)         | sim                       |
| `total_distance`          | `getTotalDistance()` (NVS)                 | sim                       |
| `trip_consumption`        | `getTripConsumption()` (NVS)               | sim                       |
| `sync_version`            | último `sync.sync_version` aplicado (NVS)  | não (padrão `0`)          |

**Respostas**

- `201` — recebido e salvo. A ESP32 pode descartar o que já enviou.

  ```json
  { "status": "ok", "reading_id": 123, "received_at": "...", "sync": null }
  ```

- `400` `invalid_payload` — JSON incompleto/inválido.
- `404` `device_not_registered` — MAC não cadastrado ou inativo.

### Leitura de telemetria

#### Mais recente — `GET /api/telemetry/latest/?device_id=...`

```json
{
  "vehicle": {
    "device_id": "AA:BB:CC:DD:EE:FF",
    "name": "Gol",
    "fuel_percent": 67.1,
    "gasoline_level": 30.2,
    "last_seen_at": "...",
    "...": "..."
  },
  "reading": {
    "sent_at": "...",
    "rpm": 850,
    "speed": 0,
    "coolant_temp": 90,
    "engine_load": 25.5,
    "throttle_position": 12.0,
    "ltft": -2.3,
    "fuel_percent": 67.1,
    "...": "..."
  }
}
```

- `reading` é `null` se o veículo ainda não enviou nada.
- Para exibir "sem dados recentes" (FE-02), compare `vehicle.last_seen_at` com a hora atual.

#### Histórico — `GET /api/telemetry/history/?device_id=...&limit=50`

Últimas N leituras (padrão 50, máximo 500), **da mais antiga para a mais nova**:

```json
{ "device_id": "...", "count": 50, "results": [ ] }
```

### Combustível

#### Status — `GET /api/fuel/status/?device_id=...`

```json
{
  "fuel_consumption_factor": 0.008,
  "liters_spent_system": 10.0,
  "gasoline_level": 20.0,
  "tank_capacity": 45.0,
  "fuel_percent": 44.4,
  "pending_sync": false,
  "last_refuels": [ ]
}
```

#### Recálculo do fator — `POST /api/fuel/recalculate/`

```json
{ "device_id": "AA:BB:CC:DD:EE:FF", "litrosInseridos": 12 }
```

```
Novo Fator = Fator Antigo × (Litros Inseridos / Litros Gastos no Sistema)
```

Depois do recálculo, o contador de litros gastos volta a zero e os litros inseridos são somados ao nível do tanque (limitado à capacidade).

```json
{
  "status": "ok",
  "old_factor": 0.008,
  "new_factor": 0.0096,
  "liters_inserted": 12,
  "liters_spent_system": 10.0,
  "gasoline_level": 32.0,
  "fuel_percent": 71.1,
  "refuel_id": 1
}
```

Erros: `400 no_consumption_recorded`, `400 liters_above_capacity`, `404 device_not_registered`.

## Sincronização após abastecimento

Quando o usuário recalcula o fator (BE-04), a próxima resposta do ingest traz o campo `sync` preenchido:

```json
"sync": {
  "sync_version": 1,
  "fuel_consumption_factor": 0.0096,
  "gasoline_level": 32.0,
  "trip_consumption": 0.0
}
```

A ESP32 deve:

1. Gravar os valores na NVS (`setFuelConsumptionFactor`, `setGasolineLevel`, `setTripConsumption`).
2. Guardar o `sync_version` recebido.
3. Passar a enviá-lo em todas as leituras seguintes.

Enquanto a ESP32 não confirmar (enviando o novo `sync_version`), o backend mantém os valores dele e `pending_sync` fica `true` em `/api/fuel/status/`.

```
Frontend            Backend                 ESP32
   |--recalculate-->|                          |
   |                |  (sync_version = 1)      |
   |                |<------ ingest (v=0) -----|
   |                |------- sync {v=1} ------>|  grava na NVS
   |                |<------ ingest (v=1) -----|  confirmado
```

## Testes

```bash
python manage.py test
```

## Deploy na AWS

1. Preencha as variáveis do `.env.example` no ambiente da AWS, com:
   - `DJANGO_DEBUG=False`
   - uma `DJANGO_SECRET_KEY` nova
   - o domínio da API em `DJANGO_ALLOWED_HOSTS`
   - o domínio da Vercel em `CORS_ALLOWED_ORIGINS`
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Prepare o banco e os arquivos estáticos:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
4. Inicie o servidor:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```
5. Confirme que está no ar: `GET /api/health/`.
