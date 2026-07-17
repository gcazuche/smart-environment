# Roadmap GSD — Sistema de Câmeras Inteligentes

Versão: 0.1
Data: 2026-07-17
Status global: em andamento; Fase 2 iniciada e 1 de 20 fases concluídas.

## Regras de execução

1. Executar as fases exatamente na ordem deste documento.
2. Antes de cada fase, criar contexto, pesquisa necessária, plano com tarefas atômicas e critérios verificáveis.
3. Implementar uma tarefa por vez; registrar decisões, riscos, comandos, resultados e mudanças de estado.
4. Não avançar com erro crítico, regressão conhecida sem decisão, requisito crítico não atendido ou teste obrigatório sem evidência.
5. Hardware real, GPU, rede distribuída, precisão biométrica, vivacidade, carga e restore só contam como validados quando executados em ambiente autorizado e documentado.
6. Uma decisão ainda não tomada permanece unspecified. Não escolher biblioteca, limiar, capacidade, retenção ou política legal apenas para liberar uma fase.
7. Segurança e privacidade são transversais: os controles de base entram nas fases iniciais e são consolidados na Fase 17.

## Gates transversais

- Gate de especificação: requisitos e decisões da tarefa estão claros.
- Gate funcional: critérios de aceitação foram demonstrados.
- Gate de qualidade: lint, format-check, type-check, testes aplicáveis e build/import passam.
- Gate de segurança: não há segredo exposto nem finding crítico sem contenção/decisão.
- Gate de privacidade: dados usados são autorizados, minimizados e sujeitos à retenção definida.
- Gate de evidência: VERIFICATION e estado persistente registram comandos e resultados reais.
- Gate de reversão: mudança possui rollback ou estratégia de recuperação testável.

---

## Fase 1 — Fundação e ambiente

Status: concluída em 2026-07-17, com ressalvas operacionais em `VERIFICATION.md`

**Objetivo:** inicializar o fluxo GSD, delimitar a primeira versão, pesquisar escolhas críticas, definir arquitetura-base e criar um projeto Python reproduzível, modular e seguro.

**Requisitos:** SEC-001, SEC-007, PRIV-001, TEST-001.

**Dependências:** nenhuma. Antes de código funcional, registrar como unspecified as respostas ainda ausentes sobre capacidade, hardware/GPU, SO, banco, rede, retenção, locais, base legal, metas biométricas e escopo exato da V1.

**Entregáveis:**

- Documentos GSD iniciais, pesquisas técnicas e ADRs de escolhas confirmadas.
- Estrutura modular de pacotes, pyproject/lockfile, ambiente virtual e configuração de qualidade.
- .env.example sem segredos, logging seguro, tratamento global inicial de exceções e comandos de desenvolvimento.
- Matriz de compatibilidade para Python, OpenCV, motor facial/ONNX, PySide6, FastAPI e banco; escolhas finais somente após evidência.

**Critérios de conclusão:**

- Projeto instala e importa em ambiente limpo suportado.
- Comandos de lint, formatação, type-check e teste vazio/smoke estão documentados e passam.
- Finalidade, uso autorizado e bloqueios de privacidade estão registrados.
- Nenhum segredo ou dado biométrico real foi incluído.
- Contexto, plano, resumo, verificação e estado da fase foram atualizados.

**Riscos:** incompatibilidade de wheels/driver, escolha prematura de stack, falta de base legal, dependência sem manutenção e divergência Windows/Linux.

**Validação:** recriar ambiente do zero; executar import/build, lint, format-check, type-check, Pytest smoke e secret scan; revisar documentos e ADRs. Teste não executado permanece pendente.

---

## Fase 2 — Configurações e banco

Status: em andamento — contexto aberto; primeiro slice local ainda não implementado

**Objetivo:** implementar configuração tipada e persistência transacional com esquema, migrações, integridade e abstração de embeddings.

**Requisitos:** DB-001, DB-002, DB-003, DB-004, SEC-003, PRIV-002.

