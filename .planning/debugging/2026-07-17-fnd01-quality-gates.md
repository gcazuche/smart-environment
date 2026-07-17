# Debug — gates completos da Fase 1

- **Data:** 2026-07-17
- **Ambiente:** Windows x64, Python 3.12.13, uv 0.11.17
- **Objetivo:** fechar FND-01-05 com ambiente bloqueado e gates reais

## Falhas observadas

- `pytest -q`: 3 falhas de isolamento na CLI após a primeira configuração do logger.
- `ruff check .`: duas importações fora da ordem e S105 falso positivo em `PASS = "pass"`.
- `ruff format --check .`: cinco arquivos fora da formatação canônica.
- `mypy app main.py tests`: retorno de `_open` mais amplo que o contrato de `FileHandler`.
- `uv build`: aprovado; wheel e sdist foram gerados em `dist/` ignorado pelo Git.

## Hipóteses e evidência inicial

- Cada teste de CLI passa isoladamente; a falha ocorre ao executar dois ou mais em
  sequência sob o capturador de logging do pytest.
- O logger reservado recusa handlers externos. O desenho deve destacá-los sem fechar
  recursos alheios, preservando a garantia de que traceback bruto não será encaminhado.
- `CheckStatus.PASS` é estado de diagnóstico, não senha; a supressão deve ser local e
  justificada.
- A assinatura de `_open` deve acompanhar `io.TextIOWrapper` do handler-base.

## Correção e regressão

- Handlers externos passaram a ser destacados do logger reservado sem serem fechados;
  a regressão sequencial do pytest desapareceu e exceções brutas continuam sem
  propagação. Uma revisão posterior restringiu `logger_name` a `multicam`/`multicam.*`
  e confirmou que handlers de um logger do host permanecem intactos.
- `_open` agora declara `TextIOWrapper`; S105 foi suprimido apenas no enum de status;
  imports e formatação foram normalizados.
- O pytest não usa `cacheprovider`, evitando ACL incompatível entre sandbox e usuário
  no Windows.
- Build requirements foram fixados em `setuptools==83.0.0` e `wheel==0.47.0`; `uv`
  requerido em `==0.11.17`; lock e sync offline aprovados.
- Logging em arquivo no Windows passou a falhar fechado sem criar caminho até existir
  uma implementação DACL validada.
- Resultado final: 28/28 em Python 3.11 e 3.12, Ruff, format-check, mypy strict,
  unittest, compileall, build, instalação limpa do wheel e compatibilidade aprovados.

Uma chamada de `uv pip check` sem `--cache-dir .uv-cache` falhou porque o caminho de
cache global do Windows colidia com uma entrada existente. O comando corrigido, com o
cache isolado do workspace, aprovou os 15 pacotes instalados.

A primeira auditoria automatizada de links internos usou crase literal dentro de
`python -c`; o PowerShell a interpretou e o regex ficou inválido. A versão corrigida
usou `chr(96)`, encontrou apenas os globs documentais intencionais `.planning/*.md` e
`.planning/research/*.md`, e confirmou os caminhos concretos do checkpoint.

Uma busca final de termos obsoletos repetiu a armadilha ao incluir crase Markdown no
argumento PowerShell e não chegou a avaliar os arquivos. A regressão válida separou os
exit codes do `rg`, do `git diff --check` e da busca de termos: zero padrões de segredo,
zero termos obsoletos e diff check aprovado.
