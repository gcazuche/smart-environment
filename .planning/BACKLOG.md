# Backlog Priorizado

Versão: 0.1
Data: 2026-07-17
Estado: backlog inicial; nenhuma tarefa concluída.

## Política de priorização

- P0: bloqueio de segurança, privacidade, arquitetura ou caminho crítico funcional.
- P1: requisito obrigatório de alta prioridade para operação completa.
- P2: requisito obrigatório de robustez, validação, empacotamento e acabamento de release.
- P3/Futuro: evolução não necessária para o primeiro release aprovado.
- A prioridade não autoriza pular fases ou dependências do ROADMAP.md.
- Cada item deve ser refinado em um PLAN.md atômico antes da implementação. Arquivos-alvo são previsões e podem mudar somente por decisão registrada.
- Status inicial de todo item de entrega: pendente. Decisões não respondidas permanecem unspecified.

## P0 — Caminho crítico e bloqueios

### BLG-001 — Fechar contexto operacional e legal

- Fase: 1
- Tipo: descoberta/governança
- Risco: crítico
- Dependências: nenhuma
- Requisitos: PRIV-001, FACE-008, PERF-006
- Arquivos-alvo: .planning/PROJECT.md, .planning/DECISIONS.md, .planning/RISKS.md
- Resultado esperado: registrar usuários, locais, base legal, consentimento, quantidades de pessoas/câmeras, SO, hardware/GPU, rede, retenção e metas; manter respostas ausentes como unspecified e bloquear uso real quando necessário.
- Validação: revisão das respostas com responsável de produto/privacidade e checklist de lacunas.
- Impacto de segurança: impede implantação biométrica sem finalidade, autoridade ou capacidade definidas.
- Status: pendente

### BLG-002 — Pesquisar stack, modelos, licenças e arquitetura

- Fase: 1
- Tipo: pesquisa/arquitetura
- Risco: alto
- Dependências: BLG-001
- Requisitos: TEST-001, FACE-003, DB-004, PERF-001
- Arquivos-alvo: .planning/research/, .planning/STACK.md, .planning/ARCHITECTURE.md, .planning/DECISIONS.md
- Resultado esperado: comparar OpenCV, InsightFace/FaceNet/DeepFace, ONNX providers, PySide6, FastAPI, PostgreSQL/Supabase, pgvector/FAISS e opções de concorrência, com compatibilidade, manutenção, precisão, segurança e licenças.
- Validação: matriz de evidências baseada em fontes primárias, spike mínimo e ADRs; escolhas sem evidência continuam unspecified.
- Impacto de segurança: evita modelo/dependência inseguro, abandonado ou com licença incompatível.
- Status: em andamento — pesquisa documental concluída; spikes/licenças pendentes

### BLG-003 — Inicializar projeto e gates básicos

- Fase: 1
- Tipo: infraestrutura/qualidade
- Risco: alto
- Dependências: BLG-002
- Requisitos: SEC-001, SEC-007, TEST-001
- Arquivos-alvo: pyproject.toml, lockfile, .env.example, app/configuration/, app/utils/, tests/
- Resultado esperado: projeto modular, configuração tipada, logs redigidos, exceção global, ambiente reproduzível, lint, format-check, type-check, Pytest e secret scan.
- Validação: recriar ambiente limpo e executar import/build, qualidade, smoke test e scan.
- Impacto de segurança: estabelece defaults seguros e impede segredo real no repositório.
- Status: em andamento — núcleo stdlib testado; lock/lint/type-check pendentes

### BLG-004 — Modelar esquema e configurações

- Fase: 2
- Tipo: dados
- Risco: crítico
- Dependências: BLG-003
- Requisitos: DB-001, DB-002, SEC-003, PRIV-002
- Arquivos-alvo: app/database/models/, app/configuration/, tests/database/
- Resultado esperado: entidades mínimas, relações, índices, checks, exclusão lógica e configurações validadas, com classificação dos dados.
- Validação: testes de modelo/configuração e revisão de esquema contra REQUIREMENTS.md.
- Impacto de segurança: reduz estados inválidos, coleta excessiva e injection.
- Status: pendente

### BLG-005 — Implementar migrações e repositories transacionais

- Fase: 2
- Tipo: dados
- Risco: crítico
- Dependências: BLG-004
- Requisitos: DB-003
- Arquivos-alvo: alembic/, app/repositories/, tests/database/
- Resultado esperado: migração inicial reproduzível, repositories tipados e operações atômicas.
- Validação: upgrade em banco vazio, downgrade suportado, rollback de falha parcial e concorrência.
- Impacto de segurança: protege integridade e rastreabilidade dos dados biométricos.
- Status: pendente