**Dependências:** Fase 1 concluída. O runtime SQLite local pode iniciar sem rede. A
prova de conceito documentada de Supabase/PostgreSQL, pgvector e Storage é gate para
implementar o adaptador remoto e encerrar a fase. Alternativa local/gerenciada é
fallback se o spike reprovar segurança, operação, custo ou compatibilidade; não uma
escolha reaberta sem evidência.

**Entregáveis:**

- Modelos e repositories para todas as tabelas mínimas.
- Migração inicial e procedimento de upgrade/downgrade seguro.
- Configuração validada para banco, arquivos, limites, reconhecimento e ambiente.
- Interface de armazenamento/índice de embeddings com metadados de versão.
- Política inicial de minimização entre embedding, recorte e frame.

**Critérios de conclusão:**

- Banco vazio migra até head de forma reproduzível.
- Restrições e transações impedem estados inválidos e falhas parciais.
- Configurações inválidas são recusadas antes de aplicação.
- Round-trip de embedding fictício respeita tipo/dimensão sem biometria real.
- Estratégia pgvector/FAISS/alternativa e fonte de verdade estão decididas por ADR ou marcadas como bloqueio.

**Riscos:** esquema superdimensionado, lock-in de banco, vetor incompatível com modelo, dados sensíveis sem classificação e migração irreversível.

**Validação:** testes unitários de configuração; integração em banco descartável; upgrade/downgrade suportado; FK/unique/check; transações com rollback; explain de consultas-base; revisão de injection e minimização.

---

## Fase 3 — Autenticação e usuários

Status: planejada

**Objetivo:** controlar identidade, sessão e permissões antes de expor funções administrativas ou dados sensíveis.

**Requisitos:** AUTH-001 a AUTH-006.

**Dependências:** Fase 2 concluída; decisão documentada de Argon2/bcrypt e JWT/sessão; política de senha, duração de sessão, lockout e recuperação permanece unspecified até aprovação.

**Entregáveis:**

- Login/logout, hash seguro, rehash e ciclo de sessão.
- Papéis Administrador, Operador e Visualizador com negação por padrão.
- Escopo por câmera/local no domínio e repositório.
- Limite de tentativas, bloqueio temporário, recuperação controlada e script de primeiro administrador.
- Registros de login e ações de segurança.

**Critérios de conclusão:**

- Matriz positiva e negativa demonstra cada permissão.
- Senha, hash, token e segredo não aparecem em código, resposta ou log.
- Logout, expiração, revogação e usuário inativo impedem acesso.
- Bootstrap e recuperação resistem a reutilização, enumeração e senha fraca.
- Ações críticas deixam trilha verificável.

**Riscos:** elevação de privilégio, sessão não revogada, lockout abusável, recuperação vulnerável e escopo aplicado só na GUI.

**Validação:** testes de domínio/API/repositório para RBAC; expiração/replay; brute force controlado; enumeração; recuperação; inspeção de logs; revisão de matriz por papel e câmera/local.

---

## Fase 4 — Captura de uma câmera

Status: planejada

**Objetivo:** entregar captura confiável de uma fonte por vez, com abstração de drivers, diagnóstico e ciclo de vida sem bloquear a aplicação.

**Requisitos:** CAM-001, CAM-002, CAM-003, CAM-007, PERF-001.

**Dependências:** Fases 1–3 concluídas; a fonte real inicial está confirmada como a
webcam integrada do computador. Fonte simulada continua obrigatória para automação;
SO de produção e detalhes do hardware permanecem `unspecified`.

**Entregáveis:**

- Interface-base e adaptadores previstos para USB/integrada, IP/RTSP, arquivo e simulação.
- Serviço de captura com estados, FPS/resolução, último frame e liberação segura.
- Configuração/cadastro de uma câmera e operação “Testar conexão”.
- Script de listar/testar fontes e documentação Windows/Linux.
- ADR de concorrência para captura e GUI.

**Critérios de conclusão:**

- Fonte simulada e arquivo abrem, entregam frame e fecham sem handle órfão.
- Erro, timeout e fim de arquivo são tipados e não encerram o processo.
- Start/stop/restart é idempotente e não bloqueia a thread da interface.
- Hardware não disponível fica explicitamente pendente, nunca presumido.

