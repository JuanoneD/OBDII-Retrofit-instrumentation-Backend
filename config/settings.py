"""
Configurações do projeto Django (BE-01).

Tudo que muda entre o seu PC e a AWS (senhas, banco, domínios) vem de
variáveis de ambiente, lidas do arquivo `.env` (veja `.env.example`).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# --- Segurança ---------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-key-troque-em-producao")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# --- Apps --------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Bibliotecas
    "rest_framework",
    "corsheaders",
    # Apps do projeto
    "telemetry",  # dispositivos, veículos e leituras da ESP32
    "fuel",  # recálculo do fator de combustível
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # precisa ficar no topo
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Banco de dados ----------------------------------------------------------
# Sem DB_HOST no .env -> usa SQLite (um arquivo local, bom para desenvolver).
# Com DB_HOST no .env -> usa o MySQL da AWS (RDS).
# Os testes automáticos sempre usam SQLite, para não mexer no banco da AWS.
RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == "test"

if os.getenv("DB_HOST") and not RUNNING_TESTS:
    import pymysql

    # O Django espera o driver "mysqlclient"; o PyMySQL se passa por ele
    # e é mais fácil de instalar no Windows e na AWS.
    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()

    db_options = {"charset": "utf8mb4"}
    if os.getenv("DB_SSL_CA"):
        # Certificado da AWS (global-bundle.pem) para conexão criptografada.
        db_options["ssl"] = {"ca": str(BASE_DIR / os.getenv("DB_SSL_CA"))}

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "obdii"),
            "USER": os.getenv("DB_USER", "admin"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": db_options,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Validação de senha (usuários do /admin) ---------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Idioma e fuso -----------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# --- Arquivos estáticos (CSS do /admin) -------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- CORS: quem pode chamar a API pelo navegador -----------------------------
# Coloque o domínio da Vercel no .env, ex.: https://obdii-frontend.vercel.app
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
)
# Libera também os links de preview da Vercel (https://qualquer-coisa.vercel.app)
if env_bool("CORS_ALLOW_VERCEL_PREVIEWS", True):
    CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://[\w-]+\.vercel\.app$"]


# --- Django REST Framework ---------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # página de teste no navegador
    ],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}


# --- Segurança extra em produção --------------------------------------------
if not DEBUG:
    # Serve o CSS do /admin direto pelo Django (sem precisar de Nginx)
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
