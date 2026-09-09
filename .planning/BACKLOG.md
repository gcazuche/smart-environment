# Backlog priorizado — Smart Environment

Atualizado em: 2026-09-08

Os itens de implementação abaixo foram reconciliados com DB-01/SRV-01 no STATE.md.
Implementação e testes locais não equivalem a aceite de Supabase/VM/câmeras reais.

## Política

- Executar somente a etapa autorizada e uma tarefa por vez.
- `P0` bloqueia a vertical; `P1` completa o MVP; `P2` amplia valor; `P3` expande escala.
- Item concluído exige evidência; item planejado não conta como funcionalidade existente.
- Dados reais e ações externas dependem dos gates de autorização e privacidade.

## P0 — Rebaseline e próxima fundação

Prioridade antes de qualquer exposição: resolver o risco residual image-size/vinext.
Em 08/09, sharp foi atualizado para 0.35.4 com override pontual e testes; o audit caiu
de 6 para 2 entradas altas. Reavaliar o override quando o pai incorporar a correção.
Detalhes em `docs/dependency-hardening.md`; testes locais
não constituem aceite de segurança para implantação pública.

| ID | Tarefa | Etapa | Requisitos | Estado |
|---|---|---|---|---|
| SEB-001 | Inventariar base preservada e plano superado | SE-01 | GOV-001 | concluída |
| SEB-002 | Redefinir visão, MVP e limites de uso | SE-01 | GOV-001, PRIV-001 | concluída |
| SEB-003 | Redesenhar arquitetura e stack | SE-01 | GOV-001, CAM-003 | concluída |
| SEB-004 | Documentar requisitos, riscos e roadmap | SE-01 | documentação de GOV-001 a GOV-004 | concluída |
| SEB-005 | Marcar antiga Fase 2 como superada e validar consistência | SE-01 | TEST-001 | concluída |
| SEB-006 | Confirmar matriz de finalidades, responsáveis e mudança de uso | SE-03 | GOV-002 a GOV-004 | pendente |
| SEB-007 | Definir contrato mínimo e granularidade | SE-03 | DATA-001, PRIV-003 | implementado: agregados por minuto occupied/empty/unknown; retenção ainda pendente |
| SEB-008 | Criar migrações e testes de integridade com dados sintéticos | SE-03 | DATA-002 | concluída localmente em DB-01; migração existente confirmada no banco |
| SEB-009 | Provar Supabase Auth/RLS e fronteira de segredos | SE-03 | DATA-003, AUTH-001 a AUTH-003, SEC-001, SEC-002 | testes offline aprovados; organização/vínculo existentes; login/JWT/ingestão reais ainda exigem aceite |
| SEB-010 | Definir retenção, exclusão, backup e rollback iniciais | SE-03 | DATA-004, OPS-002 | pendente |

## P1 — Vertical de uma webcam

| ID | Tarefa | Etapa | Requisitos | Estado |
|---|---|---|---|---|
| SEB-011 | Implementar contrato e fonte simulada | SE-02 | CAM-001, TEST-002 | concluída |
| SEB-012 | Integrar OpenCV e lifecycle da webcam em cenário controlado | SE-02 | CAM-002, CAM-004, PRIV-004 | concluída |
| SEB-013 | Implementar buffer transitório e descarte de frames | SE-02 | CAM-003, OPS-001, PRIV-002 | concluída no loop de um frame por vez |
| SEB-014 | Selecionar detector CPU-first e registrar licença | SE-02 | OCC-001 | concluída — NanoDet OpenCV/HF, Apache-2.0, revisão/hash fixados |
| SEB-015 | Implementar detecção 0/1/N, caixas e contagem | SE-02 | OCC-001, OCC-003 | concluída com NanoDet em testes; smoke real detectou presença |
| SEB-016 | Implementar estados observáveis e tracking efêmero | SE-04 | ACT-001 a ACT-003, OCC-002, OCC-004 | em andamento — Etapa 3D preparou 33 imagens autorizadas de pessoa/laptop/mouse/teclado, sem celular; pré-rótulos e privacidade ainda exigem revisão humana antes de treino, pose, tracking ou classificação |
| SEB-017 | Avaliar qualidade e zero persistência de pixels | SE-02/SE-04 | TEST-003, PRIV-002 | em andamento — webcam e Android integrados; três imagens qualitativas não substituem dataset representativo |
| SEB-018 | Implementar ingestão autenticada | SE-05 | API-001, SEC-003 | implementada/testada em SRV-01; implantação e ingestão real pendentes |
| SEB-019 | Implementar outbox, retry e idempotência | SE-05 | API-002, API-003 | implementada/testada: SQLite persistente, retry, deduplicação, erros preservados |
| SEB-020 | Instrumentar logs e métricas minimizados | SE-05 | API-004, SEC-004 | parcial: health autenticado, contagens/FPS/latência, preflight offline; observabilidade operacional pendente |
| SEB-021 | Construir shell web e autenticação | SE-06 | WEB-001, AUTH-001 | implementada/testada com Supabase; primeiro aceite real de login pendente |
| SEB-022 | Entregar histórico, gráficos e filtros | SE-06 | WEB-002 | consultas, filtros e CSV implementados/testados; depende da ingestão real para dados operacionais |
| SEB-023 | Validar responsividade, acessibilidade e ausência de vídeo | SE-06 | WEB-003, WEB-004 | código/lint aprovados; QA visual pendente |
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
| SEB-033 | Implementar supervisor multicâmera | SE-11 | DEV-002, DEV-004 | SRV-01 implementado/testado para até 4 câmeras; medida real 720p/30 FPS pendente |
| SEB-034 | Provar gateway ESP32/IP autenticado | SE-11 | DEV-003 | pendente |
| SEB-035 | Validar modo sugestão, override e fail-safe | SE-12 | OPS-003 | pendente |
| SEB-036 | Consolidar CI, SAST, SCA, segredos e SBOM | SE-12 | SEC-005 | pendente |
| SEB-037 | Testar restore, rollback e runbooks | SE-12 | OPS-002, OPS-004 | guias de instalação/versões preparados; restore de dados e rollback operacional pendentes |
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

Fechar o marco de código `v0.1.0` após revisão/testes e ação explícita do usuário no Git.
Depois executar preflight na VM, configurar fontes e validar primeiro transporte sintético,
depois uma câmera e a ingestão real. Ver `docs/server-processing.md` e `docs/versioning.md`.

A Etapa 3D de `SEB-016` permanece pausada: revisar imagens/pré-rótulos antes de treinar.
`cell_phone` continua fora até coleta futura; esta preparação de versão não autoriza
treinamento, pose, tracking, classificação de atividade ou alteração das fotos.