### BLG-006 — Selecionar e provar armazenamento vetorial

- Fase: 2
- Tipo: pesquisa/spike de dados
- Risco: crítico
- Dependências: BLG-002, BLG-005
- Requisitos: DB-004
- Arquivos-alvo: .planning/research/, .planning/DECISIONS.md, app/recognition/vector_store.py, tests/recognition/
- Resultado esperado: ADR para pgvector, FAISS ou alternativa; contrato que valida dimensão/modelo e reconstrói índice.
- Validação: round-trip, busca, atualização, reconstrução, benchmark mínimo e teste de acesso.
- Impacto de segurança: controla exposição, corrupção e incompatibilidade de embeddings.
- Status: pendente

### BLG-007 — Implementar senha e sessões

- Fase: 3
- Tipo: autenticação
- Risco: crítico
- Dependências: BLG-005
- Requisitos: AUTH-001, AUTH-004
- Arquivos-alvo: app/authentication/, app/database/models/, tests/authentication/
- Resultado esperado: hash moderno, rehash, login/logout, expiração e revogação de sessão.
- Validação: testes positivos/negativos, expiração, replay, usuário inativo e inspeção de logs.
- Impacto de segurança: controla acesso inicial ao sistema e às APIs.
- Status: pendente

### BLG-008 — Implementar RBAC e escopo

- Fase: 3
- Tipo: autorização
- Risco: crítico
- Dependências: BLG-007
- Requisitos: AUTH-002, AUTH-003
- Arquivos-alvo: app/authentication/authorization.py, app/repositories/, tests/authorization/
- Resultado esperado: matriz Administrador/Operador/Visualizador e filtro por câmera/local aplicado no backend.
- Validação: matriz positiva/negativa, acesso cruzado, enumeração e exportação.
- Impacto de segurança: evita elevação de privilégio e BOLA/IDOR.
- Status: pendente

### BLG-009 — Implementar lockout, recuperação e primeiro administrador

- Fase: 3
- Tipo: autenticação/operação
- Risco: alto
- Dependências: BLG-007, BLG-008
- Requisitos: AUTH-005, AUTH-006
- Arquivos-alvo: app/authentication/, scripts/create_admin.py, tests/authentication/
- Resultado esperado: limite de tentativas, bloqueio temporário, recuperação de uso único e bootstrap que não vaza senha.
- Validação: janela/concorrência, enumeração, expiração/reuso de token e execução segura do script.
- Impacto de segurança: reduz força bruta e takeover por recuperação.
- Status: pendente

### BLG-010 — Criar abstração e adaptadores de câmera

- Fase: 4
- Tipo: funcional/câmeras
- Risco: crítico
- Dependências: BLG-003
- Requisitos: CAM-001
- Arquivos-alvo: app/cameras/base.py, app/cameras/opencv_camera.py, app/cameras/video_file.py, app/cameras/simulated.py, tests/cameras/
- Resultado esperado: contrato abrir/ler/estado/liberar para USB, integrada, IP/RTSP, arquivo e simulação.
- Validação: testes simulados e arquivo autorizado; hardware real por checklist separado.
- Impacto de segurança: isola parsing/origem e evita credencial/caminho fixo.
- Status: pendente

### BLG-011 — Implementar serviço de captura e teste de conexão

- Fase: 4
- Tipo: funcional/concorrência
- Risco: crítico
- Dependências: BLG-010, BLG-004
- Requisitos: CAM-002, CAM-003, PERF-001
- Arquivos-alvo: app/cameras/service.py, app/cameras/state.py, app/services/, tests/cameras/
- Resultado esperado: ciclo start/stop/restart, métricas, timeout, liberação e operação não bloqueante “Testar conexão”.
- Validação: ciclos repetidos, timeout, fonte ausente/fim de arquivo, cancelamento e análise de recursos.
- Impacto de segurança: limita exposição de credenciais e falhas de disponibilidade.
- Status: pendente

### BLG-012 — Entregar diagnóstico e fonte simulada

- Fase: 4
- Tipo: ferramenta/teste
- Risco: médio
- Dependências: BLG-010
- Requisitos: CAM-007, TEST-002
- Arquivos-alvo: scripts/test_camera.py, app/cameras/simulated.py, tests/cameras/
- Resultado esperado: listar/testar fontes sem revelar segredo e simular frame, lentidão, corrupção e desconexão.
- Validação: smoke do script e cenários determinísticos em CI.
- Impacto de segurança: permite testar falhas sem tocar equipamento/stream não autorizado.
- Status: pendente

### BLG-013 — Montar pipeline com filas limitadas

