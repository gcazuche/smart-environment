# Debug — smoke da webcam integrada

- **Data:** 2026-07-17
- **Escopo:** spike autorizado de hardware; um frame em memória; sem persistência
- **Dispositivo observado:** `USB2.0 HD UVC WebCam`
- **Runtime efêmero:** Python 3.12.13, `opencv-python-headless==4.13.0.92`

## Primeira tentativa

O wrapper PowerShell entregou o código do processo pai diretamente a `python -c`.
Aspas internas foram removidas na conversão para argumentos nativos e o pai terminou
com `NameError: camera_id is not defined`. O worker de OpenCV não foi iniciado; os
arquivos em `data/` permaneceram 5 antes e 5 depois.

## Correção mínima

O código do pai e do worker passou a ser transportado em Base64. Um bootstrap sem
literais sensíveis decodificou o pai, que iniciou o worker com timeout rígido de oito
segundos. Nenhum arquivo temporário de imagem ou script foi criado.

## Resultado sanitizado

```json
{
  "camera_id": "camera-local-1",
  "opened": true,
  "frame_valid": true,
  "backend": "DSHOW",
  "width": 640,
  "height": 480,
  "channels": 3,
  "dtype": "uint8",
  "elapsed_ms": 2247,
  "release_attempted": true,
  "persisted": false,
  "attempts": [
    {"backend": "MSMF", "opened": false},
    {"backend": "DSHOW", "opened": true}
  ]
}
```

Arquivos em `data/`: 5 antes, 5 depois, 0 novos. O array de frame recebido foi
sobrescrito com zeros best-effort antes da liberação; isso não constitui garantia de
apagamento de todas as cópias internas do driver. Não houve preview, hash, inferência,
reconhecimento, log de pixels ou upload. A evidência não conclui CAM-007 e não autoriza
captura contínua.
