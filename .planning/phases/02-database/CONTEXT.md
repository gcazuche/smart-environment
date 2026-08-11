> [!CAUTION]
> **SUPERADO em 2026-08-11. NÃO EXECUTAR.** Este contexto pertence ao produto facial
> anterior. A próxima etapa ativa é `SE-02`, definida em `.planning/ROADMAP.md`, e só
> começa após autorização explícita. Conteúdo abaixo preservado como histórico.

# Fase 2 — Contexto (histórico)

## Objetivo

Introduzir uma fronteira de persistência transacional e testável, começando localmente
com SQLite e evoluindo para o serviço central preferencial somente após prova de
conceito isolada. A fase não coleta nem armazena biometria real.

## Entradas confirmadas

- Fase 1 concluída; lock, build e gates aprovados em Python 3.11 e 3.12.
- Internet e Supabase são preferenciais para a arquitetura comercial futura.
- Operação offline continua obrigatória; SQLite é o primeiro runtime local.
- A webcam integrada é o primeiro hardware, mas captura de aplicação pertence à Fase 4.
- Frames completos são opt-in por evento; retenção/base legal permanecem abertas.

## Fronteiras desta entrada

- Nenhuma credencial, projeto ou conexão Supabase será criada implicitamente.
- Nenhum DSN arbitrário, PostgreSQL, pgvector, Storage, RLS ou sincronização entra no
  primeiro slice.
- Nenhuma tabela de pessoa, face, embedding, imagem ou evento será criada no primeiro
  slice de runtime.
- Construir configuração/engine não pode criar arquivo ou abrir rede; conexão exige
  chamada explícita.
- O `doctor` continua somente leitura.

## Decisões ainda abertas

- Cardinalidade comercial de tenant/site e isolamento RLS.
- Nomes canônicos divergentes (`people`/`detection_events` versus
  `persons`/`recognition_events`) e entidades adicionais da pesquisa.
- Região, plano, quotas, custos, residência, backup e restore do Supabase.
- Modelo facial, dimensão de vetor, licença de pesos e metadados de normalização.
- Retenção, base legal, consentimento, criptografia em repouso e política de snapshots.

Essas decisões bloqueiam esquema biométrico e encerramento da fase, mas não o runtime
SQLite mínimo sem tabelas de domínio.

## Resultado esperado da próxima tarefa

Um runtime SQLite preguiçoso, parametrizado e descartável, com foreign keys habilitadas,
transações commit/rollback testadas e caminho confinado a `MULTICAM_DATA_DIR`.