- Fase: 5
- Tipo: arquitetura/concorrência
- Risco: crítico
- Dependências: BLG-011
- Requisitos: CAM-005, PERF-002
- Arquivos-alvo: app/recognition/pipeline.py, app/recognition/contracts.py, app/utils/queues.py, tests/recognition/
- Resultado esperado: etapas desacopladas, canceláveis, observáveis e política de frame mais recente.
- Validação: fila cheia, produtor rápido, frame corrompido, cancelamento e memória sustentada.
- Impacto de segurança: reduz DoS por memória e contém input de vídeo defeituoso.
- Status: pendente

### BLG-014 — Implementar detecção, alinhamento e qualidade

- Fase: 5
- Tipo: visão computacional
- Risco: crítico
- Dependências: BLG-002, BLG-013
- Requisitos: FACE-001, FACE-002
- Arquivos-alvo: app/recognition/detector.py, app/recognition/alignment.py, app/recognition/quality.py, tests/recognition/
- Resultado esperado: detectar múltiplas faces, alinhar e rejeitar casos inelegíveis com motivos.
- Validação: zero/uma/várias faces, perfil, borda, tamanho, rotação, baixa qualidade e frame inválido.
- Impacto de segurança: evita alimentar embeddings com face incorreta ou mal enquadrada.
- Status: pendente

### BLG-015 — Implementar domínio e CRUD de pessoas

- Fase: 6
- Tipo: funcional/dados
- Risco: crítico
- Dependências: BLG-005, BLG-008
- Requisitos: REG-001
- Arquivos-alvo: app/models/person.py, app/repositories/people.py, app/services/people.py, tests/people/
- Resultado esperado: criar, consultar, editar, inativar e excluir conforme política, com auditoria.
- Validação: CRUD, unicidade, status, concorrência e matriz de autorização.
- Impacto de segurança: controla identidade biométrica e ações privilegiadas.
- Status: pendente

### BLG-016 — Implementar sessão guiada e portões de qualidade

- Fase: 6
- Tipo: funcional/GUI/visão
- Risco: crítico
- Dependências: BLG-014, BLG-015
- Requisitos: REG-002, REG-003, REG-004, UI-002
- Arquivos-alvo: app/services/enrollment.py, app/interface/people/, app/recognition/quality.py, tests/enrollment/
- Resultado esperado: 10–100 imagens, poses orientadas, progresso e rejeição de zero/múltiplas faces, borrão, exposição, tamanho e corte.
- Validação: limites, sequência de poses, cada rejeição, perda de câmera, cancelamento e teste Qt.
- Impacto de segurança: reduz cadastro incorreto e coleta de terceiros no frame.
- Status: pendente

### BLG-017 — Implementar revisão, duplicidade e persistência atômica

- Fase: 6
- Tipo: funcional/dados
- Risco: crítico
- Dependências: BLG-006, BLG-016
- Requisitos: REG-005, REG-006, SEC-004
- Arquivos-alvo: app/services/enrollment.py, app/recognition/duplicate.py, app/security/uploads.py, tests/enrollment/
- Resultado esperado: refazer/excluir fotos, revisar suspeita de duplicidade e confirmar pessoa+representação sem parcial.
- Validação: mínimo após exclusão, refazer, duplicata provável, rollback e payloads de upload hostis.
- Impacto de segurança: impede path traversal, cadastro duplicado automático e resíduo biométrico.
- Status: pendente

### BLG-018 — Implementar embeddings versionados e índice

- Fase: 7
- Tipo: visão/dados
- Risco: crítico
- Dependências: BLG-006, BLG-017
- Requisitos: FACE-003
- Arquivos-alvo: app/recognition/embedder.py, app/recognition/index.py, tests/recognition/
- Resultado esperado: embedding normalizado com modelo/versão/dimensão e índice reconstruível.
- Validação: determinismo/tolerância, NaN/dimensão, round-trip, reconstrução e atualização.
- Impacto de segurança: evita mistura silenciosa de modelos e corrupção do índice.
- Status: pendente

### BLG-019 — Implementar matcher seguro e providers

- Fase: 7
- Tipo: visão/desempenho
- Risco: crítico
- Dependências: BLG-018
- Requisitos: FACE-004, FACE-006
- Arquivos-alvo: app/recognition/matcher.py, app/recognition/providers.py, tests/recognition/
- Resultado esperado: conhecido somente acima do limiar calibrável, desconhecido abaixo, CPU obrigatório e GPU opcional com fallback.
- Validação: positivos/negativos, borda, base vazia, provider ausente e comparação CPU/GPU.
- Impacto de segurança: falso positivo é risco de identidade; default inseguro é proibido.
- Status: pendente

