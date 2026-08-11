> [!CAUTION]
> **SUPERADO em 2026-08-11. NÃO EXECUTAR DB-02-02.** O rebaseline Smart Environment
> substituiu este plano. Consulte `.planning/STATE.md` e `.planning/ROADMAP.md`.
> Conteúdo abaixo preservado como histórico, não como backlog ativo.

# Fase 2 — Plano atômico (histórico)

## Estado de execução

| Tarefa | Estado | Evidência/lacuna |
|---|---|---|
| DB-02-01 | concluída | contexto, pesquisa e fronteiras persistidos |
| DB-02-02 | próxima | runtime SQLite local, preguiçoso e transacional |
| DB-02-03 | pendente | esquema/migrações após resolver nomes e minimização |
| DB-02-04 | bloqueada | spike Supabase isolado exige projeto/credenciais e autorização |
| DB-02-05 | pendente | verificação e encerramento da fase |

## DB-02-01 — Abrir contexto e resolver fronteiras

- **Tipo:** planejamento/pesquisa
- **Prioridade:** P0
- **Risco:** médio
- **Aceite:** fatos e propostas separados; nenhum serviço declarado validado; primeiro
  slice não depende de biometria, rede ou escolha de tenant.
- **Resultado:** concluída neste checkpoint.

## DB-02-02 — Runtime SQLite local mínimo

- **Tipo:** implementação/teste
- **Prioridade:** P0
- **Risco:** médio
- **Arquivos previstos:** `pyproject.toml`, `uv.lock`, `.env.example`,
  `app/configuration/settings.py`, `app/database/__init__.py`,
  `app/database/runtime.py`, `tests/database/test_runtime.py`.
- **Dependências:** DB-02-01; `SQLAlchemy==2.0.51` verificado em fonte primária.
- **Passos:** adicionar dependência/lock; validar backend local; construir URL
  internamente; criar engine sem conexão; habilitar FK por conexão; oferecer unidade
  transacional curta; descartar engine; documentar contrato.
- **Critérios de aceite:**
  1. Construir settings/runtime não cria `multicam.db`.
  2. Backend remoto/DSN arbitrário é recusado sem DNS ou rede.
  3. Arquivo fica confinado a `MULTICAM_DATA_DIR` e paths inválidos são recusados.
  4. `repr`, resumo público e logs não mostram DSN ou path completo.
  5. `PRAGMA foreign_keys` retorna 1 em cada conexão.
  6. Sucesso confirma; exceção injetada reverte integralmente.
  7. Consulta de prova usa bind parameter, nunca concatenação.
  8. `dispose()` permite remover arquivo temporário no Windows.
  9. `doctor --json` permanece somente leitura.
  10. Gates 3.11/3.12, build, wheel limpo, compatibilidade e secret scan passam.
- **Não inclui:** modelos/tabelas de domínio, Alembic, Supabase, PostgreSQL, pgvector,
  imagens, embeddings, credenciais ou dados reais.
- **Reversão:** remover módulo/dependência e restaurar lock; nenhum banco real existe.

## DB-02-03 — Esquema mínimo e migrações

Só inicia após decidir nomenclatura canônica, tenant/site, minimização e quais tabelas
podem existir sem modelo facial. Terá plano e threat model próprios; não herda aceite
do runtime vazio.

## DB-02-04 — Spike Supabase/PostgreSQL

Bloqueado até o usuário fornecer/autorizar um projeto de teste e as decisões mínimas
de região/plano. Usará apenas dados sintéticos e não instalará chave elevada em câmera
ou cliente não confiável.

## Status esperado após DB-02-02

DB-001 e SEC-003 ficam `em andamento`; DB-002, DB-003, DB-004 e PRIV-002 continuam
pendentes. A Fase 2 permanece aberta.