**Riscos:** diferenças de backend OpenCV, credencial RTSP exposta, bloqueio em read, device lock e comportamento divergente por SO.

**Validação:** testes unitários dos adaptadores; integração com vídeo autorizado; ciclos repetidos; timeout/cancelamento; análise de handles; smoke manual em cada câmera real disponível.

---

## Fase 5 — Detecção facial

Status: planejada

**Objetivo:** construir pipeline desacoplado de frames e detectar/alinha faces elegíveis com backpressure.

**Requisitos:** CAM-005, FACE-001, FACE-002, PERF-002.

**Dependências:** Fase 4 concluída; detector/modelo escolhido por pesquisa e licenciamento; limites de tamanho/qualidade inicialmente unspecified até calibração.

**Entregáveis:**

- Contratos tipados para cada etapa do pipeline.
- Filas limitadas com política de frame mais recente.
- Detector de múltiplas faces, landmarks/alinhamento e motivos de rejeição.
- Métricas de latência, fila, descarte e erro.

**Critérios de conclusão:**

- Zero, uma e várias faces são tratados sem falha.
- Face parcial, pequena, na borda ou frame inválido recebe decisão explícita.
- Carga sustentada mantém memória limitada e a captura continua responsiva.
- Modelo, versão, licença e origem estão registrados.

**Riscos:** detecção enviesada, fila crescente, cópia excessiva de frames, falso negativo em perfil e modelo incompatível com Python/ONNX.

**Validação:** conjunto autorizado de imagens/vídeos; testes de contrato e limites; fila cheia; frame corrompido; benchmark preliminar CPU; revisão de memória e licenciamento.

---

## Fase 6 — Cadastro de pessoas

Status: planejada

**Objetivo:** cadastrar pessoas por sessão guiada de 10–100 imagens, com qualidade, revisão, duplicidade e persistência segura.

**Requisitos:** REG-001 a REG-006, UI-002, SEC-004.

**Dependências:** Fase 5 concluída; finalidade/base legal aprovadas; política de armazenamento e critérios de qualidade definidos ou bloqueando uso real.

**Entregáveis:**

- CRUD e ciclo de vida de pessoa.
- Fluxo guiado por frente/direita/esquerda/cima/baixo, expressão e iluminação.
- Portões de rosto único, nitidez, exposição, tamanho e enquadramento.
- Progresso, refazer/excluir foto e confirmação atômica.
- Verificação assistida de possível duplicidade e representação facial versionada.

**Critérios de conclusão:**

- Sessões válidas respeitam mínimo/máximo e cobertura exigida.
- Imagens ruins têm motivo claro e não entram silenciosamente.
- Cancelamento/falha remove temporários e não deixa pessoa parcial.
- Upload/importação não permite path traversal, conteúdo inválido ou excesso de tamanho.
- Duplicata suspeita exige revisão humana; não há mesclagem automática.

**Riscos:** coleta excessiva, cadastro sem consentimento, qualidade inconsistente, upload malicioso, duplicidade errada e vazamento de imagem temporária.

**Validação:** testes Qt/domínio; imagens sintéticas/autorizadas por portão; limites 10/100; perda de câmera; cancelamento/rollback; ataques de upload; matriz de autorização e auditoria.

---

## Fase 7 — Embeddings e reconhecimento

Status: planejada

**Objetivo:** gerar embeddings versionados, buscar candidatos e reconhecer somente com confiança suficiente, em CPU e GPU opcional.

**Requisitos:** FACE-003 a FACE-006.

**Dependências:** Fase 6 concluída; motor facial, modelo, licença, dimensão, índice, métrica e provider aprovados por ADR; limiar permanece unspecified até calibração.

**Entregáveis:**

- Serviço substituível de embedding e normalização.
- Índice local reconstruível e comparação com limiar.
- Resultado conhecido/desconhecido com confiança, versão e evidência mínima.
- Tracking temporal, cache curto e janela antirrepetição.
- Seleção segura de CPU/GPU com fallback.

**Critérios de conclusão:**