### BLG-020 — Implementar tracking e antirrepetição

- Fase: 7
- Tipo: visão/eventos
- Risco: alto
- Dependências: BLG-019
- Requisitos: FACE-005
- Arquivos-alvo: app/recognition/tracker.py, app/services/detection.py, tests/recognition/
- Resultado esperado: ID temporal, reaproveitamento controlado do reconhecimento e janela de novo evento.
- Validação: presença contínua, oclusão, reaparecimento, cruzamento e expiração.
- Impacto de segurança: evita evento falso/repetido e associação temporal indevida.
- Status: pendente

## P1 — Operação completa, distribuída e hardening

### BLG-021 — Persistir eventos idempotentes

- Fase: 8
- Tipo: dados/eventos
- Risco: alto
- Dependências: BLG-020
- Requisitos: DB-005
- Arquivos-alvo: app/models/detection.py, app/repositories/detections.py, app/services/detection.py, tests/detections/
- Resultado esperado: evento completo com ID global, tracking, origem e estado de sincronização.
- Validação: criação, repetição, timezone, transação e imagem opcional.
- Impacto de segurança: preserva rastreabilidade sem duplicar dados pessoais.
- Status: pendente

### BLG-022 — Entregar histórico, filtros e exportação

- Fase: 8
- Tipo: GUI/relatório
- Risco: alto
- Dependências: BLG-021, BLG-008
- Requisitos: UI-004, PRIV-005
- Arquivos-alvo: app/interface/history/, app/services/exports.py, tests/history/
- Resultado esperado: filtros/paginação e CSV/PDF/JSON conforme escopo, com auditoria.
- Validação: combinações, grande volume, CSV injection, arquivos, autorização e timezone.
- Impacto de segurança: exportação é canal de exfiltração e exige controle rigoroso.
- Status: pendente

### BLG-023 — Implementar supervisor multicâmera

- Fase: 9
- Tipo: concorrência/câmeras
- Risco: crítico
- Dependências: BLG-013, BLG-021
- Requisitos: CAM-006
- Arquivos-alvo: app/cameras/supervisor.py, app/services/runtime.py, tests/cameras/
- Resultado esperado: unidade isolada por câmera, inclusão/remoção em runtime e estado individual.
- Validação: fontes simultâneas, uma lenta/falha, runtime add/remove e concorrência.
- Impacto de segurança: falha isolada reduz indisponibilidade sistêmica.
- Status: pendente

### BLG-024 — Implementar reconexão e limites de capacidade

- Fase: 9
- Tipo: resiliência/desempenho
- Risco: crítico
- Dependências: BLG-023
- Requisitos: CAM-004, PERF-003
- Arquivos-alvo: app/cameras/reconnect.py, app/devices/capacity.py, tests/cameras/
- Resultado esperado: backoff configurável, recuperação, modelo/pool controlado e recusa/degradação acima do limite.
- Validação: disconnect/reconnect, storm, limite excedido, contagem de modelos e memória.
- Impacto de segurança: evita DoS por retry e exaustão de CPU/GPU/RAM.
- Status: pendente

### BLG-025 — Construir painel principal

- Fase: 10
- Tipo: GUI
- Risco: alto
- Dependências: BLG-023
- Requisitos: UI-001
- Arquivos-alvo: app/interface/dashboard/, tests/interface/
- Resultado esperado: grade adaptativa, tela cheia, métricas, estados, últimas detecções/alertas e controles.
- Validação: teste Qt com várias fontes, resize, offline, ações e profiling de responsividade.
- Impacto de segurança: exibição deve aplicar escopo e não vazar preview.
- Status: pendente

### BLG-026 — Construir telas administrativas e preferências

- Fase: 10
- Tipo: GUI/administração
- Risco: alto
- Dependências: BLG-025, BLG-008
- Requisitos: UI-003, UI-006
- Arquivos-alvo: app/interface/cameras/, app/interface/settings/, app/interface/admin/, tests/interface/
- Resultado esperado: câmeras, configurações, usuários, logs, auditoria, dispositivos, tema e idioma.
- Validação: validação de campos, teste conexão assíncrono, RBAC, mascaramento e persistência.
- Impacto de segurança: ações administrativas e segredos exigem menor privilégio.
- Status: pendente

### BLG-027 — Persistir e agrupar desconhecidos

- Fase: 11
- Tipo: visão/dados
- Risco: alto
- Dependências: BLG-021
- Requisitos: DB-006
- Arquivos-alvo: app/models/unknown.py, app/services/unknowns.py, app/recognition/grouping.py, tests/unknowns/
- Resultado esperado: temporários/grupos corrigíveis, intervalo antirrepetição e classificações.
- Validação: sequência repetida, grupos/separação, retenção e correção humana.
- Impacto de segurança: evita perfil automático e armazenamento descontrolado.
- Status: pendente

