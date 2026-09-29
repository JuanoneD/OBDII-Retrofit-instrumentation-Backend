"""
Testa a conexão com o MySQL da AWS usando os dados do .env.

Uso: python manage.py testar_banco
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Testa a conexão com o banco MySQL da AWS (RDS) configurado no .env"

    def handle(self, *args, **options):
        import pymysql

        host = os.getenv("DB_HOST")
        if not host:
            self.stdout.write(self.style.WARNING(
                "DB_HOST está vazio no .env -> o projeto está usando o SQLite local."
            ))
            return

        port = int(os.getenv("DB_PORT", "3306"))
        user = os.getenv("DB_USER", "")
        db_name = os.getenv("DB_NAME", "")
        ssl_ca = os.getenv("DB_SSL_CA")

        self.stdout.write(f"Host:    {host}:{port}")
        self.stdout.write(f"Usuário: {user}")
        self.stdout.write(f"Banco:   {db_name}")

        kwargs = {
            "host": host,
            "port": port,
            "user": user,
            "password": os.getenv("DB_PASSWORD", ""),
            "connect_timeout": 10,
        }
        if ssl_ca:
            ca_path = settings.BASE_DIR / ssl_ca
            if not ca_path.exists():
                self.stdout.write(self.style.ERROR(
                    f"Certificado não encontrado: {ca_path}\n"
                    "Baixe com: curl.exe -o global-bundle.pem "
                    "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"
                ))
                return
            kwargs["ssl"] = {"ca": str(ca_path)}

        try:
            conn = pymysql.connect(**kwargs)
        except pymysql.err.OperationalError as exc:
            code = exc.args[0] if exc.args else None
            self.stdout.write(self.style.ERROR(f"Falha ao conectar: {exc}"))
            if code == 1045:
                self.stdout.write("-> Usuário ou senha errados (DB_USER / DB_PASSWORD).")
            elif code in (2003, 2013):
                self.stdout.write(
                    "-> O servidor não respondeu. Normalmente é o Security Group da AWS "
                    "bloqueando o seu IP: peça para liberarem a porta 3306 para o seu IP."
                )
            return

        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            cur.execute("SHOW DATABASES")
            databases = [row[0] for row in cur.fetchall()]
            cur.execute("SHOW STATUS LIKE 'Ssl_cipher'")
            ssl_row = cur.fetchone()
        conn.close()

        self.stdout.write(self.style.SUCCESS(f"Conectado! MySQL {version}"))
        self.stdout.write(f"Conexão criptografada (SSL): {'sim' if ssl_row and ssl_row[1] else 'não'}")
        system = {"information_schema", "mysql", "performance_schema", "sys"}
        self.stdout.write(f"Bancos disponíveis: {', '.join(d for d in databases if d not in system) or '(nenhum)'}")

        if db_name in databases:
            self.stdout.write(self.style.SUCCESS(
                f"O banco '{db_name}' existe. Próximo passo: python manage.py migrate"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"O banco '{db_name}' ainda não existe. Crie com (usuário admin):\n"
                f"  CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            ))
