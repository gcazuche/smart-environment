# Fase 1 — Verificação

Status: **Aprovado com ressalvas até FND-01-04; fase ainda aberta**.

## Implementação

Foram implementados configuração mínima validada, diagnóstico somente leitura,
entrypoints, logging JSON seguro e testes stdlib. O contexto foi refinado para uma
webcam inicial, Supabase/internet preferenciais, futura ingestão ESP32 e frames de
eventos. Planejamento, pesquisa e checkpoint estão persistidos.

## Critérios e comandos

```powershell
& '<runtime-python-3.12.13>' -m unittest discover -s tests -v
& '<runtime-python-3.12.13>' -m compileall -q app main.py tests
& '<runtime-python-3.12.13>' -m app doctor --json
& '<runtime-python-3.12.13>' -m app version
& '<runtime-python-3.12.13>' main.py doctor
```

## Evidências

- `unittest`: **26 testes, 26 aprovados**, 0 falhas, 0 erros (0,248 s).
- `compileall`: exit code 0.
- `tomllib` sobre `pyproject.toml`: `pyproject: OK`.
- `doctor --json`: exit code 0, cinco checks `pass`, `has_failures=false`.
- layout instalado simulado: não exige `tests/`/`.planning` nem aponta dados para
  `site-packages`; coberto por teste unitário.
- `version`: exit code 0, versão `0.1.0`.
- `main.py doctor`: exit code 0, cinco checks `OK`.
- `MULTICAM_MAX_CAMERAS=0`: exit code 2 esperado e erro sanitizado.
- busca passiva por chaves privadas/tokens de alta confiança: nenhum match.
- redaction: Bearer/Basic, Authorization/Cookie, credencial em URL, embeddings,
  imagens e campos pessoais comuns não aparecem na saída testada.
- contexto: somente `operation`, `camera_id`, `device_id` e `error_type`; contexto
  livre é recusado e identificador com `@` é redigido.
- exceção fatal: mensagem/traceback bruto e path absoluto não são emitidos; arquivo
  opcional preserva apenas tipos, source hash, função e linha.
- logging: correlação com escopo, IDs não reutilizados fora do escopo, rotação,
  `backup_count>=1`, proteção POSIX reaplicada e fallback de destino aprovados.
- bootstrap do logger e exceção inesperada retornam código controlado sem traceback.
- primeira tentativa de invocar o Python falhou no parser PowerShell e não executou
  teste algum; causa/correção registradas em `debugging/2026-07-17-powershell-python-invocation.md`.

## Gaps

- `pytest`, Ruff e mypy: consultas `python -m <ferramenta> --version` retornaram
  `No module named ...`; gates não executados e nenhum download foi feito.
- Python 3.11, build/instalação em venv limpo e lockfile: não validados.
- `git diff --check` retornou 0 para arquivos rastreados; arquivos novos também foram
  cobertos por `compileall`, testes e verificação explícita de linhas Python >100.
- nenhuma dependência, câmera, modelo, GPU, banco, rede ou GUI foi exercitada.
- ACL explícita do arquivo de log no Windows e o diretório persistente real não foram
  validados; o entrypoint usa somente stderr estruturado nesta fase.

## Testes manuais

CLI humana foi executada. Testes de câmera/hardware não são aplicáveis à etapa e não
serão declarados como validados.

## Resultado final

**Aprovado com ressalvas** para FND-01-01..04. FND-01-05 e a Fase 1 permanecem
abertos até os gates de ambiente/lock serem executados. SEC-007 continua `em
andamento` nas camadas futuras e não autoriza log persistente de produção no Windows.
