# OBDII Retrofit Instrumentation — Backend (v1.0)

API em Python/Django que recebe os dados de combustível enviados pela ESP32,
guarda no banco MySQL da AWS e os entrega para o site (Frontend em React na Vercel).

```
ESP32 ──(HTTP/JSON)──► Backend (Django, AWS) ──► MySQL (AWS RDS)
                              ▲
Site (React, Vercel) ─────────┘
```

Na versão 1.0, a ESP32 envia os dados apenas com o carro desligado. Por isso o
backend trabalha só com os dados persistentes de combustível, além das contas
de usuário.

## Estrutura do projeto

| Pasta      | O que tem                                                         |
|------------|-------------------------------------------------------------------|
| `config/`  | Configurações do projeto: banco de dados, CORS, rotas principais  |
| `users/`   | Contas de usuário, login e logout                                 |
| `devices/` | Dados das ESP32 e vínculo entre usuário e ESP                     |

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
| **VehicleData**      | ID_ESP (MAC), name, gasolineLevel, tankCapacity, fuelConsumptionFactor, totalDistance, tripConsumption, sync_version |

Um usuário pode ter várias ESPs, e uma ESP pode estar ligada a mais de um usuário.

## Endpoints

| Método | Rota                                       | Quem usa | O que faz                                                    | Situação     |
|--------|--------------------------------------------|----------|--------------------------------------------------------------|--------------|
| GET    | `/user`                                    | ADM      | Lista todos os usuários                                      | A implementar |
| POST   | `/user`                                    | Site     | Cria a conta e devolve o Token (login automático)            | A implementar |
| POST   | `/user/login`                              | Site     | Faz login e devolve o Token                                  | A implementar |
| POST   | `/user/logout`                             | Site     | Invalida o Token                                             | A implementar |
| POST   | `/user/addDevice`                          | Site     | Liga uma ESP à conta do usuário                              | A implementar |
| GET    | `/devices?idDevice=`                       | Site     | Lista as ESPs do usuário (o ADM vê todas)                    | A implementar |
| POST   | `/devices/<idDevice>`                      | ESP32    | Envia os dados e recebe de volta os valores do banco         | A implementar |
| POST   | `/devices/resetAndRecalculate?idDevice=`   | Site     | Recalcula o fator de consumo e volta o tanque para cheio     | A implementar |
| POST   | `/devices/resetTrip?idDevice=`             | Site     | Zera a distância e o consumo da viagem                       | A implementar |

## Como rodar no computador

Pré-requisito: Python 3.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py runserver
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver
```

O backend fica disponível em <http://127.0.0.1:8000>.

## Configuração (`.env`)

As configurações ficam no arquivo `.env`, que **não vai para o GitHub** porque
guarda senhas. O modelo está em `.env.example`.

| Variável               | O que é                                                    |
|------------------------|------------------------------------------------------------|
| `DJANGO_SECRET_KEY`    | Chave secreta do Django (no servidor, usar uma nova)       |
| `DJANGO_DEBUG`         | `True` no computador, `False` no servidor                  |
| `DJANGO_ALLOWED_HOSTS` | Endereços pelos quais o backend pode ser acessado          |
| `CORS_ALLOWED_ORIGINS` | Endereços do site autorizados a chamar o backend (Vercel)  |
| `DB_HOST`              | Endereço do MySQL da AWS. **Vazio = usa o banco local (SQLite)** |
| `DB_PORT`              | Porta do MySQL (3306)                                      |
| `DB_NAME`              | Nome do banco (`obdii`)                                    |
| `DB_USER`              | Usuário do banco                                           |
| `DB_PASSWORD`          | Senha do banco                                             |
| `DB_SSL_CA`            | Arquivo do certificado da AWS (`global-bundle.pem`)        |

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
