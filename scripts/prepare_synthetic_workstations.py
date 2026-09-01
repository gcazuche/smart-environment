"""Validate the project-generated synthetic workstation references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.datasets import prepare_synthetic_workstation_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validar as referências sintéticas e gerar o manifest",
    )
    parser.add_argument(
        "--input-directory",
        type=Path,
        default=Path("data/datasets/workstation-references/synthetic"),
    )
    args = parser.parse_args()
    summary = prepare_synthetic_workstation_manifest(args.input_directory)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
