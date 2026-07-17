# Fase 2 — Pesquisa de entrada

Atualizado em: 2026-07-17

## Evidência técnica selecionada

- A versão estável observada do SQLAlchemy é **2.0.51**; a série 2.1 está em beta e
  não será usada no primeiro slice. O pacote declara licença MIT e suporte a Python
  3.11/3.12: <https://pypi.org/project/SQLAlchemy/2.0.51/>.
- A documentação oficial informa que foreign keys do SQLite não têm efeito por padrão
  e que `PRAGMA foreign_keys=ON` deve ser emitido em todas as conexões, inclusive antes
  de criação de metadados:
  <https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support>.
- `Engine.begin()` confirma a transação ao sair normalmente e faz rollback quando há
  exceção; será o contrato transacional do spike:
  <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Engine.begin>.
- A pesquisa de Supabase/PostgreSQL/pgvector/Storage já está consolidada em
  `.planning/research/SUPABASE_ESP32_DEPLOYMENT.md`, mas nenhum projeto, credencial,
  migration, RLS, Storage ou restore real foi testado.

## Escolha provisória

Usar `SQLAlchemy==2.0.51` com o driver `sqlite3` da stdlib no primeiro slice. A versão
será fixada no lock somente quando DB-02-02 for implementada. Não instalar Alembic,
psycopg, SDK Supabase ou pgvector ainda.

## Threat model do slice local

- **Entrada não confiável:** variáveis de ambiente e valores de consulta.
- **Ativos:** integridade do arquivo local, confidencialidade de paths e futura base.
- **Ameaças:** path traversal/arquivo fora de `data`, DSN remoto injetado, SQL
  concatenado, foreign key desabilitada, transação parcial e handle aberto no Windows.
- **Controles:** backend fixo `sqlite`, nome de arquivo interno, `Path.resolve` e
  confinamento, bind parameters, event hook para PRAGMA, `Engine.begin()` e `dispose()`.
- **Fora do escopo:** criptografia de biometria, RLS, autenticação e rede; nenhum dado
  real entra neste slice.

## Gate para o adaptador remoto

Antes de implementar Supabase/PostgreSQL, executar spike separado e autorizado com
projeto não produtivo, dados sintéticos, RLS negativa entre tenants, pgvector, bucket
privado, URLs assinadas, rotação de segredo, quota/custo, backup e restore. Até lá,
Supabase permanece preferência não validada.
