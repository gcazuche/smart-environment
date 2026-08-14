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

    camera = subparsers.add_parser("camera", help="detectar pessoas com a webcam local")
    camera.add_argument("--index", type=_non_negative_int, default=0)
    camera.add_argument("--backend", choices=("auto", "dshow", "msmf", "any"), default="auto")
    camera.add_argument("--no-display", action="store_true")
    camera.add_argument("--max-frames", type=_positive_int)

    subparsers.add_parser("version", help="mostrar versão da aplicação")
    return parser


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("deve ser zero ou maior")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("deve ser maior que zero")
    return parsed


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


def _run_camera_command(args: argparse.Namespace) -> int:
    """Import the optional runtime path only when the operator requests it."""

    from app.cameras import CameraError, OpenCVCamera
    from app.live_detection import NullDisplay, OpenCVDisplay, run_person_detection
    from app.vision import HybridPersonDetector

    if args.no_display and args.max_frames is None:
        print("erro: --no-display exige --max-frames", file=sys.stderr)
        return 2

    camera = OpenCVCamera(index=args.index, backend=args.backend)
    display = NullDisplay() if args.no_display else OpenCVDisplay()
    try:
        summary = run_person_detection(
            camera,
            HybridPersonDetector(),
            display,
            max_frames=args.max_frames,
        )
    except CameraError as exc:
        print(f"erro de câmera: {exc}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("operação cancelada", file=sys.stderr)
        return 130
    except Exception:
        print("erro interno durante a detecção local", file=sys.stderr)
        return 1

    print(
        "detecção encerrada: "
        f"frames={summary.frames_processed}, "
        f"pessoas_agora={summary.last_count}, "
        f"máximo={summary.max_count}, "
        f"backend={summary.backend_name}, "
        f"motivo={summary.stopped_by}"
    )
    return 0


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
    if args.command == "camera":
        return _run_camera_command(args)

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
