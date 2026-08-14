# Avisos de terceiros

## OpenCV Zoo NanoDet

- Repositório: `opencv/object_detection_nanodet` no Hugging Face.
- Revisão fixada: `5bfd47077350a726ad440dd7bd1e1e35e8ebcfb2`.
- Arquivo: `object_detection_nanodet_2022nov.onnx`.
- SHA-256: `4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186`.
- Licença declarada pelo mantenedor: Apache License 2.0.
- Modelo: NanoDet-m-plus-1.5x, entrada 416 × 416, avaliado no COCO 2017 val.

O peso não é versionado pelo Git deste projeto. `scripts/download_nanodet.ps1` baixa o
modelo e a licença da revisão acima, verifica ambos por SHA-256 e grava em
`models/nanodet/`. Distribuições comerciais devem preservar a licença e este aviso e
reavaliar separadamente direitos, limitações do dataset de treino e adequação ao uso.
