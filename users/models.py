"""
Tabelas (modelos) do app de usuários.

Tabela User: ID_USER, name, password, email, isAdm.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Funções para criar usuários (a senha é sempre salva criptografada)."""

    def create_user(self, email, name, password):
        user = self.model(email=self.normalize_email(email), name=name)
        user.set_password(password)  # guarda a senha criptografada, nunca o texto
        user.save()
        return user

    def create_superuser(self, email, name, password):
        """Usado pelo comando `createsuperuser` para criar o ADM."""
        user = self.create_user(email, name, password)
        user.isAdm = True
        user.save()
        return user


class User(AbstractBaseUser):
    """
    Usuário do sistema.

    O AbstractBaseUser é a base do Django para usuários: já traz o campo
    password e as funções para conferir a senha.
    """

    id = models.BigAutoField(primary_key=True, db_column="ID_USER")
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)  # cada e-mail só pode ter uma conta
    isAdm = models.BooleanField(default=False)  # True = administrador

    # O AbstractBaseUser cria uma coluna "last_login" que o projeto não usa.
    last_login = None

    objects = UserManager()

    USERNAME_FIELD = "email"  # o login é feito com o e-mail
    REQUIRED_FIELDS = ["name"]  # pedido pelo createsuperuser além do e-mail e da senha

    class Meta:
        db_table = "User"
        verbose_name = "usuário"  # nome usado nas mensagens de erro

    def __str__(self):
        return self.email