- Base vazia e score insuficiente sempre resultam em Desconhecido.
- Embedding inválido ou de versão/dimensão incompatível é rejeitado.
- Índice pode ser reconstruído sem perder fonte de verdade.
- Testes positivos e, principalmente, negativos cobrem fronteira do limiar.
- Resultado CPU/GPU respeita tolerância documentada.

**Riscos:** falso positivo, limiar arbitrário, incompatibilidade de vetores, índice obsoleto, drift e consumo duplicado de modelo.

**Validação:** pares autorizados positivos/negativos; dimensão/NaN; borda do limiar; base vazia; tracking/oclusão; reconstrução do índice; smoke CPU e GPU quando disponível.

---

## Fase 8 — Histórico de detecções

Status: planejada

**Objetivo:** persistir eventos deduplicados e permitir consulta/exportação segura e rastreável.

**Requisitos:** DB-005, UI-004 e dependências FACE-005, PRIV-005.

**Dependências:** Fase 7 concluída; timezone, janela de repetição, política de imagem e formato de exportação aprovados ou mantidos unspecified sem liberar uso real.

**Entregáveis:**

- Modelo/serviço de evento com identificador global, tracking, confiança, vivacidade e sincronização.
- Consultas paginadas e filtros completos.
- Exportadores CSV, PDF e JSON autorizados.
- Auditoria de consulta sensível e exportação.

**Critérios de conclusão:**

- Evento registra data/hora, câmera, local, dispositivo, situação e origem.
- Janela antirrepetição evita spam sem eliminar ocorrência legítima posterior.
- Filtros e exportações respeitam papel, câmera/local e timezone.
- CSV/PDF/JSON não permitem injeção nem revelam campos ocultos.

**Riscos:** crescimento rápido, evento duplicado, horário inconsistente, imagem excessiva e exportação com vazamento.

**Validação:** testes de criação/idempotência; filtros isolados e combinados; paginação; timezone; autorização; CSV injection; PDF/JSON; volume sintético e consulta indexada.

---

## Fase 9 — Suporte a várias câmeras

Status: planejada

Escopo: **pós-v1**; a primeira versão confirmada permanece com uma webcam.

**Objetivo:** operar várias fontes simultaneamente com isolamento, reconexão e limites de capacidade.

**Requisitos:** CAM-004, CAM-006, PERF-003.

**Dependências:** Fase 8 concluída; a primeira versão permanece limitada a uma webcam.
A expansão considera múltiplas webcams e ESP32, mas quantidade futura, modelos,
protocolos e hardware de referência permanecem `unspecified`.

**Entregáveis:**

- Supervisor por câmera/worker com estados isolados.
- Reconexão com backoff, jitter/limites conforme decisão.
- Compartilhamento seguro de modelo ou pool controlado.
- Limite por dispositivo e métricas individualizadas.

**Critérios de conclusão:**

- Falha de uma câmera não interrompe captura, reconhecimento ou GUI das demais.
- Inclusão/remoção/reinício em runtime não exige reinício global.
- Tentativas offline não causam busy loop ou crescimento de memória.
- Exceder capacidade gera recusa/degradação explícita, não colapso silencioso.

**Riscos:** deadlock, starvation, GIL/IPC, excesso de memória por modelo, instabilidade RTSP e tempestade de reconexão.

**Validação:** múltiplas fontes simuladas; desconexão/reconexão; uma fonte lenta; inclusão/remoção; contagem de modelos; memória prolongada; smoke no número de câmeras reais disponível.

---

## Fase 10 — Interface principal

Status: planejada

**Objetivo:** oferecer painel PySide6 moderno, responsivo e autorizado para operação cotidiana.

**Requisitos:** UI-001, UI-003, UI-006.

**Dependências:** Fase 9 concluída; design visual, idiomas e resoluções-alvo podem permanecer unspecified, mantendo funcionalidade e acessibilidade básica.

**Entregáveis:**

- Grade adaptativa, tela cheia e cartões de estado/métricas.
- Controles de sistema/câmera, últimas detecções e alertas.
- Telas de câmeras, configurações, usuários, logs, auditoria e dispositivos.
- Temas claro/escuro e base de localização.

**Critérios de conclusão:**

