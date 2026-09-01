"""Prepare the reviewed workstation reference images outside Git."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.datasets import prepare_workstation_references


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Baixar as referências revisadas de estações de trabalho",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("data/datasets/workstation-references/huggingface"),
    )
    parser.add_argument("--maximum-image-bytes", type=int, default=1_000_000)
    args = parser.parse_args()
    summary = prepare_workstation_references(
        args.output_directory,
        maximum_image_bytes=args.maximum_image_bytes,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
