"""Command-line interface for foundation diagnostics."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from app import __version__
from app.configuration import ConfigurationError, Settings
from app.diagnostics import CheckStatus, DiagnosticReport, collect_diagnostics


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
        report = collect_diagnostics(Settings.from_env())
    except ConfigurationError as exc:
        parser.exit(2, f"erro de configuração: {exc}\n")

    if args.as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human_report(report)
    return 1 if report.has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
