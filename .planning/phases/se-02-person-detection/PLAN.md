# SE-02 — Plano atômico

Data: 2026-08-14
Status: primeiro incremento concluído; avaliação de qualidade pendente

| ID | Tarefa | Prioridade | Risco | Estado |
|---|---|---|---|---|
| SE-02-01 | reordenar roadmap e registrar limites | P0 | médio | concluída |
| SE-02-02 | adicionar OpenCV/NumPy ao lock | P0 | médio | concluída |
| SE-02-03 | implementar câmera e fonte simulável | P0 | alto | concluída |
| SE-02-04 | implementar detector, anotação e loop local | P0 | alto | concluída |
| SE-02-05 | integrar CLI e testes de regressão | P0 | médio | concluída |
| SE-02-06 | executar smoke autorizado e gates | P0 | alto | concluída com ressalva de qualidade |
| SE-02-07 | revisar, documentar e criar checkpoint | P1 | médio | concluída |

Próximo incremento: SEB-017, avaliar um detector adequado a corpo parcial. O HOG não
detectou a pessoa na amostra real de 30 frames e não deve ser promovido a detector de
produção com base apenas nos testes simulados.

## Contrato esperado

```text
CameraSource.open()
  -> CameraSource.read() -> frame uint8 em memória
  -> PersonDetector.detect(frame) -> Detection[]
  -> annotate(frame, detections) -> cópia para janela
  -> q/Esc/limite/interrupção -> release + destroyWindow
```

## Arquivos alvo

- `pyproject.toml`, `uv.lock`;
- `app/cameras/`, `app/vision/`, `app/live_detection.py`, `app/__main__.py`;
- `tests/test_camera.py`, `tests/test_person_detection.py`, `tests/test_live_detection.py`,
  `tests/test_cli.py`;
- README e artefatos desta fase.

## Validação

- fonte fake: open/read/release, backend fallback e falhas;
- detector fake/HOG: 0/1/N, recorte de caixas e frame inválido;
- loop: saída por tecla/limite, liberação em exceção, nenhuma API de escrita;
- CLI: parâmetros, modo invisível limitado, erros sanitizados;
- webcam real: ciclo limitado, apenas contagem/latência agregada e zero arquivo novo;
- pytest, Ruff, format-check, mypy, compileall, doctor, build e pip check.

## Rollback

Reverter dependências, módulos e comando `camera`. Nenhum dado/schema/serviço remoto é
criado; o modelo HOG está dentro do OpenCV e não deixa peso separado no repositório.
