# SE-02 — Evidência do primeiro incremento

Data: 2026-08-14

## Resultado

- captura, lifecycle, loop, caixas e contagem foram implementados;
- frames permanecem no processo e o código não contém writer de imagem/vídeo nem
  cliente de rede no caminho inspecionado;
- detector HOG é baseline substituível, não um modelo declarado pronto para produção;
- a etapa permanece aberta para avaliação de corpo parcial.

## Testes automatizados

```powershell
.\.venv\Scripts\pytest.exe -q
# 44 passed

.\.venv\Scripts\ruff.exe check app tests
# All checks passed!

.\.venv\Scripts\ruff.exe format --check app tests
# 21 files already formatted

.\.venv\Scripts\mypy.exe app tests
# Success
```

Também passaram `unittest` (44), `compileall`, `doctor`, `uv build --offline`,
`uv pip check` (17 pacotes compatíveis) e `git diff --check`.

Cobertura comportamental: abertura/fallback/liberação, frame inválido, detecção fake
0/1/N, recorte e remoção de caixa aninhada, limite/tecla/exceção no loop, cópia antes
da anotação e contrato da CLI.

## Webcam autorizada

Comando executado fora do isolamento para permitir acesso ao hardware:

```powershell
.\.venv\Scripts\multicam.exe camera --no-display --max-frames 30
```

Resultado: 30 frames, backend DirectShow, encerramento pelo limite, contagem atual e
máxima iguais a zero. O teste prova acesso e lifecycle, mas **não** prova qualidade de
detecção de uma pessoa sentada/parcial. A contagem de arquivos em `data/` observada nas
tentativas permaneceu 5 antes e 5 depois; não é uma alegação sobre outros caminhos.

## Ressalva e próximo gate

Antes de encerrar SE-02, comparar um detector de corpo parcial com licença compatível,
registrar um conjunto autorizado/sintético e métricas simples de acerto, falso positivo,
latência e CPU. Não iniciar classificação de atividade nessa avaliação.
