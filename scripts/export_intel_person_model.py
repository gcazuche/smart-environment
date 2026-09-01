"""Export and verify the pinned YOLO26n model used by Intel's reference pipeline."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

MODEL_NAME = "yolo26n"
WEIGHT_SHA256 = "9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef"
EXPECTED_ARTIFACTS = {
    "yolo26n.xml": "d9120135a234b51dcfae7ee904247df7bfc7830d55955beedb1aed3c7400f2e1",
    "yolo26n.bin": "f555e06c74c0ab1d4338428bf41ca5f6674f25902f2c6a4530b5af3605485193",
    "metadata.yaml": "f4967e6adf566bff2de25ecfdeed21e77cbdf7f0bacd2d705991152689384dc3",
}


def _digest(path: Path) -> str:
    with path.open("rb") as artifact:
        return hashlib.file_digest(artifact, "sha256").hexdigest()


def _verify(path: Path, expected_sha256: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"artefato ausente: {path.name}")
    digest = _digest(path)
    if digest != expected_sha256:
        raise RuntimeError(f"hash inesperado para {path.name}: {digest}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-directory", required=True, type=Path)
    args = parser.parse_args()
    target = args.target_directory.resolve()
    target.mkdir(parents=True, exist_ok=True)
    weights = target / f"{MODEL_NAME}.pt"
    output = target / f"{MODEL_NAME}_openvino_model"

    if output.is_dir():
        _verify(weights, WEIGHT_SHA256)
        for filename, expected_hash in EXPECTED_ARTIFACTS.items():
            _verify(output / filename, expected_hash)
        print(f"Modelo Intel já verificado em {output}")
        return 0

    from ultralytics import YOLO

    previous_directory = Path.cwd()
    try:
        os.chdir(target)
        model = YOLO(weights.name)
        _verify(weights, WEIGHT_SHA256)
        exported = Path(
            model.export(format="openvino", half=True, dynamic=False, imgsz=640)
        ).resolve()
    finally:
        os.chdir(previous_directory)

    if exported != output:
        raise RuntimeError(f"diretório de exportação inesperado: {exported}")
    for filename, expected_hash in EXPECTED_ARTIFACTS.items():
        _verify(output / filename, expected_hash)
    print(f"Modelo Intel exportado e verificado em {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