### BLG-028 — Entregar revisão e conversão de desconhecidos

- Fase: 11
- Tipo: GUI/fluxo
- Risco: alto
- Dependências: BLG-027, BLG-017
- Requisitos: REG-007, UI-005
- Arquivos-alvo: app/interface/unknowns/, app/services/people.py, tests/unknowns/
- Resultado esperado: converter, importar/atualizar, excluir, ignorar e classificar com proveniência.
- Validação: operações unitárias/em lote, upload hostil, reindexação, concorrência e RBAC.
- Impacto de segurança: impede associação biométrica silenciosa ou sem autoridade.
- Status: pendente

### BLG-029 — Implementar contratos da API central

- Fase: 12
- Tipo: API
- Risco: crítico
- Dependências: BLG-022, BLG-028
- Requisitos: SYNC-001
- Arquivos-alvo: app/api/, tests/api/
- Resultado esperado: API versionada, OpenAPI, paginação, erros e idempotency keys para recursos e sync.
- Validação: contract tests, entradas inválidas, paginação, compatibilidade e erros.
- Impacto de segurança: nova trust boundary exige validação e mínimo de dados.
- Status: pendente

### BLG-030 — Endurecer transporte e autorização da API

- Fase: 12
- Tipo: segurança/API
- Risco: crítico
- Dependências: BLG-029, BLG-007, BLG-008
- Requisitos: SEC-002
- Arquivos-alvo: app/api/security.py, app/configuration/security.py, tests/security/
- Resultado esperado: TLS fora de local, CORS/hosts restritivos e authn/authz por endpoint.
- Validação: certificado inválido, HTTP, token ausente/inválido, CORS/host e BOLA/IDOR.
- Impacto de segurança: protege dados biométricos em trânsito e endpoints centrais.
- Status: pendente

### BLG-031 — Implementar enrollment e inventário de dispositivos

- Fase: 13
- Tipo: dispositivos/segurança
- Risco: crítico
- Dependências: BLG-030
- Requisitos: DEVICE-001, DEVICE-002
- Arquivos-alvo: app/devices/, app/api/devices.py, tests/devices/
- Resultado esperado: aprovação, credencial própria, revogação/rotação, heartbeat, versão e capacidade.
- Validação: enrollment, clone, revogação, rotação, timeout e versão incompatível.
- Impacto de segurança: estabelece identidade de máquina e limite de confiança.
- Status: pendente

### BLG-032 — Distribuir cache e configurações versionadas

- Fase: 13
- Tipo: sincronização/dados
- Risco: crítico
- Dependências: BLG-031, BLG-018
- Requisitos: SYNC-002, SYNC-005, DEVICE-003
- Arquivos-alvo: app/synchronization/cache.py, app/devices/configuration.py, tests/synchronization/
- Resultado esperado: cliente recebe somente dados autorizados, valida versões e troca índice/configuração atomicamente.
- Validação: carga inicial/delta, lacuna, cache corrompido, revogação, transferência de câmera e rollback.
- Impacto de segurança: controla réplica local de biometria e credenciais de câmera.
- Status: pendente

### BLG-033 — Implementar protocolo idempotente e diagnóstico remoto

- Fase: 13
- Tipo: sincronização/operação
- Risco: crítico
- Dependências: BLG-032
- Requisitos: SYNC-004, DEVICE-004
- Arquivos-alvo: app/synchronization/protocol.py, app/devices/diagnostics.py, tests/synchronization/
- Resultado esperado: deduplicação, estados de entrega, conflitos visíveis e diagnóstico/ações remotas auditados.
- Validação: replay, timeout após commit, ordem trocada, conflito, cliente offline e RBAC remoto.
- Impacto de segurança: impede duplicação e abuso de controle remoto.
- Status: pendente

### BLG-034 — Implementar outbox e modo offline

- Fase: 14
- Tipo: resiliência/sincronização
- Risco: crítico
- Dependências: BLG-033
- Requisitos: SYNC-003
- Arquivos-alvo: app/synchronization/outbox.py, app/database/local/, tests/synchronization/
- Resultado esperado: fila durável/protegida, capacidade finita e reconhecimento com cache válido sem servidor.
- Validação: rede perdida, reinício, fila cheia, corrupção recuperável e retorno.
- Impacto de segurança: dados biométricos/eventos locais exigem proteção equivalente.
- Status: pendente

