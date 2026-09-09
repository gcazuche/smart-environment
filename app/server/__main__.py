"""Run with conda run -n smart-environment python -m app.server."""

from __future__ import annotations

import argparse
import json
import signal
from pathlib import Path

from app.server.config import Settings, load_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smart Environment: processamento CPU na VM")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--env-file", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Valida o formato da configuração")
    modes.add_argument(
        "--preflight", action="store_true", help="Diagnóstico da instalação, sem rede"
    )
    parser.add_argument("--json", action="store_true", help="Saída estruturada de --preflight")
    args = parser.parse_args(argv)
    if args.json and not args.preflight:
        parser.error("--json requer --preflight")
    if args.env_file and not args.config:
        parser.error("--env-file requer --config")
    if args.preflight:
        from app.server.preflight import render_report, run_preflight

        report = run_preflight(args.config, args.env_file)
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False))
        else:
            render_report(report)
        return 1 if report.has_failures else 0
    if not args.config:
        parser.error("--config é obrigatório para iniciar ou validar a configuração")
    try:
        if args.env_file:
            load_env(args.env_file)
        settings = Settings.read(args.config)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        print("Configuração inválida. Confira o TOML, os UUIDs e as variáveis; segredos omitidos.")
        return 2
    if args.check:
        print(f"Configuração válida: {len(settings.streams)} câmeras; nenhuma conexão iniciada.")
        return 0
    from app.server.runtime import Runtime

    try:
        runtime = Runtime(settings)
        signal.signal(signal.SIGINT, lambda *_: runtime.stop.set())
        signal.signal(signal.SIGTERM, lambda *_: runtime.stop.set())
        runtime.run()
    except Exception:
        print("Servidor encerrado por falha. Confira modelo, dependências, disco e configuração.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
