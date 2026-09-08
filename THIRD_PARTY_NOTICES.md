# Avisos de terceiros

## Dashboard e persistência DB-01

- `@supabase/supabase-js` 2.115.0: MIT, conforme manifesto do pacote instalado.
  SDK de autenticação e consultas ao Supabase; versão fixada no package-lock.
- `@electric-sql/pglite` 0.5.8: Apache-2.0, conforme manifesto do pacote instalado.
  PostgreSQL em WebAssembly, usado apenas nos testes locais do banco.
- Estes avisos não substituem os arquivos LICENSE/NOTICE dos pacotes e de suas
  dependências, que devem ser preservados em distribuições aplicáveis.

## Transmissão local ST-01

- MediaMTX 1.20.1, executável obtido da release oficial (fora do Git), pacote
  Windows/Linux AMD64 conferido por SHA-256 em `scripts/streaming.py`.
  Origem e termos: https://github.com/bluenviron/mediamtx/releases/tag/v1.20.1
- imageio-ffmpeg 0.6.0: https://pypi.org/project/imageio-ffmpeg/0.6.0/
  Wrapper BSD-2-Clause; os binários FFmpeg incluídos têm seus próprios termos.
- A publicação usa FFmpeg com libx264. Os avisos/licenças do build FFmpeg/libx264
  devem ser preservados em eventual redistribuição. Este repositório não inclui
  seus executáveis. Consulte o `-L` do FFmpeg instalado e https://ffmpeg.org/legal.html.
- Cliente WHEP implementado no projeto com APIs nativas, sem copiar o reader.js
  do MediaMTX. Referências de protocolo: https://mediamtx.org/docs/read/web-browsers.

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

## Intel Person Detection / Ultralytics YOLO26n

- Repositório de referência: `Intel/person-detection` no Hugging Face.
- Revisão fixada: `b86aaa534de9e93aad967fbaf89d93aa0fb4ba94`.
- Licença declarada pelo repositório Intel: MIT.
- Modelo-base: Ultralytics YOLO26n, peso SHA-256
  `9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef`.
- Runtime: OpenVINO 2026.2.1, Apache License 2.0.
- Artefatos FP16 OpenVINO XML/BIN têm hashes verificados pelo instalador.

O modelo é usado somente na avaliação acadêmica aberta deste TCC. A Ultralytics declara
seus modelos treinados sob AGPL-3.0 por padrão; uso privado ou comercial exigiria revisão
jurídica e possivelmente licença Enterprise. O peso, amostras e artefatos exportados não
são versionados pelo Git.

## Open Office Workstation Usage Detection Dataset

- Repositório: `shangzx/Open-Office-Workstation-Usage-Detection-Dataset` no Hugging Face.
- Arquivos usados: três JPEGs listados e verificados por SHA-256 em
  `app/datasets/workstation_references.py`.
- Licença declarada pelo repositório: CC-BY-NC-SA-4.0.
- Uso neste projeto: referência qualitativa e smoke acadêmico do TCC.

As imagens e o manifest gerado não são versionados pelo Git. O conjunto é não comercial,
tem somente três cenas ocupadas e não contém rótulos de produtividade, distração, postura
ou intenção. Ele não pode sustentar treinamento, métricas representativas ou uma evolução
comercial sem substituição por dados adequadamente licenciados e validados.
