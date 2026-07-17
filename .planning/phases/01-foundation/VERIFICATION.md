# Fase 1 — Verificação

Status: **Aprovado com ressalvas para a primeira etapa; fase ainda aberta**.

## Implementação

Foram implementados configuração mínima validada, diagnóstico somente leitura,
entrypoints e testes stdlib. Planejamento, pesquisas e checkpoint estão persistidos.

## Critérios e comandos

```powershell
& '<runtime-python-3.12.13>' -m unittest discover -s tests -v
& '<runtime-python-3.12.13>' -m compileall -q app main.py tests
& '<runtime-python-3.12.13>' -m app doctor --json
& '<runtime-python-3.12.13>' -m app version
& '<runtime-python-3.12.13>' main.py doctor
```

## Evidências

- `unittest`: **13 testes, 13 aprovados**, 0 falhas, 0 erros (0,167 s).
- `compileall`: exit code 0.
- `tomllib` sobre `pyproject.toml`: `pyproject: OK`.
- `doctor --json`: exit code 0, cinco checks `pass`, `has_failures=false`.
- layout instalado simulado: não exige `tests/`/`.planning` nem aponta dados para
  `site-packages`; coberto por teste unitário.
- `version`: exit code 0, versão `0.1.0`.
- `main.py doctor`: exit code 0, cinco checks `OK`.
- `MULTICAM_MAX_CAMERAS=0`: exit code 2 esperado e erro sanitizado.
- busca passiva por chaves privadas/tokens de alta confiança: nenhum match.
- primeira tentativa de invocar o Python falhou no parser PowerShell e não executou
  teste algum; causa/correção registradas em `debugging/2026-07-17-powershell-python-invocation.md`.

## Gaps

- `pytest`, Ruff e mypy: não instalados, portanto **não executados**.
- Python 3.11, build/instalação em venv limpo e lockfile: não validados.
- `git diff --check` retornou 0, mas arquivos eram untracked; não é contado como
  cobertura suficiente do conteúdo novo.
- nenhuma dependência, câmera, modelo, GPU, banco, rede ou GUI foi exercitada.

## Testes manuais

CLI humana foi executada. Testes de câmera/hardware não são aplicáveis à etapa e não
serão declarados como validados.

## Resultado final

**Aprovado com ressalvas** para FND-01-01..03. FND-01-04, FND-01-05 e a Fase 1
permanecem pendentes até os controles/gates serem implementados e executados.