- GUI não trava sob captura/inferência simuladas.
- Estado mostrado corresponde ao serviço, inclusive offline/reconectando.
- Cada ação respeita RBAC/escopo e confirma operação destrutiva.
- Segredos e dados não autorizados permanecem mascarados.

**Riscos:** thread incorreta no Qt, renderização cara de muitos frames, estado divergente, vazamento por preview e baixa usabilidade.

**Validação:** testes Qt; E2E com fontes simuladas; redimensionamento/grade; falhas; matriz de permissão; tema; resolução menor; profiling da thread da GUI e roteiro manual.

---

## Fase 11 — Pessoas desconhecidas

Status: planejada

**Objetivo:** registrar e revisar desconhecidos com agrupamento conservador, retenção e conversão autorizada.

**Requisitos:** DB-006, REG-007, UI-005.

**Dependências:** Fase 10 concluída; política de salvar recorte/frame, intervalo, agrupamento e retenção aprovada.

**Entregáveis:**

- Identificador temporário, grupo e estados ignorado/suspeito/autorizado.
- Deduplicação temporal e agrupamento corrigível.
- Tela “Pessoas desconhecidas” e operações em lote seguras.
- Conversão em pessoa cadastrada, atualização/importação e reindexação.

**Critérios de conclusão:**

- Centenas de imagens repetidas não são salvas por presença contínua.
- Agrupamento nunca cria identidade real automaticamente.
- Conversão preserva eventos/proveniência e atualiza versão dos embeddings.
- Exclusão, classificação e imagens respeitam autorização e retenção.

**Riscos:** agrupamento de pessoas diferentes, criação indevida de perfil, crescimento de armazenamento, exposição de frames e operação em lote errada.

**Validação:** sequências repetidas; agrupamento/separação; correção humana; conversão; importação hostil; exclusão/retenção; autorização e concorrência.

---

## Fase 12 — API central

Status: planejada

**Objetivo:** expor contratos seguros e versionados para preparar operação cliente-servidor.

**Requisitos:** SYNC-001, SEC-002, CAM-008.

**Dependências:** Fase 11 concluída; internet é a preferência confirmada e LAN/gateway
local continua suportada. Domínio, certificados, região/plano do Supabase, custos,
quotas e estratégia final de deploy permanecem `unspecified` até prova de conceito.

**Entregáveis:**

- API versionada para recursos e sincronização.
- OpenAPI/documentação, paginação, erros e idempotency keys.
- Autenticação de usuário/dispositivo e autorização por recurso.
- Health/readiness com conteúdo mínimo.
- Configuração TLS/CORS/hosts por ambiente.
- Gateway autenticado para frames ESP32; o dispositivo não recebe chave elevada do
  Supabase nem expõe servidor de câmera diretamente à internet.

**Critérios de conclusão:**

- Contratos de sucesso/erro são estáveis e testados.
- Endpoint sensível sem autenticação/escopo é negado.
- TLS é obrigatório fora do perfil local explícito.
- Dados/segredos não aparecem em erro, health ou documentação indevida.

**Riscos:** API ampla demais, BOLA/IDOR, CORS permissivo, breaking changes, certificado mal gerido e exposição acidental de docs.

**Validação:** contract tests/OpenAPI; matriz authz; entradas inválidas; TLS/certificado; CORS/host; idempotência; paginação; rate limits definidos e teste de log/redaction.

---

## Fase 13 — Dispositivos e sincronização

Status: planejada

**Objetivo:** registrar clientes confiáveis, distribuir cache autorizado e sincronizar alterações/eventos com idempotência e versões.

**Requisitos:** SYNC-002, SYNC-004, SYNC-005, DEVICE-001 a DEVICE-004.

**Dependências:** Fase 12 concluída; processo de enrollment, rotação de credencial, conflito e revogação precisa de decisão formal.

**Entregáveis:**

- Enrollment/aprovação/revogação de dispositivo.
- Heartbeat, inventário, versão, capacidade, painel e modo manutenção.
- Atribuição versionada de câmeras/configurações.
- Cache local protegido de cadastros autorizados.
- Protocolo idempotente de eventos/deltas e reconciliação.
- Diagnóstico remoto separado de ações mutáveis.

