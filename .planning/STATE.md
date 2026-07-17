# Estado GSD

Atualizado em: 2026-07-17

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch:** `main`
- **Commit executável da Fase 1:** `909d3ac` (correções-base em `b642e45`)
- **Checkpoint de planejamento:** o commit que contém este arquivo

## Posição atual

- **Fase atual:** 2 — Configurações e banco
- **Plano atual:** `.planning/phases/02-database/PLAN.md`
- **Tarefa atual:** DB-02-02 — runtime SQLite local mínimo
- **Última tarefa concluída:** DB-02-01 — contexto, pesquisa e fronteiras da Fase 2
- **Próxima ação:** implementar engine preguiçosa/transacional sem tabelas biométricas
- **Progresso global:** fundação reproduzível concluída; nenhuma função biométrica entregue

## O que funciona

- Ambiente `uv==0.11.17`, `uv.lock`, sync offline e build backend fixado.
- Configuração validada, uma câmera como limite padrão e `doctor` somente leitura.
- Logging JSON com allowlist, correlação, redaction, fronteira fatal e fail-closed de
  arquivo no Windows.
- **28/28 testes** em Python 3.11.15 e 3.12.13; Ruff, format-check, mypy strict,
  unittest, compileall, build, wheel limpo e compatibilidade aprovados.
- Webcam integrada `USB2.0 HD UVC WebCam` abriu por DirectShow em spike autorizado:
  um frame 640×480 somente em memória, dispositivo liberado e zero imagem/arquivo novo
  em `data/`.
- Pesquisa oficial para Supabase/pgvector/Storage, ESP32 e entrada SQLAlchemy persistida.

## O que ainda não existe

- Runtime SQLite, esquema, migrações, repositories ou conexão Supabase/PostgreSQL.
- Captura contínua, fonte simulada, modelo facial, cadastro, reconhecimento, API, GUI,
  autenticação, sincronização e alertas.
- Arquivo de log de produção no Windows; DACL precisa de adaptador e teste real.
- OpenCV no lock da aplicação; o pacote foi usado somente no spike efêmero.

## Testes e evidências

- **Aprovados:** pytest/unittest 28/28 em 3.11 e 3.12; Ruff; format-check; mypy;
  compileall; doctor; build; instalação limpa do wheel; `uv pip check`; busca passiva
  local por padrões de segredos; `git diff --check`; smoke manual sanitizado da webcam.
- **Pendentes da próxima tarefa:** runtime SQLite, foreign keys por conexão,
  commit/rollback, confinamento de path, dispose no Windows e ausência de rede.

## Erros conhecidos

- `python` e `py` não estão no `PATH` do sistema; usar `.venv` ou `uv`.
- O cache global do `uv` colide com uma entrada existente neste Windows; todos os
  comandos do projeto usam `--cache-dir .uv-cache`.
- MSMF não abriu a webcam no spike atual; DirectShow funcionou. O índice 0 e o backend
  não são identidade/contrato portável e serão reavaliados na Fase 4.

## Bloqueios

- Supabase remoto requer projeto de teste, autorização, região/plano e prova de RLS,
  pgvector, Storage privado, quota, custo, backup e restore.
- Esquema biométrico requer nomes canônicos, tenant/site, modelo/dimensão, minimização,
  retenção, base legal e proteção em repouso.
- Uso biométrico comercial real permanece bloqueado por base legal/consentimento,
  licença dos pesos, metas de precisão/viés e política de dados.

## Decisões abertas

- Quantidade futura de webcams/ESP32 e pessoas; protocolos finais do ESP32.
- SO e hardware de produção, GPU, metas de FPS/latência e câmeras predominantes.
- Região/plano/custos/quotas/restore do Supabase e topologia do gateway.
- Tenant/site, nomes do esquema, retenção, base legal e política de snapshots.
- Modelo/pesos com licença compatível com eventual uso comercial.

## Arquivos importantes

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/DECISIONS.md`
- `.planning/ARCHITECTURE.md`
- `.planning/phases/02-database/CONTEXT.md`
- `.planning/phases/02-database/RESEARCH.md`
- `.planning/phases/02-database/PLAN.md`

## Comandos para continuar

```powershell
uv sync --locked --extra dev --cache-dir .uv-cache
.\.venv\Scripts\python.exe -m pytest -q
git status --short
```

## Prompt de retomada sugerido

> Leia os arquivos GSD obrigatórios e continue por DB-02-02. Implemente somente o
> runtime SQLite local, preguiçoso e transacional definido no plano. Não crie tabelas
> biométricas, não aceite DSN arbitrária e não conecte Supabase sem o spike autorizado.
