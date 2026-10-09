"""
Configurações do projeto Django.

Tudo o que muda entre o computador de desenvolvimento e o servidor na AWS
(senhas, endereço do banco, domínios) NÃO fica escrito aqui: vem das
variáveis de ambiente. No computador, elas ficam no arquivo `.env`
(o modelo está em `.env.example`). No servidor, são configuradas na AWS.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Pasta raiz do projeto (onde está o manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Lê o arquivo .env e coloca os valores nas variáveis de ambiente
load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    """Lê uma variável com valores separados por vírgula e devolve uma lista."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# --- Segurança ---------------------------------------------------------------

# Chave usada pelo Django para criptografia interna (ex.: gerar tokens).
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "chave-apenas-para-desenvolvimento")

# DEBUG=True mostra detalhes dos erros. No servidor deve ser False.
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

# Endereços pelos quais o backend pode ser acessado.
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")


# --- Aplicações --------------------------------------------------------------

INSTALLED_APPS = [
    # Partes do próprio Django usadas pelo sistema de usuários e tokens
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # Bibliotecas externas
    "rest_framework",  # facilita criar a API (endpoints que recebem e devolvem JSON)
    "corsheaders",  # libera o site (Frontend) a chamar o backend pelo navegador
    # Apps do projeto
    "users",  # contas de usuário, login e logout
    "devices",  # dados das ESP32 e vínculo entre usuário e ESP
]

MIDDLEWARE = [
    # O CORS precisa ser o primeiro para responder antes dos demais
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# Arquivo com a lista de rotas (endpoints) do projeto
ROOT_URLCONF = "config.urls"

# Ponto de entrada usado pelo servidor web na AWS (gunicorn)
WSGI_APPLICATION = "config.wsgi.application"


# --- Banco de dados ----------------------------------------------------------
# Se DB_HOST estiver preenchido no .env, usa o MySQL da AWS.
# Se estiver vazio, usa o SQLite: um arquivo local (db.sqlite3) para testar
# no computador sem precisar de internet.

if os.getenv("DB_HOST"):
    import pymysql

    # O Django conversa com o MySQL por meio de um "driver". Usamos o PyMySQL
    # por ser fácil de instalar no Windows e na AWS. As duas linhas abaixo
    # fazem o Django aceitá-lo no lugar do driver padrão (mysqlclient).
    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "OPTIONS": {
                "charset": "utf8mb4",
                # Modo estrito: o MySQL recusa dados inválidos em vez de
                # cortá-los ou ajustá-los sem avisar
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                # Certificado da AWS: deixa a conexão com o banco criptografada
                "ssl": {"ca": str(BASE_DIR / os.getenv("DB_SSL_CA", "global-bundle.pem"))},
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Tipo padrão dos IDs numéricos das tabelas
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Idioma e fuso horário ---------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# --- CORS --------------------------------------------------------------------
# O navegador só deixa um site chamar um backend de outro endereço se o
# backend autorizar. Aqui ficam os endereços do Frontend autorizados
# (localhost para desenvolvimento e o domínio da Vercel em produção).

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")


# --- Django REST Framework ---------------------------------------------------

REST_FRAMEWORK = {
    # A API responde sempre em JSON
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}
