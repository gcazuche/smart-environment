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

## Migração do ambiente — 2026-08-14

O ambiente ativo passou a ser o Conda isolado `smart-environment`, em
`C:\Users\angel\anaconda3\envs\smart-environment`. Nenhum comando de instalação foi
direcionado ao `base`; sua inspeção mostrou pacotes gerais preexistentes, mas não o
projeto nem OpenCV. `environment.yml` instala Python 3.12, o projeto editável e versões
fixadas de build, mypy, pytest, pytest-cov e Ruff; OpenCV/NumPy permanecem fixados no
projeto.

Os comandos anteriores com `.venv` permanecem acima somente como evidência histórica
da execução original. Toda nova validação usa `conda run -n smart-environment`.

No Conda passaram Ruff, format-check (21 arquivos), mypy (21 arquivos), pytest e
unittest (44 testes), compileall, doctor, build sem isolamento, `pip check` e
`git diff --check`. O smoke Conda de 30 frames abriu via DirectShow, atingiu contagem
máxima de uma pessoa e manteve `data/` em 5 → 5 arquivos.

## Incremento de corpo parcial — 2026-08-14

- `HybridPersonDetector` combina HOG de corpo inteiro e cascade de parte superior;
- a entrada do cascade é cinza/equalizada e o tamanho mínimo é 24 × 24 pixels;
- caixas sobrepostas são deduplicadas e a origem é visível apenas na anotação local;
- nenhum pacote, peso externo, writer, cliente de rede ou persistência foi adicionado.

No Conda, pytest e unittest passaram com 48 testes; Ruff, format-check e mypy strict
passaram em 21 arquivos. Também passaram `compileall`, `doctor`, build sem isolamento,
`pip check` e `git diff --check`.
O smoke limitado processou 30 frames via DirectShow, encerrou por `frame_limit`, terminou
com uma pessoa e observou máximo de duas. `data/` permaneceu em 5 → 5 arquivos. O teste
confirma presença e lifecycle, não precisão: o pico pode representar detecção duplicada
ou falso positivo e permanece como risco a medir.

## Incremento NanoDet/Hugging Face — 2026-08-14

- peso FP32 oficial baixado da revisão fixa e validado pelo SHA-256 publicado;
- licença Apache-2.0 baixada e validada separadamente;
- `NanoDetPersonDetector` preserva proporção com letterbox, filtra somente `person`,
  aplica NMS e converte caixas para as coordenadas originais;
- peso alterado/ausente e saída inesperada falham de modo explícito e sanitizado;
- frame sintético preto produziu zero pessoas e inferência inicial de aproximadamente
  108 ms na CPU local.

No smoke da webcam, limiar 0,35 processou 30 frames via DirectShow, terminou em zero e
observou máximo de uma pessoa. Em comparações de 30 frames, 0,30 terminou/máximo em duas
e 0,25 terminou em duas/máximo em quatro; esses limiares foram rejeitados por risco de
falso positivo. A medição não usou ground truth e não prova acurácia. `data/` permaneceu
em 5 → 5 no smoke oficial; nenhum frame foi salvo ou enviado.

Após a integração, passaram no Conda: pytest e unittest (54 testes), Ruff, format-check,
mypy strict (23 arquivos), compileall, doctor, build sem isolamento e `pip check`. O
script PowerShell foi analisado pelo parser nativo sem erro; hashes locais do peso e da
licença coincidiram com os valores fixados; `git diff --check` passou.
