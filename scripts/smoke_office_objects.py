"""Run the office-object detector only on the reviewed public references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.vision import IntelOfficeObjectDetector
from app.vision.office_object_smoke import run_office_object_smoke


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Testar objetos de escritório nas três referências públicas",
    )
    parser.add_argument(
        "--input-directory",
        type=Path,
        default=Path("data/datasets/workstation-references/huggingface"),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("data/evaluations/office-object-smoke"),
    )
    parser.add_argument("--confidence-threshold", type=float, default=0.25)
    args = parser.parse_args()
    detector = IntelOfficeObjectDetector(confidence_threshold=args.confidence_threshold)
    report = run_office_object_smoke(
        args.input_directory,
        args.output_directory,
        detector,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
