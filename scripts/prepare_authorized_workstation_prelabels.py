"""Build review-required YOLO prelabels from the authorized workstation photos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.datasets.authorized_workstations import (
    AUTHORIZED_SCENE_GROUPS,
    AUTHORIZED_SOURCE_FINGERPRINT_SHA256,
    COCO_PRELABEL_CLASSES,
    DEFAULT_AUTHORIZED_SOURCE_DIRECTORY,
    DEFAULT_PRELABEL_OUTPUT_DIRECTORY,
    prepare_authorized_workstation_prelabels,
)
from app.vision.intel_yolo import IntelYoloDetector


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preparar pré-rótulos locais de pessoa, laptop, mouse e teclado; "
            "nenhum treinamento é iniciado"
        )
    )
    parser.add_argument(
        "--input-directory",
        type=Path,
        default=DEFAULT_AUTHORIZED_SOURCE_DIRECTORY,
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_PRELABEL_OUTPUT_DIRECTORY,
    )
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--device", default="CPU")
    args = parser.parse_args()

    # The detector-level threshold is the lowest class threshold.  The dataset
    # pipeline applies the stricter, documented threshold for each class later.
    detector = IntelYoloDetector(
        COCO_PRELABEL_CLASSES,
        args.model_path,
        confidence_threshold=0.25,
        device=args.device,
    )
    manifest = prepare_authorized_workstation_prelabels(
        args.input_directory,
        args.output_directory,
        detector,
        scene_groups=AUTHORIZED_SCENE_GROUPS,
        expected_source_fingerprint=AUTHORIZED_SOURCE_FINGERPRINT_SHA256,
    )
    summary = {
        "output_directory": str(args.output_directory.resolve()),
        "classes": manifest["classes"],
        "cell_phone_class_included": manifest["cell_phone_class_included"],
        "selection": manifest["selection"],
        "split_counts": manifest["split_counts"],
        "prelabel_counts": manifest["prelabel_counts"],
        "ready_for_training": manifest["ready_for_training"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