### BLG-035 — Implementar recuperação e observabilidade do sync

- Fase: 14
- Tipo: observabilidade/resiliência
- Risco: alto
- Dependências: BLG-034
- Requisitos: SYNC-006
- Arquivos-alvo: app/synchronization/worker.py, app/metrics/, app/interface/devices/, tests/synchronization/
- Resultado esperado: retry/backoff, quarentena, métricas e reprocessamento autorizado.
- Validação: atraso, poison message, retry storm, quarentena, métricas e RBAC.
- Impacto de segurança: evita loop de dados maliciosos e exposição no diagnóstico.
- Status: pendente

### BLG-036 — Modelar ameaça e selecionar vivacidade

- Fase: 15
- Tipo: pesquisa/segurança biométrica
- Risco: crítico
- Dependências: BLG-019, BLG-035
- Requisitos: FACE-007
- Arquivos-alvo: .planning/research/, .planning/DECISIONS.md, .planning/RISKS.md
- Resultado esperado: comparar piscada, movimento, textura, desafio e anti-spoofing; definir limitações e política dos quatro estados.
- Validação: revisão de fontes/modelo/licença e protocolo de ataques autorizado.
- Impacto de segurança: reduz falsa promessa de anti-spoofing.
- Status: pendente

### BLG-037 — Implementar e calibrar vivacidade

- Fase: 15
- Tipo: visão/segurança
- Risco: crítico
- Dependências: BLG-036
- Requisitos: FACE-007
- Arquivos-alvo: app/recognition/liveness.py, app/services/detection.py, tests/liveness/
- Resultado esperado: aprovada/reprovada/inconclusiva/desativada integrados ao evento e política.
- Validação: pessoa real, foto, impressão, tela, vídeo, baixa luz, inconclusivo e desativado.
- Impacto de segurança: sinal adicional, nunca garantia absoluta.
- Status: pendente

### BLG-038 — Implementar regras de alerta

- Fase: 16
- Tipo: funcional/alertas
- Risco: alto
- Dependências: BLG-024, BLG-035, BLG-037
- Requisitos: ALERT-001, ALERT-004
- Arquivos-alvo: app/services/alerts.py, app/models/alert.py, tests/alerts/
- Resultado esperado: regras faciais, operacionais, recursos, fraude e autenticação com severidade/escopo/janela.
- Validação: regra por categoria, limites, desativada, escopo e conteúdo.
- Impacto de segurança: alerta mal calibrado pode vazar ou gerar DoS operacional.
- Status: pendente

### BLG-039 — Implementar canais e ciclo de vida de alertas

- Fase: 16
- Tipo: integração/alertas
- Risco: alto
- Dependências: BLG-038
- Requisitos: ALERT-002, ALERT-003
- Arquivos-alvo: app/alerts/channels/, app/interface/alerts/, tests/alerts/
- Resultado esperado: interface/log/local e canais externos opt-in, dedupe, retry, quarentena e resolução.
- Validação: defaults, tempestade, agravamento, timeout, destino inválido, segredo e auditoria.
- Impacto de segurança: canais externos são nova saída de dados e segredos.
- Status: pendente

### BLG-040 — Consolidar threat model, criptografia e auditoria

- Fase: 17
- Tipo: hardening
- Risco: crítico
- Dependências: BLG-039
- Requisitos: SEC-005, SEC-006
- Arquivos-alvo: .planning/RISKS.md, app/security/, app/services/audit.py, tests/security/
- Resultado esperado: trust boundaries/invariantes, proteção em repouso, rotação e cobertura de ações privilegiadas.
- Validação: ACL, chave ausente/incorreta, rotação em ambiente seguro, trilha de auditoria e redaction.
- Impacto de segurança: controle central contra vazamento e adulteração.
- Status: pendente

### BLG-041 — Implementar retenção, exclusão e acesso do titular

- Fase: 17
- Tipo: privacidade/dados
- Risco: crítico
- Dependências: BLG-032, BLG-040
- Requisitos: PRIV-003, PRIV-004, PRIV-005
- Arquivos-alvo: app/services/retention.py, app/services/privacy.py, tests/privacy/
- Resultado esperado: política por dado, limpeza idempotente, mapa de exclusão distribuída e exportação/acesso autorizado.
- Validação: relógio controlado, dry-run, limites de caminho, caches offline, hold e auditoria.
- Impacto de segurança: reduz retenção indevida e garante revogação real.
- Status: pendente

### BLG-042 — Implementar backup, restore, disco e limpeza

