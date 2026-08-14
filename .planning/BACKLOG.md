# Backlog priorizado — Smart Environment

Atualizado em: 2026-08-14

## Política

- Executar somente a etapa autorizada e uma tarefa por vez.
- `P0` bloqueia a vertical; `P1` completa o MVP; `P2` amplia valor; `P3` expande escala.
- Item concluído exige evidência; item planejado não conta como funcionalidade existente.
- Dados reais e ações externas dependem dos gates de autorização e privacidade.

## P0 — Rebaseline e próxima fundação

| ID | Tarefa | Etapa | Requisitos | Estado |
|---|---|---|---|---|
| SEB-001 | Inventariar base preservada e plano superado | SE-01 | GOV-001 | concluída |
| SEB-002 | Redefinir visão, MVP e limites de uso | SE-01 | GOV-001, PRIV-001 | concluída |
| SEB-003 | Redesenhar arquitetura e stack | SE-01 | GOV-001, CAM-003 | concluída |
| SEB-004 | Documentar requisitos, riscos e roadmap | SE-01 | documentação de GOV-001 a GOV-004 | concluída |
| SEB-005 | Marcar antiga Fase 2 como superada e validar consistência | SE-01 | TEST-001 | concluída |
| SEB-006 | Confirmar matriz de finalidades, responsáveis e mudança de uso | SE-03 | GOV-002 a GOV-004 | pendente |
| SEB-007 | Definir contrato mínimo e granularidade | SE-03 | DATA-001, PRIV-003 | pendente |
| SEB-008 | Criar migrações e testes de integridade com dados sintéticos | SE-03 | DATA-002 | pendente |
| SEB-009 | Provar Supabase Auth/RLS e fronteira de segredos | SE-03 | DATA-003, AUTH-001 a AUTH-003, SEC-001, SEC-002 | bloqueada por projeto/credenciais/autorização |
| SEB-010 | Definir retenção, exclusão, backup e rollback iniciais | SE-03 | DATA-004, OPS-002 | pendente |

## P1 — Vertical de uma webcam

| ID | Tarefa | Etapa | Requisitos | Estado |
|---|---|---|---|---|
| SEB-011 | Implementar contrato e fonte simulada | SE-02 | CAM-001, TEST-002 | concluída |
| SEB-012 | Integrar OpenCV e lifecycle da webcam em cenário controlado | SE-02 | CAM-002, CAM-004, PRIV-004 | concluída |
| SEB-013 | Implementar buffer transitório e descarte de frames | SE-02 | CAM-003, OPS-001, PRIV-002 | concluída no loop de um frame por vez |
| SEB-014 | Selecionar detector CPU-first e registrar licença | SE-02 | OCC-001 | concluída — HOG/OpenCV como baseline substituível |
| SEB-015 | Implementar detecção 0/1/N, caixas e contagem | SE-02 | OCC-001, OCC-003 | concluída em testes simulados; qualidade real pendente |
| SEB-016 | Implementar estados observáveis e tracking efêmero | SE-04 | ACT-001 a ACT-003, OCC-002, OCC-004 | pendente |
| SEB-017 | Avaliar qualidade e zero persistência de pixels | SE-02/SE-04 | TEST-003, PRIV-002 | pendente |
| SEB-018 | Implementar ingestão autenticada | SE-05 | API-001, SEC-003 | pendente |
| SEB-019 | Implementar outbox, retry e idempotência | SE-05 | API-002, API-003 | pendente |
| SEB-020 | Instrumentar logs e métricas minimizados | SE-05 | API-004, SEC-004 | pendente |
| SEB-021 | Construir shell web e autenticação | SE-06 | WEB-001, AUTH-001 | pendente |
| SEB-022 | Entregar histórico, gráficos e filtros | SE-06 | WEB-002 | pendente |
| SEB-023 | Validar responsividade, acessibilidade e ausência de vídeo | SE-06 | WEB-003, WEB-004 | pendente |
| SEB-024 | Executar vertical E2E autorizada | SE-07 | TEST-004 | pendente |
| SEB-025 | Executar piloto de uma webcam e registrar métricas | SE-07 | PRIV-004, PRIV-005, OPS-005 | bloqueada até governança/autorização |

## P2 — Sustentabilidade, patrimônio e operação

| ID | Tarefa | Etapa | Requisitos | Estado |
|---|---|---|---|---|
| SEB-026 | Implementar indicadores e fórmulas versionadas | SE-08 | SUS-001, SUS-002 | pendente |
| SEB-027 | Entregar recomendações revisáveis | SE-08 | SUS-003 | pendente |
| SEB-028 | Implementar inventário e zonas | SE-09 | AST-001 | pendente |
| SEB-029 | Implementar eventos patrimoniais autorizados | SE-09 | AST-002 | pendente |
| SEB-030 | Implementar regras, ciclo e linguagem não acusatória | SE-10 | ALT-001, ALT-002, AST-003 | pendente |
| SEB-031 | Adicionar canais opt-in e relatórios | SE-10 | ALT-003, ALT-004 | pendente |

## P3 — Expansão e release

| ID | Tarefa | Etapa | Requisitos | Estado |
|---|---|---|---|---|
| SEB-032 | Registrar/revogar agentes de borda | SE-11 | DEV-001 | pendente |
| SEB-033 | Implementar supervisor multicâmera | SE-11 | DEV-002, DEV-004 | pendente |
| SEB-034 | Provar gateway ESP32/IP autenticado | SE-11 | DEV-003 | pendente |
| SEB-035 | Validar modo sugestão, override e fail-safe | SE-12 | OPS-003 | pendente |
| SEB-036 | Consolidar CI, SAST, SCA, segredos e SBOM | SE-12 | SEC-005 | pendente |
| SEB-037 | Testar restore, rollback e runbooks | SE-12 | OPS-002, OPS-004 | pendente |
| SEB-038 | Empacotar demonstração e documentação do TCC | SE-12 | GOV-005 | pendente |

## Itens retirados do backlog ativo

- cadastro de pessoas e galeria de desconhecidos;
- reconhecimento facial, embeddings, matching, pgvector e vivacidade;
- inferência de emoção, intenção ou produtividade real;
- controle de ponto, ranking ou punição automática por classificação de atividade;
- interface PySide6;
- armazenamento de frames e transmissão pública;
- automação física no MVP.

O histórico desses itens permanece no Git. Eles não são “futuro implícito”: qualquer
retorno exige nova autorização, finalidade e gate de risco.

## Próxima tarefa recomendada

Continuar por `SEB-017`: avaliar qualidade e um detector adequado a corpo parcial,
somente no protótipo local. Não iniciar Supabase, persistência ou classificação de
atividade nesta etapa.
