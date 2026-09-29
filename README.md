# OBDII Retrofit Instrumentation — Backend

API em Django que recebe os dados da ESP32 e entrega para o Frontend (React/Vercel).

```
ESP32 --(POST JSON)--> Backend (Django, AWS) --> MySQL (AWS RDS)
                              ^
Frontend (Vercel) --(GET/POST)-+
```

## Estrutura

| Pasta        | O que tem                                                              |
|--------------|------------------------------------------------------------------------|
| `config/`    | Configurações do projeto (banco, CORS, variáveis de ambiente)          |
| `telemetry/` | Veículos/dispositivos (BE-05), ingestão (BE-02) e leitura (BE-03)      |
| `fuel/`      | Recálculo do fator de combustível (BE-04)                              |

## Como rodar no seu PC (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser   # usuário para o painel /admin
python manage.py runserver
```

Abra http://127.0.0.1:8000/api/devices/ (dá para testar a API pelo navegador)
e http://127.0.0.1:8000/admin/ (painel para ver/editar os dados).

Rodar os testes automáticos: `python manage.py test`

### Usar o MySQL da AWS

No `.env`, preencha `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`, baixe o
certificado [`global-bundle.pem`](https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem)
para a pasta do projeto e rode `python manage.py migrate` (cria as tabelas).
Sem `DB_HOST`, o projeto usa SQLite (arquivo `db.sqlite3`).

## Identificação do dispositivo (BE-05)

Opções avaliadas:

| Opção                         | Prós                                   | Contras                                   |
|-------------------------------|----------------------------------------|-------------------------------------------|
| **MAC address da ESP32** ✅    | Já vem de fábrica, único, zero config  | Pode ser copiado por quem souber o MAC    |
| UUID gerado e salvo na NVS    | Único                                  | Some se a NVS for apagada; precisa gerar  |
| ID cadastrado manualmente     | Controle total                         | Precisa gravar o ID em cada ESP32         |

**Decisão:** o MAC (`WiFi.macAddress()` / `ESP.getEfuseMac()`) é o `device_id`.
O dispositivo precisa ser cadastrado antes (`POST /api/devices/`, tela FE-04),
vinculando o MAC a um veículo. Todo envio da ESP32 é recusado se o MAC não estiver
cadastrado e ativo. O MAC é aceito em qualquer formato (`aa-bb-cc-dd-ee-ff`,
`aabbccddeeff`) e salvo como `AA:BB:CC:DD:EE:FF`.

## Endpoints

Base: `/api/`. Todos os erros seguem o formato:
`{"status": "error", "code": "...", "message": "...", "errors": {...}}`

| Método | Rota                                           | Card  | Quem usa  |
|--------|------------------------------------------------|-------|-----------|
| GET    | `/api/health/`                                 | BE-01 | AWS       |
| GET    | `/api/devices/`                                | BE-05 | Frontend  |
| POST   | `/api/devices/`                                | BE-05 | Frontend  |
| GET    | `/api/devices/<device_id>/`                    | BE-05 | Frontend  |
| PATCH  | `/api/devices/<device_id>/`                    | BE-05 | Frontend  |
| POST   | `/api/telemetry/ingest/`                       | BE-02 | ESP32     |
| GET    | `/api/telemetry/latest/?device_id=...`         | BE-03 | Frontend  |
| GET    | `/api/telemetry/history/?device_id=...&limit=50` | BE-03 | Frontend |
| GET    | `/api/fuel/status/?device_id=...`              | BE-04 | Frontend  |
| POST   | `/api/fuel/recalculate/`                       | BE-04 | Frontend  |

### Cadastrar dispositivo — `POST /api/devices/`

```json
{ "device_id": "AA:BB:CC:DD:EE:FF", "name": "Gol do Juan", "plate": "ABC1D23",
  "model": "Gol 1.0 2012", "owner_name": "Juan", "tank_capacity": 45 }
