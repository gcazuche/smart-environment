"""Create private web settings once, without mutating Supabase or the legacy file."""

import os
import secrets

from django.core.management.base import BaseCommand, CommandError

from app.web.configuration import ROOT, read_env


class Command(BaseCommand):
    help = "Cria configuração web privada sem sobrescrever arquivo existente ou acessar a rede."

    def handle(self, *args, **options):
        directory = ROOT / "config" / "web"
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = directory / ".env.web.local"
        if target.exists():
            self.stdout.write("Configuração privada já existe; nenhum valor foi sobrescrito.")
            return
        previous = read_env(ROOT / "dashboard" / ".env.local")
        values = {
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_DEBUG": "false",
            "DJANGO_PRODUCTION": "false",
            "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,[::1]",
            "LOCAL_MONITOR_ENABLED": "false",
        }
        for key in (
            "SUPABASE_URL",
            "SUPABASE_PUBLISHABLE_KEY",
            "ORGANIZATION_ID",
            "PROCESSING_SERVER_URL",
        ):
            value = previous.get(f"VITE_{key}", "")
            if "\n" in value or "\r" in value:
                raise CommandError("Configuração de origem inválida.")
            values[key] = value
        # Exclusive create and owner-only POSIX mode; never log keys or contents.
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write("# Privado: não adicionar ao Git nem compartilhar em logs.\n")
            handle.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
        self.stdout.write("Configuração privada criada. Reinicie o comando Django para carregá-la.")
        self.stdout.write(
            "O banco remoto não foi acessado; execute migrate para as sessões locais."
        )