**Critérios de conclusão:**

- Cliente não aprovado não recebe dados nem envia eventos válidos.
- Reenvio do mesmo item produz um efeito.
- Lacuna de versão dispara reconciliação; índice troca atomicamente.
- Revogar dispositivo/pessoa interrompe acesso segundo SLA ainda a definir.
- Diagnóstico e ação remota são autorizados e auditados.

**Riscos:** clonagem de dispositivo, cache excessivo, conflito perdido, split brain, revogação tardia e diagnóstico remoto abusivo.

**Validação:** múltiplos clientes simulados; enrollment/rotação/revogação; replay; timeout após commit; delta/lacuna; configuração conflitante; cache corrompido e authz remoto.

---

## Fase 14 — Funcionamento offline

Status: planejada

**Objetivo:** manter reconhecimento local temporário e sincronizar com segurança após perda de conectividade.

**Requisitos:** SYNC-003, SYNC-006.

**Dependências:** Fase 13 concluída; duração offline, validade do cache, capacidade da fila e comportamento quando cheia permanecem unspecified até dimensionamento.

**Entregáveis:**

- Outbox local durável e protegida.
- Estados online/offline/degradado, backpressure e quarentena.
- Retry com backoff e retomada após reinício.
- Métricas de atraso/fila/último sucesso e controles autorizados de reprocessamento.

**Critérios de conclusão:**

- Perda de rede não interrompe reconhecimento com cache válido.
- Reinício não perde itens pendentes.
- Retorno da rede não duplica eventos confirmados.
- Fila cheia não cresce sem limite; comportamento é explícito e alertável.
- Payload inválido não bloqueia para sempre os itens seguintes.

**Riscos:** perda/duplicação, fila cheia, dado local desprotegido, cache obsoleto, conflito após longo offline e retry storm.

**Validação:** desligar/restaurar servidor; rede intermitente; reinício; fila cheia; timeout após commit; poison message; reconciliação; inspeção de proteção local e métricas.

---

## Fase 15 — Vivacidade

Status: planejada

**Objetivo:** adicionar sinal de anti-spoofing configurável e explicitamente limitado.

**Requisitos:** FACE-007.

**Dependências:** Fase 14 concluída; método, modelo/licença, política por estado e requisitos de hardware permanecem unspecified até pesquisa/ameaças.

**Entregáveis:**

- Threat model de foto, impressão, tela e vídeo.
- Implementação escolhida de desafio/movimento/textura/modelo ou composição.
- Estados aprovada, reprovada, inconclusiva e desativada.
- Política de reconhecimento/alerta e documentação de limitações.

**Critérios de conclusão:**

- Sistema nunca declara vivacidade “totalmente segura”.
- Estado inconclusivo não é tratado silenciosamente como aprovado.
- Recurso pode ser desativado com indicação visível e auditável.
- Dados adicionais respeitam minimização e retenção.

**Riscos:** falsa sensação de segurança, viés, falso bloqueio, replay sofisticado, latência e modelo sem manutenção.

**Validação:** protocolo autorizado com pessoa real, foto, impressão, tela e vídeo; baixa luz; óculos; movimento; inconclusivo; desativado; métricas e limitações documentadas.

---

## Fase 16 — Alertas

Status: planejada

**Objetivo:** detectar eventos operacionais, faciais e de autenticação e entregá-los sem tempestade nem vazamento.

**Requisitos:** ALERT-001 a ALERT-004.

**Dependências:** Fase 15 concluída; canais, destinatários, limiares e SLAs permanecem unspecified; integrações externas desativadas por padrão.

**Entregáveis:**

- Motor de regras, severidade, escopo e janelas.
- Alertas para pessoas/lotação, câmera/infra, recursos/disco, vivacidade e login.
- Interface/log/notificação local; e-mail/webhook opcionais.
- Deduplicação, retry, quarentena, reconhecimento e resolução.

**Critérios de conclusão:**

