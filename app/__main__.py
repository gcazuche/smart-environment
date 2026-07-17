"""Command-line interface for foundation diagnostics."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence

from app import __version__
from app.configuration import ConfigurationError, Settings
from app.diagnostics import CheckStatus, DiagnosticReport, collect_diagnostics
from app.observability import (
    SecureLogContext,
    configure_secure_logging,
    correlation_scope,
    log_event,
    sanitize_for_log,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multicam",
        description="Ferramentas locais do Multicam Inteligente",
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="diagnóstico somente leitura")
    doctor.add_argument("--json", action="store_true", dest="as_json")

    subparsers.add_parser("version", help="mostrar versão da aplicação")
    return parser


def _print_human_report(report: DiagnosticReport) -> None:
    # Kept private because the structured JSON contract is the automation surface.
    print(f"Multicam Inteligente {report.version}")
    for check in report.checks:
        marker = {
            CheckStatus.PASS: "OK",
            CheckStatus.WARN: "AVISO",
            CheckStatus.FAIL: "FALHA",
        }[check.status]
        print(f"[{marker}] {check.name}: {check.detail}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command is None:
        parser.print_help()
        return 0

    try:
        logger = configure_secure_logging()
    except KeyboardInterrupt:
        print("operação cancelada", file=sys.stderr)
        return 130
    except Exception:
        print("erro interno ao iniciar observabilidade", file=sys.stderr)
        return 1
    with correlation_scope() as correlation_id:
        try:
            settings = Settings.from_env()
            logger.setLevel(settings.log_level)
            report = collect_diagnostics(settings)
            if args.as_json:
                print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_human_report(report)
            return 1 if report.has_failures else 0
        except ConfigurationError as exc:
            log_event(
                logger,
                logging.WARNING,
                "configuration_rejected",
                context=SecureLogContext(
                    operation="load-settings",
                    error_type=type(exc).__name__,
                ),
            )
            public_detail = sanitize_for_log(str(exc))
            print(f"erro de configuração: {public_detail}", file=sys.stderr)
            return 2
        except KeyboardInterrupt:
            log_event(
                logger,
                logging.INFO,
                "shutdown_requested",
                context=SecureLogContext(operation="doctor"),
            )
            print("operação cancelada", file=sys.stderr)
            return 130
        except Exception as exc:
            log_event(
                logger,
                logging.ERROR,
                "fatal_error",
                context=SecureLogContext(
                    operation="doctor",
                    error_type=type(exc).__name__,
                ),
                exc_info=True,
            )
            print(
                f"erro interno; referência: {correlation_id}",
                file=sys.stderr,
            )
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