```
Obrigatórios: `device_id`, `name`. Resposta `201` com o veículo; `400` se o MAC
for inválido ou já cadastrado.

### Envio da ESP32 — `POST /api/telemetry/ingest/` (contrato para o ESP-03)

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

| Campo                     | Origem na ESP32 (`VehicleData`) | Obrigatório |
|---------------------------|---------------------------------|-------------|
| `device_id`               | MAC da ESP32                    | sim         |
| `timestamp`               | hora do envio (se souber)       | não (usa hora de chegada) |
| `rpm`                     | `getEngineRPM()`                | sim         |
| `speed`                   | `getVehicleSpeed()`             | sim         |
| `coolant_temp`            | `getCoolantTemp()`              | sim         |
| `engine_load`             | `getEngineLoad()`               | sim         |
| `throttle_position`       | `getThrottlePosition()`         | sim         |
| `ltft`                    | `getLongTermFuelTrim()`         | sim         |
| `timing_advance`          | `getTimingAdvance()`            | não         |
| `module_voltage`          | `getModuleVoltage()`            | não         |
| `map_pressure`            | `getMapPressure()`              | não         |
| `gasoline_level`          | `getGasolineLevel()` (NVS)      | sim         |
| `tank_capacity`           | `getTankCapacity()` (NVS)       | sim         |
| `fuel_consumption_factor` | `getFuelConsumptionFactor()` (NVS) | sim      |
| `total_distance`          | `getTotalDistance()` (NVS)      | sim         |
| `trip_consumption`        | `getTripConsumption()` (NVS)    | sim         |
| `sync_version`            | último `sync.sync_version` aplicado (NVS) | não (padrão 0) |

Respostas:

- `201` — recebido e salvo. A ESP32 pode descartar o que já enviou.
  ```json
  { "status": "ok", "reading_id": 123, "received_at": "...", "sync": null }
  ```
- `400` `invalid_payload` — JSON incompleto/inválido (`errors` diz qual campo).
- `404` `device_not_registered` — MAC não cadastrado ou inativo.

**Sincronização após abastecimento:** quando o usuário recalcula o fator (BE-04),
a próxima resposta do ingest traz `sync` preenchido:

```json
"sync": { "sync_version": 1, "fuel_consumption_factor": 0.0096,
          "gasoline_level": 32.0, "trip_consumption": 0.0 }
```

A ESP32 deve gravar esses valores na NVS (`setFuelConsumptionFactor`,
`setGasolineLevel`, `setTripConsumption`), guardar o `sync_version` e passar a
enviá-lo. Enquanto ela não confirmar, o backend mantém os valores dele.

### Leitura mais recente — `GET /api/telemetry/latest/?device_id=...`

```json
{
  "vehicle": { "device_id": "AA:BB:CC:DD:EE:FF", "name": "Gol", "fuel_percent": 67.1,
               "gasoline_level": 30.2, "last_seen_at": "...", "...": "..." },
  "reading": { "sent_at": "...", "rpm": 850, "speed": 0, "coolant_temp": 90,
               "engine_load": 25.5, "throttle_position": 12.0, "ltft": -2.3,
               "fuel_percent": 67.1, "...": "..." }
}
```
`reading` é `null` se o veículo ainda não enviou nada. Para mostrar "sem dados
recentes" (FE-02), compare `vehicle.last_seen_at` com a hora atual.

### Histórico — `GET /api/telemetry/history/?device_id=...&limit=50`

Últimas N leituras (padrão 50, máximo 500), **da mais antiga para a mais nova**:
`{ "device_id": "...", "count": 50, "results": [ ...leituras... ] }`

### Dados do combustível — `GET /api/fuel/status/?device_id=...`

```json
{ "fuel_consumption_factor": 0.008, "liters_spent_system": 10.0,
  "gasoline_level": 20.0, "tank_capacity": 45.0, "fuel_percent": 44.4,
  "pending_sync": false, "last_refuels": [ ... ] }
```

### Recálculo do fator — `POST /api/fuel/recalculate/`

```json
{ "device_id": "AA:BB:CC:DD:EE:FF", "litrosInseridos": 12 }
```

`Novo Fator = Fator Antigo × (Litros Inseridos / Litros Gastos no Sistema)`.
Depois disso o contador de litros gastos volta a zero e os litros inseridos são
somados ao nível do tanque (limitado à capacidade).

```json
{ "status": "ok", "old_factor": 0.008, "new_factor": 0.0096,
  "liters_inserted": 12, "liters_spent_system": 10.0,
  "gasoline_level": 32.0, "fuel_percent": 71.1, "refuel_id": 1 }
```
Erros: `400 no_consumption_recorded` (nenhum consumo registrado ainda),
`400 liters_above_capacity`, `404 device_not_registered`.

## Deploy na AWS

1. Preencha as variáveis do `.env.example` no ambiente da AWS, com
   `DJANGO_DEBUG=False`, uma `DJANGO_SECRET_KEY` nova, o domínio da API em
   `DJANGO_ALLOWED_HOSTS` e o domínio da Vercel em `CORS_ALLOWED_ORIGINS`.
2. `pip install -r requirements.txt`
3. `python manage.py migrate` e `python manage.py collectstatic --noinput`
4. Iniciar: `gunicorn config.wsgi:application --bind 0.0.0.0:8000`