- Regra desativada não dispara e regra ativada é rastreável.
- Tempestade é agrupada sem esconder agravamento.
- Falha de canal não interrompe captura/reconhecimento.
- Mensagem contém somente dados autorizados e nenhum segredo.

**Riscos:** alert fatigue, vazamento por webhook/e-mail, loop de retry, regra mal calibrada e dependência externa.

**Validação:** testes por categoria; limites/janelas; tempestade; agravamento; canal inválido; timeout/retry; segredo mascarado; RBAC e auditoria.

---

## Fase 17 — Segurança e auditoria

Status: planejada

**Objetivo:** consolidar hardening, auditoria, proteção em repouso, retenção, direitos da pessoa, backup e gates de supply chain.

**Requisitos:** DB-007, SEC-005, SEC-006, SEC-008, PRIV-003, PRIV-004, PRIV-005.

**Dependências:** Fase 16 concluída; revisão dos controles transversais das fases anteriores; DAST/scan ativo não autorizado enquanto autorização e alvo forem unspecified.

**Entregáveis:**

- Threat model atualizado, attack surface e invariantes.
- Criptografia/ACL, rotação de chaves e proteção de cache/outbox/backups.
- Auditoria completa e acesso restrito.
- Política/jobs de retenção, exclusão distribuída e acesso/exportação.
- Backup/restore, espaço em disco, limpeza e plano de recuperação.
- SAST, SCA, secret scan e gates de CI com suppressions governadas.

**Critérios de conclusão:**

- Nenhum finding crítico validado permanece sem correção/contenção formal.
- Backup restaurado em ambiente isolado com integridade demonstrada.
- Solicitação de exclusão remove/inativa todos os locais previstos e invalida caches.
- Ações privilegiadas são auditadas e registros não expõem segredos.
- Retenção e chaves possuem responsáveis e procedimentos aprovados.

**Riscos:** biometria vazada, chave junto aos dados, auditoria mutável, restore não testado, exclusão incompleta e dependência vulnerável.

**Validação:** threat review; testes de ACL/cripto/rotação em staging; backup/restore; mapa de exclusão; retenção dry-run; authz de arquivos; SAST/SCA/secrets/config; revisão manual. DAST somente com autorização explícita futura.

---

## Fase 18 — Otimização

Status: planejada

**Objetivo:** otimizar após medição, garantir degradação controlada, observabilidade e encerramento seguro.

**Requisitos:** PERF-004, PERF-005, PERF-006.

**Dependências:** Fase 17 concluída; hardware de referência, número de câmeras, resoluções, metas de FPS/latência e limites de recurso ainda precisam ser definidos.

**Entregáveis:**

- Baseline e profiling por etapa.
- Política adaptativa de FPS/resolução/frames ignorados com histerese.
- Métricas CPU/RAM/GPU/temperatura, filas, FPS e latência.
- Sequência idempotente de shutdown e recuperação de worker travado.
- Limites configuráveis por dispositivo e documentação de threading/processos/asyncio/workers/filas.

**Critérios de conclusão:**

- Otimizações têm comparação antes/depois e não degradam precisão além do aprovado.
- Memória/filas permanecem limitadas em carga sustentada.
- Shutdown preserva outbox ou explicita falha e não deixa câmeras/workers.
- Modo degradado é visível e recupera quando carga normaliza.

**Riscos:** otimização prematura, regressão de precisão, oscilação adaptativa, vazamento de memória e shutdown incompleto.

**Validação:** profiling; benchmarks CPU/GPU; carga crescente; soak; falha de alocação; worker travado; pouco recurso; shutdown repetido e regressão biométrica.

---

## Fase 19 — Testes completos

Status: planejada

**Objetivo:** executar a matriz integral de qualidade, segurança, precisão, integração, carga e recuperação antes de empacotar.

**Requisitos:** FACE-008, TEST-002 a TEST-007 e regressão de todos os requisitos anteriores.

**Dependências:** Fase 18 concluída; ambientes e dados autorizados disponíveis; metas de aceitação definidas. Ausência desses elementos mantém testes correspondentes pendentes.

**Entregáveis:**