- Fase: 17
- Tipo: operação/dados
- Risco: crítico
- Dependências: BLG-041
- Requisitos: DB-007
- Arquivos-alvo: scripts/backup.py, scripts/restore.py, app/services/storage.py, tests/operations/
- Resultado esperado: backup protegido/verificado, restore isolado, alerta de disco e limpeza confinada.
- Validação: backup/restore, corrupção, chave ausente, pouco disco e tentativa de sair do diretório permitido.
- Impacto de segurança: backup é cópia sensível e operação de limpeza é destrutiva.
- Status: pendente

### BLG-043 — Implantar gates de supply chain e segurança

- Fase: 17
- Tipo: CI/segurança
- Risco: alto
- Dependências: BLG-040
- Requisitos: SEC-008
- Arquivos-alvo: pipeline CI, configurações de scanners, documentação de suppressions
- Resultado esperado: SAST, SCA, secret scan, inventário/licença/modelos e bloqueio por severidade.
- Validação: findings sintéticos, artefatos SARIF/JSON, suppression governada e execução reproduzível.
- Impacto de segurança: previne release com segredo ou vulnerabilidade crítica conhecida.
- Status: pendente

## P2 — Otimização, evidência e release

### BLG-044 — Definir baseline e perfilar o sistema

- Fase: 18
- Tipo: desempenho
- Risco: alto
- Dependências: BLG-043
- Requisitos: PERF-006
- Arquivos-alvo: scripts/benchmark.py, app/metrics/, tests/performance/
- Resultado esperado: benchmark por hardware/provider/câmeras/resolução e perfil por etapa.
- Validação: execução reproduzível com ambiente e séries de métricas registradas.
- Impacto de segurança: capacidade insuficiente pode causar indisponibilidade e perda de eventos.
- Status: pendente

### BLG-045 — Implementar adaptação e shutdown seguro

- Fase: 18
- Tipo: desempenho/resiliência
- Risco: crítico
- Dependências: BLG-044, BLG-034
- Requisitos: PERF-004, PERF-005
- Arquivos-alvo: app/services/adaptive.py, app/services/runtime.py, tests/performance/
- Resultado esperado: degradação com histerese e sequência idempotente que libera câmera/workers e preserva outbox.
- Validação: carga crescente, recuperação, worker travado, fila pendente, shutdown repetido e regressão de precisão.
- Impacto de segurança: evita DoS e corrupção no encerramento.
- Status: pendente

### BLG-046 — Executar suítes automatizadas completas

- Fase: 19
- Tipo: teste
- Risco: crítico
- Dependências: BLG-045
- Requisitos: TEST-002, TEST-004, TEST-005, TEST-006
- Arquivos-alvo: tests/
- Resultado esperado: câmera simulada, DB, API, auth, GUI, segurança, offline, sync e E2E executados em pipeline limpo.
- Validação: relatório de testes/cobertura, repetição da suíte crítica e triagem de flakiness.
- Impacto de segurança: reduz regressão em authz, sync e parsing.
- Status: pendente

### BLG-047 — Calibrar e validar biometria

- Fase: 19
- Tipo: validação biométrica
- Risco: crítico
- Dependências: BLG-037, BLG-046
- Requisitos: FACE-008, TEST-003
- Arquivos-alvo: tests/biometric/, .planning/TESTING.md, .planning/RISKS.md
- Resultado esperado: FAR/FRR, falsos positivos/negativos, robustez, vieses, limiar aprovado e limitações.
- Validação: protocolo versionado com dados autorizados e revisão independente.
- Impacto de segurança: impede liberar reconhecimento com limiar arbitrário ou viés desconhecido.
- Status: pendente

### BLG-048 — Executar carga, soak, restore e validação manual

- Fase: 19
- Tipo: teste/operação
- Risco: crítico
- Dependências: BLG-042, BLG-044, BLG-047
- Requisitos: TEST-007
- Arquivos-alvo: tests/performance/, .planning/TESTING.md, .planning/phases/19-testing/VERIFICATION.md
- Resultado esperado: evidência de capacidade, vazamento, reconexão, disco, múltiplas câmeras, backup/restore, hardware e shutdown.
- Validação: comparação com metas aprovadas; gaps permanecem pendentes e bloqueiam afirmações correspondentes.
- Impacto de segurança: valida disponibilidade, recuperação e ausência de perda silenciosa.
- Status: pendente

### BLG-049 — Empacotar, instalar e testar upgrade/rollback

- Fase: 20
- Tipo: release
- Risco: alto
- Dependências: BLG-048
- Requisitos: TEST-001, SEC-008
- Arquivos-alvo: configuração de empacotamento, scripts/install/, release/
- Resultado esperado: pacote reproduzível para plataformas aprovadas, versão, SBOM/hash/assinatura conforme decisão e rollback.
- Validação: instalação limpa, smoke, upgrade, rollback e inspeção por segredos/dados.
- Impacto de segurança: cadeia de distribuição e configuração de produção.
- Status: pendente

### BLG-050 — Concluir documentação e checklist de release

- Fase: 20
- Tipo: documentação/operação
- Risco: alto
- Dependências: BLG-049
- Requisitos: PRIV-006 e todos os requisitos de documentação/validação
- Arquivos-alvo: README.md, docs/, .planning/STATE.md, .planning/CHANGELOG.md
- Resultado esperado: instalação Windows/Linux, API, primeira pessoa/câmera/admin, backup/restore, sync/offline, segurança/LGPD, limites, manutenção e release notes.
- Validação: walkthrough por operador não autor, links/comandos, checklist final e consistência com comportamento testado.
- Impacto de segurança: documentação errada pode induzir implantação insegura ou uso proibido.
- Status: pendente

## Itens futuros

Os itens abaixo não pertencem ao primeiro release, salvo nova decisão de escopo. Permanecem em estado futuro, não concluído.

| ID | Prioridade | Item | Dependências para reavaliar | Motivo/critério de entrada | Status |
|---|---|---|---|---|---|
| FUT-001 | P3 | Balanceamento automático de câmeras entre dispositivos | Fases 13, 18 e métricas reais | necessário somente após capacidade e topologia medidas | futuro |
| FUT-002 | P3 | Alta disponibilidade do servidor e banco | SLO/RPO/RTO aprovados | complexidade operacional não justificada sem metas | futuro |
| FUT-003 | P3 | Cliente web/mobile complementar | API estável e threat model específico | PySide6 é a interface preferencial inicial | futuro |
| FUT-004 | P3 | Sensores de profundidade para vivacidade | hardware e orçamento definidos | melhora depende de equipamento não informado | futuro |
| FUT-005 | P3 | Aceleradores adicionais e execução edge especializada | benchmarks e demanda | hardware alvo unspecified | futuro |
| FUT-006 | P3 | Multi-tenant/organizações isoladas | modelo de negócio e compliance | amplia fortemente autorização e isolamento | futuro |
| FUT-007 | P3 | Atualização remota assinada de clientes | PKI, canal e rollback maduros | alto impacto de supply chain | futuro |
| FUT-008 | P3 | Agrupamento de desconhecidos com revisão assistida avançada | métricas de erro e aprovação de privacidade | risco de perfilização requer evidência | futuro |
| FUT-009 | P3 | Integrações SIEM/observabilidade externas | destino, contrato e minimização aprovados | integrações externas estão desativadas por padrão | futuro |
| FUT-010 | P3 | Suporte adicional a idiomas e acessibilidade avançada | pesquisa de usuários | além do baseline funcional inicial | futuro |

## Fora de escopo

Estes itens são explicitamente excluídos. Qualquer reconsideração exige novo escopo, base legal, threat model, revisão de privacidade e autorização.

| ID | Item | Justificativa | Status |
|---|---|---|---|
| OOS-001 | Buscar ou enriquecer identidades em redes sociais | viola finalidade/minimização e foi proibido no pedido | fora de escopo |
| OOS-002 | Rastrear pessoas fora das câmeras cadastradas | excede o perímetro autorizado | fora de escopo |
| OOS-003 | Identificação secreta ou sem autorização | incompatível com uso responsável e LGPD | fora de escopo |
| OOS-004 | Usar bases obtidas ilegalmente | ilegal e proibido | fora de escopo |
| OOS-005 | Compartilhar biometria automaticamente com terceiros | nova finalidade/transferência sem governança | fora de escopo |
| OOS-006 | Declarar vivacidade infalível | tecnicamente falso e inseguro | fora de escopo |
| OOS-007 | Executar DAST, fuzzing agressivo ou scan ativo em produção sem autorização | alvo e autorização estão unspecified | fora de escopo |
| OOS-008 | Tomar decisão punitiva ou negar direito de forma autônoma apenas pelo reconhecimento | risco elevado de falso positivo e devido processo | fora de escopo |
| OOS-009 | Reconhecimento de voz, áudio ambiente ou análise emocional | não solicitado e amplia coleta sensível | fora de escopo |
| OOS-010 | Controle PTZ, gravação contínua estilo DVR ou análise geral de objetos | não fazem parte do núcleo facial descrito | fora de escopo |

## Próxima tarefa recomendada

BLG-001 — Fechar contexto operacional e legal. Enquanto as respostas estiverem ausentes, registrar unspecified, continuar apenas em design/testes com dados simulados ou autorizados e não afirmar prontidão para uso real.