- Suítes unitária, integração, API, banco, GUI, câmera simulada, offline, sincronização, segurança e E2E.
- Protocolo biométrico com FAR/FRR, falso positivo/negativo, vieses e limitações.
- Testes de múltiplas câmeras, reconexão, carga, soak, disco, backup/restore e encerramento.
- Relatório de evidências, cobertura, gaps, falhas e riscos residuais.

**Critérios de conclusão:**

- Todos os gates obrigatórios passam no ambiente declarado.
- Nenhum teste crítico está “presumido”; hardware não testado permanece gap explícito.
- Achado crítico bloqueia a fase; altos exigem correção ou aceite formal com prazo.
- Limiar facial e metas são aprovados por evidência, não por default de biblioteca.

**Riscos:** dataset não representativo, testes flakey, ambiente divergente, meta indefinida, viés e falsa confiança por cobertura nominal.

**Validação:** executar pipeline limpo; repetir suíte crítica; testes manuais documentados; revisão independente de authz/privacidade; relatório de precisão; carga/soak; restore; checklist de release.

---

## Fase 20 — Empacotamento e documentação

Status: planejada

**Objetivo:** entregar artefatos instaláveis, operação reproduzível e documentação completa de uso, segurança, manutenção e limitações.

**Requisitos:** PRIV-006 e fechamento documental/operacional de todos os requisitos anteriores.

**Dependências:** Fase 19 concluída sem erro crítico; plataformas de distribuição, estratégia de atualização/assinatura e suporte permanecem unspecified até decisão.

**Entregáveis:**

- Pacote/instalador para plataformas aprovadas, versão da aplicação e hashes/assinatura quando definida.
- README, documentação da API e arquitetura.
- Instalação Windows/Linux, primeiro administrador, primeira câmera e primeira pessoa.
- Operação local/distribuída, backup/restore, offline/sync, diagnósticos, manutenção e rollback.
- Guia de segurança/LGPD, retenção, consentimento, resposta a incidente e limites de vivacidade/reconhecimento.
- Release notes, SBOM/dependências, configurações de produção e checklist.

**Critérios de conclusão:**

- Instalação limpa e upgrade suportado são reproduzidos nas plataformas declaradas.
- Pacote não contém segredo, dado biométrico real, cache, log ou artefato de teste sensível.
- Documentação reproduz smoke test e procedimentos críticos.
- Limites de uso e funcionalidades fora de escopo estão explícitos.
- Estado GSD, requisitos, changelog, resumo e verificação final refletem evidência real.

**Riscos:** instalador inseguro, DLL/modelo ausente, atualização sem rollback, documentação divergente e configuração de produção permissiva.

**Validação:** instalar em ambiente limpo; verificar hashes/assinatura/SBOM; executar smoke/E2E essencial; testar upgrade/rollback; revisar pacote por segredos/dados; walkthrough operacional e checklist final.

## Marcos de entrega

| Marco | Fases | Resultado demonstrável | Estado |
|---|---|---|---|
| M0 — Baseline seguro | 1–3 | projeto reproduzível, banco/configuração e controle de acesso | pendente |
| M1 — V1 local de uma câmera | 4–8 | captura, cadastro, reconhecimento e histórico em webcam/simulação/arquivo | pendente |
| M2 — Evolução pós-v1 multicâmera | 9–11 | isolamento de múltiplas fontes, GUI e desconhecidos | pendente |
| M3 — Operação distribuída | 12–14 | API, dispositivos, cache, sincronização e offline | pendente |
| M4 — Controles avançados | 15–17 | vivacidade, alertas, privacidade, auditoria e hardening | pendente |
| M5 — Release verificável | 18–20 | desempenho medido, testes completos, pacote e documentação | pendente |

## Definição global de pronto

O sistema só pode ser chamado de pronto quando todos os requisitos críticos estiverem concluídos com evidência; não houver erro/finding crítico aberto; precisão, capacidade, retenção e base legal estiverem aprovadas; backup/restore, offline/sync, autorização e shutdown tiverem sido testados; o pacote limpo for reproduzível; e riscos residuais e limitações estiverem documentados. Até lá, o estado permanece planejado ou em desenvolvimento, nunca “funcionando” por presunção.
