# Requisitos do Sistema de Câmeras Inteligentes

Versão do baseline: 0.1
Data: 2026-07-17
Estado: planejamento inicial com fundação mínima em implementação; reconhecimento,
câmeras, banco, API e GUI continuam sem implementação ou validação real.

## Convenções

- Prioridades: crítica, alta, média e baixa.
- Status permitidos: pendente, em andamento, bloqueado e concluído.
- Requisitos parcialmente iniciados usam `em andamento`; nenhum requisito está concluído.
  Só podem ser concluídos com evidência registrada de implementação e teste.
- Testes de hardware real, GPU, rede, carga e precisão biométrica dependem de ambiente e dados autorizados; permanecem pendentes até execução documentada.
- Dependências entre requisitos indicam pré-condições lógicas, não autorização para antecipar fases do roadmap.

## Entradas normalizadas e lacunas

| Entrada | Valor |
|---|---|
| repo_url_ou_snapshot | workspace local fornecido e fundação Python avaliada; não há remoto configurado |
| stack_tecnologica | Python 3.11+; Supabase preferencial; SQLite offline; webcam integrada inicial; versões e escolhas biométricas finais unspecified |
| nivel_seguranca | unspecified; o domínio biométrico exige baseline conservador |
| alvos_compliance | LGPD explicitamente citada; demais alvos unspecified |
| entregaveis_desejados | sistema local evolutivo para cliente-servidor, GUI, API, reconhecimento, sincronização, testes e documentação |
| fontes_prioritarias | documentação oficial e padrões primários; lista final unspecified |
| ferramentas_prioritarias | OpenCV, alternativas de reconhecimento, ONNX Runtime, FastAPI, PostgreSQL/Supabase, SQLAlchemy, Alembic, PySide6 e Pytest; seleção final unspecified |
| escopo_funcional | descrito neste documento e no roadmap |
| restricoes_operacionais | uso autorizado, proteção biométrica, uma webcam real inicial, internet preferencial com modo offline e postura de licença comercial |
| ambiente_execucao | computador Windows atual com webcam integrada; Windows/Linux futuros, hardware, GPU e rede reais ainda unspecified |
| alvo_dast | unspecified |
| autorizacao_para_testes_ativos | unspecified; nenhum teste ativo está autorizado por este baseline |

Decisões confirmadas: uma webcam integrada na primeira versão; expansão futura para
múltiplas webcams e ESP32; Supabase como preferência ainda sujeita a prova de conceito;
internet como meio preferencial, sem remover operação offline; armazenamento de frames
solicitado; avaliação de licenças como produto comercial. Ainda estão `unspecified`:
quantidade futura e protocolos finais das câmeras; quantidade de pessoas; hardware/GPU;
SO de produção; período e granularidade de retenção; base legal/consentimento; região,
plano, custos e limites do Supabase; metas de latência/FPS/precisão; limiares; vivacidade;
locais de uso, responsáveis e canais externos de alerta.

## Câmeras

### CAM-001 — Abstração de fontes de vídeo

- Descrição: disponibilizar uma interface substituível, começando pela webcam integrada
  e fonte simulada e permitindo futuros adaptadores USB, IP/RTSP, arquivo e ESP32.
- Prioridade: crítica
- Fase: 4 — Captura de uma câmera
- Dependências: SEC-001
- Critérios de aceitação:
  - Cada tipo efetivamente implementado possui adaptador com abrir, ler, estado e liberar.
  - Fonte inválida retorna erro tipado sem encerrar a aplicação.
  - Caminhos e credenciais não ficam fixos no código.
- Testes: unitários por adaptador simulado; integração com arquivo; validação manual de cada hardware real disponível.
- Status: pendente

### CAM-002 — Cadastro e teste de conexão de câmera

- Descrição: manter identificador, nome, tipo, origem, credencial protegida, local, resolução, FPS, dispositivo responsável, reconexão, reconhecimento e política de imagens.
- Prioridade: alta
- Fase: 4 — Captura de uma câmera
- Dependências: CAM-001, DB-001, SEC-004
- Critérios de aceitação:
  - Adicionar, editar, ativar, desativar e remover logicamente uma câmera.
  - Exigir “Testar conexão” com resultado claro antes de salvar uma nova origem.
  - Validar tipo, resolução, FPS, timeout e intervalo de reconexão.
- Testes: validação de campos; conexão simulada com sucesso, timeout e credencial inválida; persistência.
- Status: pendente

### CAM-003 — Ciclo de captura e liberação de recursos

- Descrição: capturar frames continuamente sem bloquear GUI e liberar câmera, filas e workers em parada ou falha.
- Prioridade: crítica
- Fase: 4 — Captura de uma câmera
- Dependências: CAM-001, PERF-001
- Critérios de aceitação:
  - Iniciar, pausar, parar e reiniciar de forma idempotente.
  - Atualizar resolução, FPS real e instante do último frame.
  - Encerramento não deixa handle ou worker órfão.
- Testes: ciclo repetido start/stop; fonte ausente; fim de arquivo; teste manual de liberação do dispositivo.
- Status: pendente

### CAM-004 — Isolamento de falhas e reconexão

- Descrição: impedir que falha ou desconexão de uma câmera interrompa as demais e aplicar reconexão com espera configurável e limitada.
- Prioridade: crítica
- Fase: 9 — Suporte a várias câmeras
- Dependências: CAM-003, CAM-006, ALERT-001
- Critérios de aceitação:
  - Falha muda somente a câmera afetada para offline e registra causa.
  - Reconexão usa backoff/intervalo configurado, sem busy loop.
  - Reconexão restaura o fluxo e gera evento de estado.
- Testes: injeção de desconexão; recuperação; exaustão de tentativas; confirmação de continuidade das outras fontes.
- Status: pendente

### CAM-005 — Pipeline de vídeo desacoplado

- Descrição: separar captura, validação, detecção, rastreamento, alinhamento, embedding, comparação, vivacidade, exibição e registro.
- Prioridade: crítica
- Fase: 5 — Detecção facial
- Dependências: CAM-003, PERF-002
- Critérios de aceitação:
  - Etapas possuem contratos tipados e observáveis.
  - Filas têm capacidade finita e política explícita de descarte.
  - Um erro de frame é contido e não derruba o fluxo.
- Testes: contrato de cada etapa; fila cheia; frame corrompido; propagação controlada de cancelamento.
- Status: pendente

### CAM-006 — Execução simultânea de múltiplas câmeras

- Descrição: executar câmeras em unidades isoladas de concorrência, com limite de capacidade configurável.
- Prioridade: crítica
- Fase: 9 — Suporte a várias câmeras
- Dependências: CAM-003, CAM-005, PERF-003
- Critérios de aceitação:
  - Adicionar ou remover uma câmera não exige reiniciar as demais.
  - Estados, métricas e erros são individualizados por câmera.
  - Limite configurado impede iniciar carga acima da capacidade.
- Testes: duas ou mais fontes simuladas; inclusão/remoção em runtime; uma fonte lenta e uma com falha.
- Status: pendente

### CAM-007 — Descoberta, teste e simulação de câmeras

- Descrição: fornecer script para listar/testar câmeras e modo de simulação reproduzível para desenvolvimento automatizado.
- Prioridade: alta
- Fase: 4 — Captura de uma câmera
- Dependências: CAM-001
- Critérios de aceitação:
  - Script informa origem, abertura, resolução, FPS e erros sem expor credenciais.
  - Fonte simulada permite frames válidos, timeout, corrupção e desconexão programados.
  - Uso e limitações são documentados para Windows e Linux.
- Testes: execução automatizada da fonte simulada; smoke test do script; hardware real marcado como teste manual pendente.
- Status: pendente

### CAM-008 — Ingestão segura de frames de ESP32

- Descrição: receber JPEG/snapshots de câmeras ESP32 como nós de captura, mantendo
  detecção e reconhecimento no cliente de borda/servidor confiável no baseline.
- Prioridade: alta
- Fase: 12 — API central
- Dependências: CAM-001, SYNC-001, SEC-002
- Critérios de aceitação:
  - O ESP32 inicia comunicação autenticada de saída ou usa gateway local confiável;
    nenhum servidor MJPEG/HTTP do dispositivo é exposto diretamente à internet.
  - Payload, tipo, tamanho, resolução, frequência, timeout e dispositivo são validados.
  - Credencial elevada do Supabase nunca é instalada no ESP32; revogação e rotação são
    possíveis por dispositivo.
  - Falha de rede não bloqueia outras fontes e não cria fila de frames sem limite.
- Testes: dispositivo simulado, JPEG inválido/sobredimensionado, autenticação negada,
  replay, timeout, reconexão, rate limit e checklist manual em hardware autorizado.
- Status: pendente

## Reconhecimento facial

### FACE-001 — Detecção de todos os rostos

- Descrição: detectar todos os rostos elegíveis em cada frame processado e retornar caixas e pontos necessários.
- Prioridade: crítica
- Fase: 5 — Detecção facial
- Dependências: CAM-005
- Critérios de aceitação:
  - Múltiplos rostos no mesmo frame são retornados separadamente.
  - Rostos pequenos, parciais ou inválidos recebem decisão explícita.
  - Nenhum rosto não implica erro de pipeline.
- Testes: imagens autorizadas com zero, um e vários rostos; bordas; baixa resolução; entradas inválidas.
- Status: pendente

### FACE-002 — Alinhamento e qualidade pré-inferência

- Descrição: alinhar faces quando necessário e calcular qualidade mínima antes de gerar embeddings.
- Prioridade: alta
- Fase: 5 — Detecção facial
- Dependências: FACE-001
- Critérios de aceitação:
  - Transformação preserva proporção e metadados de origem.
  - Face fora dos limites, pequena ou sem landmarks suficientes é rejeitada com motivo.
  - Limites são configuráveis e validados.
- Testes: rotação, perfil moderado, face na borda, tamanhos mínimo/máximo e imagem corrompida.
- Status: pendente

### FACE-003 — Geração versionada de embeddings

- Descrição: gerar embeddings normalizados com identificação de modelo, versão e parâmetros.
- Prioridade: crítica
- Fase: 7 — Embeddings e reconhecimento
- Dependências: FACE-002, DB-004
- Critérios de aceitação:
  - Mesma entrada e versão produzem saída dimensional consistente.
  - Embedding inválido, NaN ou dimensão incorreta é rejeitado.
  - Metadados permitem reprocessamento e migração futura.
- Testes: determinismo dentro da tolerância; dimensão; normalização; entradas rejeitadas; compatibilidade CPU/GPU.
- Status: pendente

### FACE-004 — Correspondência com limiar seguro

- Descrição: comparar embeddings e reconhecer somente acima de limiar calibrado; caso contrário classificar como Desconhecido.
- Prioridade: crítica
- Fase: 7 — Embeddings e reconhecimento
- Dependências: FACE-003, REG-006
- Critérios de aceitação:
  - Melhor candidato abaixo do limiar nunca recebe identidade.
  - Resultado inclui identidade ou desconhecido, similaridade, limiar e versão do índice.
  - Limiar global e eventual política por contexto são validados; valor inicial permanece unspecified até calibração.
- Testes: pares positivos e negativos; borda do limiar; base vazia; identidades próximas; regressão contra falso positivo.
- Status: pendente

### FACE-005 — Rastreamento temporal e antirrepetição

- Descrição: rastrear faces por curto período, reduzir inferências redundantes e impedir eventos repetidos dentro de janela configurável.
- Prioridade: alta
- Fase: 7 — Embeddings e reconhecimento
- Dependências: FACE-001, FACE-004, DB-005
- Critérios de aceitação:
  - Cada trilha possui identificador e duração visível.
  - Reconhecimento pode ser reutilizado somente enquanto critérios temporais/visuais forem válidos.
  - Nova ocorrência após a janela gera novo evento; valor da janela é unspecified até configuração.
- Testes: sequência contínua, oclusão curta, reaparecimento, duas pessoas cruzando, expiração e mudança de identidade.
- Status: pendente

### FACE-006 — Execução em CPU e aceleração opcional

- Descrição: executar inferência em CPU e selecionar GPU apenas quando compatível e disponível, com fallback controlado.
- Prioridade: alta
- Fase: 7 — Embeddings e reconhecimento
- Dependências: FACE-003, SEC-008
- Critérios de aceitação:
  - Provider efetivo e versão são registrados.
  - Ausência ou falha de GPU não impede modo CPU.
  - Resultados entre providers respeitam tolerância definida em pesquisa.
- Testes: smoke em CPU; GPU quando hardware autorizado existir; provider indisponível; comparação numérica.
- Status: pendente

### FACE-007 — Verificação de vivacidade configurável

- Descrição: produzir estado aprovada, reprovada, inconclusiva ou desativada e reduzir ataques simples de foto, tela, vídeo ou impressão sem prometer segurança total.
- Prioridade: alta
- Fase: 15 — Vivacidade
- Dependências: FACE-001, FACE-005, PRIV-001
- Critérios de aceitação:
  - Método e limitações são documentados e configuráveis.
  - Reconhecimento/alerta aplica política explícita para cada estado.
  - Evidência da vivacidade não expõe imagem além da retenção autorizada.
- Testes: ataques autorizados com foto/tela/vídeo, pessoa real, baixa luz, estado inconclusivo e recurso desativado.
- Status: pendente

### FACE-008 — Calibração de precisão e robustez

- Descrição: medir falsos positivos/negativos e robustez a óculos, barba, cabelo, expressão, iluminação, perfil e distância em conjunto autorizado e representativo.
- Prioridade: crítica
- Fase: 19 — Testes completos
- Dependências: FACE-004, FACE-007, TEST-003
- Critérios de aceitação:
  - Métricas, amostra, vieses, limitações e limiar escolhido são registrados.
  - Metas de FAR/FRR e tamanho da amostra permanecem unspecified até decisão formal.
  - Resultado inseguro bloqueia liberação para uso real.
- Testes: protocolo offline reproduzível, estratificação autorizada, teste de regressão do limiar e revisão humana.
- Status: pendente

## Cadastro e pessoas

### REG-001 — Modelo e ciclo de vida da pessoa

- Descrição: manter nome, identificador/matrícula, categoria, observações, foto principal, datas, responsável e status ativo/inativo.
- Prioridade: crítica
- Fase: 6 — Cadastro de pessoas
- Dependências: DB-001, AUTH-002, PRIV-001
- Critérios de aceitação:
  - Identificador interno obedece unicidade definida.
  - Criar, consultar, editar, inativar e excluir respeitam autorização e auditoria.
  - Pessoa inativa não é reconhecida como ativa.
- Testes: CRUD, unicidade, transições de status, concorrência de edição e autorização por papel.
- Status: pendente

### REG-002 — Sessão guiada de captura

- Descrição: capturar quantidade configurável entre 10 e 100 fotos com instruções e progresso em tempo real.
- Prioridade: crítica
- Fase: 6 — Cadastro de pessoas
- Dependências: REG-001, CAM-003, UI-002
- Critérios de aceitação:
  - Quantidade fora de 10–100 é rejeitada.
  - Sessão pode ser cancelada sem deixar cadastro parcial inconsistente.
  - Progresso diferencia fotos aceitas e rejeitadas com motivo.
- Testes: limites 10/100, cancelamento, perda da câmera, retomada definida e progresso.
- Status: pendente

### REG-003 — Cobertura de pose, expressão e iluminação

- Descrição: orientar frente, direita, esquerda, cima, baixo, pequenas expressões e variações de iluminação.
- Prioridade: alta
- Fase: 6 — Cadastro de pessoas
- Dependências: REG-002, FACE-002
- Critérios de aceitação:
  - Plano de captura exige cobertura mínima configurada de poses.
  - Orientação só avança após uma imagem válida ou ação explícita autorizada.
  - Cobertura final é registrada junto ao cadastro.
- Testes: sequência completa, pose incorreta, repetição excessiva, iluminação inadequada e cancelamento.
- Status: pendente

### REG-004 — Portões de qualidade do cadastro

- Descrição: aceitar somente uma face nítida, iluminada, suficientemente grande e inteiramente enquadrada.
- Prioridade: crítica
- Fase: 6 — Cadastro de pessoas
- Dependências: REG-002, FACE-002
- Critérios de aceitação:
  - Zero ou mais de uma face é rejeitado.
  - Borrão, exposição extrema, tamanho insuficiente e corte parcial têm códigos de motivo.
  - Limiares são configuráveis, versionados e validados.
- Testes: casos positivos/negativos para cada portão; limites; imagens corrompidas; consistência de mensagens.
- Status: pendente

### REG-005 — Revisão das imagens do cadastro

- Descrição: permitir visualizar, refazer e excluir fotos específicas antes de confirmar.
- Prioridade: alta
- Fase: 6 — Cadastro de pessoas
- Dependências: REG-002, REG-004
- Critérios de aceitação:
  - Remoção reduz o progresso e impede confirmação abaixo do mínimo.
  - Refazer substitui de forma atômica a imagem selecionada.
  - Cancelar elimina temporários conforme política de privacidade.
- Testes: excluir, refazer, confirmar abaixo/acima do mínimo, cancelamento e falha de armazenamento.
- Status: pendente

### REG-006 — Representação facial e duplicidade

- Descrição: detectar possível cadastro duplicado e produzir embedding médio ou conjunto representativo, conforme decisão técnica ainda unspecified.
- Prioridade: crítica
- Fase: 6 — Cadastro de pessoas
- Dependências: REG-004, FACE-003, DB-004
- Critérios de aceitação:
  - Suspeita de duplicidade exige revisão autorizada, sem mesclar automaticamente.
  - Estratégia de agregação registra modelo, versão, imagens de origem e qualidade.
  - Persistência é atômica entre pessoa e representação válida.
- Testes: duplicata provável, homônimo não duplicado, embeddings inválidos, rollback e múltiplas representações.
- Status: pendente

### REG-007 — Atualização, importação e conversão de desconhecido

- Descrição: atualizar fotos, importar imagens quando autorizado e converter grupo desconhecido em pessoa preservando proveniência.
- Prioridade: alta
- Fase: 11 — Pessoas desconhecidas
- Dependências: REG-001, REG-006, DB-006, PRIV-005
- Critérios de aceitação:
  - Importação valida tipo, tamanho, conteúdo e autorização.
  - Atualização incrementa versão dos embeddings e dispara sincronização.
  - Conversão associa eventos selecionados sem perder auditoria.
- Testes: importação válida/maliciosa, atualização, rollback, conversão, autorização negada e reindexação.
- Status: pendente

## Autenticação e autorização

### AUTH-001 — Autenticação com senha protegida

- Descrição: autenticar usuários sem armazenar senha em texto puro, usando algoritmo de hash moderno escolhido por pesquisa.
- Prioridade: crítica
- Fase: 3 — Autenticação e usuários
- Dependências: DB-001, SEC-001
- Critérios de aceitação:
  - Hash inclui salt e parâmetros atualizáveis.
  - Comparação é feita por biblioteca adequada e senha nunca aparece em log.
  - Hash antigo pode ser reprocessado após login válido.
- Testes: login válido/inválido, hash único para mesma senha, rehash, entrada extrema e inspeção de logs.
- Status: pendente

### AUTH-002 — Papéis Administrador, Operador e Visualizador

- Descrição: implementar permissões mínimas descritas para os três papéis, com negação por padrão.
- Prioridade: crítica
- Fase: 3 — Autenticação e usuários
- Dependências: AUTH-001, DB-002
- Critérios de aceitação:
  - Administrador gerencia recursos privilegiados.
  - Operador executa apenas ações operacionais autorizadas.
  - Visualizador não modifica cadastros nem configurações.
- Testes: matriz positiva e negativa por ação/API/tela; tentativa de elevação de privilégio.
- Status: pendente

### AUTH-003 — Escopo por câmera e local

- Descrição: restringir visualização e operação às câmeras e locais autorizados para cada usuário.
- Prioridade: alta
- Fase: 3 — Autenticação e usuários
- Dependências: AUTH-002, CAM-002
- Critérios de aceitação:
  - Filtros são aplicados no servidor/repositório, não apenas na GUI.
  - Recurso fora do escopo retorna negação sem revelar metadados.
  - Alterações de escopo são auditadas e passam a valer conforme política definida.
- Testes: acesso cruzado, enumeração, exportação filtrada, cache/sessão após revogação.
- Status: pendente

### AUTH-004 — Sessões seguras

- Descrição: implementar criação, expiração, renovação controlada, revogação e logout com JWT ou sessão segura ainda unspecified.
- Prioridade: crítica
- Fase: 3 — Autenticação e usuários
- Dependências: AUTH-001, DB-001
- Critérios de aceitação:
  - Tokens/cookies têm expiração e atributos seguros adequados ao cliente.
  - Logout e desativação de usuário invalidam acesso conforme política.
  - Segredo/chave de assinatura não reside no repositório.
- Testes: expiração, replay/revogação, logout, assinatura inválida, usuário desativado e relógio limítrofe.
- Status: pendente

### AUTH-005 — Proteção contra força bruta

- Descrição: registrar tentativas, limitar frequência e bloquear temporariamente credenciais/origens conforme política configurada.
- Prioridade: alta
- Fase: 3 — Autenticação e usuários
- Dependências: AUTH-001, DB-001, ALERT-004
- Critérios de aceitação:
  - Limites e duração são configuráveis e não permitem bypass simples.
  - Resposta não facilita enumeração de usuários.
  - Bloqueio, desbloqueio e tentativas suspeitas são auditados.
- Testes: limite, janela, desbloqueio, concorrência, usuário inexistente, negação de serviço abusiva.
- Status: pendente

### AUTH-006 — Recuperação e bootstrap administrativo

- Descrição: oferecer recuperação controlada de senha e script seguro para criar o primeiro administrador.
- Prioridade: alta
- Fase: 3 — Autenticação e usuários
- Dependências: AUTH-001, AUTH-004, SEC-001
- Critérios de aceitação:
  - Token de recuperação é curto, expirável, uso único e não registrado em claro.
  - Bootstrap recusa senha insegura e não imprime segredo.
  - Ações invalidam sessões quando necessário e geram auditoria.
- Testes: expiração, reutilização, token inválido, criação duplicada, senha fraca e logs.
- Status: pendente

## Dados e persistência

### DB-001 — Esquema mínimo e configurações

- Descrição: modelar users, roles, permissions, user_permissions, people, face_images, face_embeddings, cameras, devices, detection_events, unknown_faces, unknown_face_groups, alerts, audit_logs, system_settings, synchronization_queue, sessions e login_attempts.
- Prioridade: crítica
- Fase: 2 — Configurações e banco
- Dependências: SEC-001, PRIV-001
- Critérios de aceitação:
  - Todas as entidades possuem chaves, datas e relacionamentos necessários.
  - Configuração do banco vem do ambiente e falha de forma segura.
  - Campos sensíveis e políticas de exclusão são identificados.
- Testes: criação em banco limpo, introspecção do esquema, configuração ausente/inválida e conexão.
- Status: pendente

### DB-002 — Integridade, índices e exclusão lógica

- Descrição: aplicar chaves estrangeiras, unicidade, checks, índices e exclusão lógica onde retenção/auditoria exigirem.
- Prioridade: crítica
- Fase: 2 — Configurações e banco
- Dependências: DB-001
- Critérios de aceitação:
  - Estado inválido é rejeitado pelo domínio ou banco.
  - Índices cobrem consultas previstas sem duplicação desnecessária.
  - Exclusão lógica não torna dados ativos novamente por consulta comum.
- Testes: violações de FK/unique/check, explain das consultas críticas e filtros de registros excluídos.
- Status: pendente

### DB-003 — Migrações e transações

- Descrição: versionar esquema com Alembic ou alternativa decidida, repositories tipados e transações atômicas.
- Prioridade: crítica
- Fase: 2 — Configurações e banco
- Dependências: DB-001, DB-002
- Critérios de aceitação:
  - Upgrade de banco vazio até head é reproduzível.
  - Rollback suportado é documentado e testado em backup.
  - Falha parcial não deixa pessoa, evento ou sincronização inconsistente.
- Testes: upgrade, downgrade seguro, migração idempotente, rollback transacional e concorrência.
- Status: pendente

### DB-004 — Armazenamento e índice de embeddings

- Descrição: abstrair persistência/busca de vetores e selecionar entre pgvector, FAISS local ou alternativa após pesquisa; JSON bruto não deve ser adotado sem justificativa.
- Prioridade: crítica
- Fase: 2 — Configurações e banco
- Dependências: DB-003, PRIV-002
- Critérios de aceitação:
  - Dimensão, dtype, normalização, modelo e versão são validados.
  - Índice pode ser reconstruído a partir da fonte de verdade.
  - Acesso e backup obedecem às proteções de biometria.
- Testes: round-trip, dimensão inválida, busca exata/aproximada, reconstrução, atualização e isolamento de acesso.
- Status: pendente

### DB-005 — Histórico de detecções consultável

- Descrição: persistir pessoa/temporário, categoria, data/hora, câmera, local, dispositivo, confiança, imagem opcional, situação, vivacidade, duração, tracking, origem e sincronização.
- Prioridade: alta
- Fase: 8 — Histórico de detecções
- Dependências: DB-003, FACE-004, PRIV-003
- Critérios de aceitação:
  - Evento possui identificador global/idempotente e timestamps consistentes.
  - Repetição é controlada antes da persistência.
  - Consultas filtram todos os campos solicitados com paginação.
- Testes: criação, deduplicação, timezone, filtros combinados, paginação, imagem ausente e autorização.
- Status: pendente

### DB-006 — Persistência e agrupamento de desconhecidos

- Descrição: armazenar recorte, frame opcional, metadados, confiança máxima, vivacidade, identificador temporário, grupo e classificação ignorado/suspeito/autorizado.
- Prioridade: alta
- Fase: 11 — Pessoas desconhecidas
- Dependências: DB-005, FACE-004, PRIV-003
- Critérios de aceitação:
  - Agrupamento registra método/versão e permite correção humana.
  - Intervalo configurável limita imagens repetidas.
  - Exclusão e conversão preservam auditoria mínima legalmente permitida.
  - Frame completo é opt-in e vinculado a evento; o padrão não presume vídeo contínuo.
  - Objetos ficam privados, com referência no banco e acesso temporário autorizado;
    retenção e exclusão reconciliam metadado e objeto.
- Testes: agrupamento/separação, repetição, classificação, exclusão, conversão e retenção.
- Status: pendente

### DB-007 — Backup, restauração e saúde do armazenamento

- Descrição: realizar backup protegido, restauração testável, limpeza controlada e verificação de espaço.
- Prioridade: alta
- Fase: 17 — Segurança e auditoria
- Dependências: DB-003, SEC-005, PRIV-003
- Critérios de aceitação:
  - Backup não inclui segredo em claro e possui integridade verificável.
  - Restauração em ambiente isolado recompõe esquema e dados autorizados.
  - Pouco espaço gera alerta antes de falha e limpeza nunca remove fora da política.
- Testes: backup/restore, arquivo corrompido, chave ausente, pouco espaço simulado e retenção.
- Status: pendente

## API, sincronização e offline

### SYNC-001 — API central segura e versionada

- Descrição: expor API FastAPI ou alternativa decidida para usuários, pessoas, câmeras, dispositivos, eventos, configurações, alertas e sincronização.
- Prioridade: crítica
- Fase: 12 — API central
- Dependências: AUTH-002, DB-003, SEC-002
- Critérios de aceitação:
  - Contratos são versionados, documentados e validados.
  - Autenticação/autorização é aplicada por operação.
  - Paginação, erros e idempotência seguem padrão consistente.
- Testes: contrato/OpenAPI, integração por recurso, entradas inválidas, autorização e compatibilidade de versão.
- Status: pendente

### SYNC-002 — Cache local autorizado

- Descrição: cada cliente baixa apenas cadastros/configurações autorizados e reconhece localmente sem consultar o servidor a cada frame.
- Prioridade: crítica
- Fase: 13 — Dispositivos e sincronização
- Dependências: SYNC-001, DEVICE-001, DB-004, PRIV-005
- Critérios de aceitação:
  - Cache possui versão, origem, validade e armazenamento protegido.
  - Revogação/alteração resulta em atualização ou invalidação definida.
  - Falha no servidor não bloqueia inferência com cache ainda válido.
- Testes: carga inicial, atualização incremental, revogação, cache corrompido/expirado e isolamento entre dispositivos.
- Status: pendente

### SYNC-003 — Fila local offline

- Descrição: persistir eventos e alterações permitidas em outbox local durável quando o servidor estiver indisponível.
- Prioridade: crítica
- Fase: 14 — Funcionamento offline
- Dependências: SYNC-001, SYNC-002
- Critérios de aceitação:
  - Reinício do cliente não perde itens pendentes.
  - Capacidade, backpressure e comportamento quando cheia são configurados.
  - Dados locais recebem a mesma proteção e retenção aplicável.
- Testes: perda de rede, reinício, fila cheia, corrupção recuperável e retorno de conexão.
- Status: pendente

### SYNC-004 — Sincronização idempotente e conflitos

- Descrição: reenviar itens com retry/backoff sem duplicar eventos e resolver conflitos por política versionada.
- Prioridade: crítica
- Fase: 13 — Dispositivos e sincronização
- Dependências: SYNC-001, SYNC-003
- Critérios de aceitação:
  - Mesmo identificador idempotente produz um único efeito.
  - Status pendente, enviado, confirmado e erro é rastreável.
  - Conflitos não são descartados silenciosamente; política final permanece unspecified.
- Testes: reenvio, timeout após commit, respostas fora de ordem, concorrência, conflito e poison message.
- Status: pendente

### SYNC-005 — Versionamento de cadastros e embeddings

- Descrição: propagar criação, atualização, inativação e exclusão de pessoas/embeddings por versão verificável.
- Prioridade: crítica
- Fase: 13 — Dispositivos e sincronização
- Dependências: REG-006, SYNC-002, SYNC-004
- Critérios de aceitação:
  - Cliente detecta lacuna de versão e solicita reconciliação.
  - Índice só troca para nova versão completa e válida.
  - Pessoa revogada deixa de ser reconhecida após regra temporal definida.
- Testes: delta, lacuna, atualização parcial, rollback de índice, revogação e múltiplos clientes.
- Status: pendente

### SYNC-006 — Observabilidade e recuperação da sincronização

- Descrição: expor saúde, atraso, tamanho da fila, último sucesso e erros, com recuperação operacional segura.
- Prioridade: alta
- Fase: 14 — Funcionamento offline
- Dependências: SYNC-003, SYNC-004, ALERT-001
- Critérios de aceitação:
  - Painel diferencia offline esperado, falha de autenticação e erro de dados.
  - Operação de reprocessar/quarentenar exige autorização e auditoria.
  - Diagnóstico não revela payload biométrico ou segredo.
- Testes: métricas, alertas por atraso, reprocessamento, quarentena e autorização.
- Status: pendente

## Interface

### UI-001 — Painel principal não bloqueante

- Descrição: mostrar câmeras em grade adaptativa, tela cheia, estados, FPS, resolução, último frame, recursos, contagens, últimas detecções e alertas.
- Prioridade: alta
- Fase: 10 — Interface principal
- Dependências: CAM-006, DB-005, PERF-001
- Critérios de aceitação:
  - Interface permanece responsiva durante captura e inferência.
  - Grade se ajusta à quantidade de câmeras e respeita autorização.
  - Iniciar, interromper e reiniciar câmera apresentam confirmação e estado real.
- Testes: interação com fontes simuladas, câmera lenta/offline, redimensionamento, autorização e teste manual de responsividade.
- Status: pendente

### UI-002 — Gestão e cadastro de pessoas

- Descrição: fornecer telas para listar, cadastrar, editar, inativar, excluir e atualizar fotos, com sessão guiada.
- Prioridade: crítica
- Fase: 6 — Cadastro de pessoas
- Dependências: REG-001, AUTH-002
- Critérios de aceitação:
  - Campos e erros são claros, sem perder dados válidos.
  - Progresso, instruções e revisão de fotos são acessíveis.
  - Ações destrutivas exigem confirmação e autorização.
- Testes: fluxos completos, validação, cancelamento, permissão negada e recuperação de erro.
- Status: pendente

### UI-003 — Gestão de câmeras

- Descrição: fornecer tela para adicionar, editar, testar, ativar, desativar, remover e reiniciar câmeras.
- Prioridade: alta
- Fase: 10 — Interface principal
- Dependências: CAM-002, AUTH-003
- Critérios de aceitação:
  - Credenciais existentes nunca são exibidas em claro.
  - “Testar conexão” não bloqueia a janela e informa diagnóstico seguro.
  - Estado exibido converge com o worker real.
- Testes: CRUD, teste assíncrono, timeout, credencial mascarada, autorização e concorrência.
- Status: pendente

### UI-004 — Histórico, filtros e exportação

- Descrição: consultar histórico por todos os filtros solicitados e exportar CSV, PDF e JSON quando autorizado.
- Prioridade: alta
- Fase: 8 — Histórico de detecções
- Dependências: DB-005, AUTH-003, PRIV-005
- Critérios de aceitação:
  - Filtros combinados, paginação e timezone são consistentes.
  - Exportação respeita o mesmo escopo e registra auditoria.
  - Arquivos usam escaping seguro e não incluem campos ocultos.
- Testes: cada filtro e combinações, grande paginação, CSV injection, PDF/JSON, autorização e auditoria.
- Status: pendente

### UI-005 — Revisão de pessoas desconhecidas

- Descrição: disponibilizar tela “Pessoas desconhecidas” para agrupar, corrigir, converter, excluir, ignorar ou classificar registros.
- Prioridade: alta
- Fase: 11 — Pessoas desconhecidas
- Dependências: DB-006, REG-007, AUTH-002
- Critérios de aceitação:
  - Operações em lote exibem alvo exato e consequência.
  - Imagens só são mostradas a usuário autorizado.
  - Correção humana preserva proveniência e auditoria.
- Testes: filtros, seleção em lote, conversão, exclusão, classificação, concorrência e autorização.
- Status: pendente

### UI-006 — Administração e preferências

- Descrição: fornecer telas de usuários, alertas, configurações, logs, auditoria, dispositivos e modos claro/escuro, com idioma configurável.
- Prioridade: média
- Fase: 10 — Interface principal
- Dependências: AUTH-002, DB-001, DEVICE-002
- Critérios de aceitação:
  - Cada tela respeita papel e escopo.
  - Configurações são validadas antes de aplicar e indicam necessidade de reinício.
  - Dados sensíveis são mascarados.
- Testes: matriz de permissão, valores inválidos, persistência de tema/idioma, mascaramento e atualização concorrente.
- Status: pendente

## Segurança

### SEC-001 — Configuração e gestão de segredos

- Descrição: usar variáveis de ambiente/secret manager, fornecer .env.example sem valores reais e falhar com segurança quando segredo obrigatório faltar.
- Prioridade: crítica
- Fase: 1 — Fundação e ambiente
- Dependências: nenhuma
- Critérios de aceitação:
  - Nenhuma senha, chave, token ou URL credenciada fica no código ou exemplo.
  - Configuração possui tipos, defaults seguros e validação.
  - Logs mascaram valores sensíveis.
- Testes: secret scan, configuração ausente/inválida, inspeção de logs e arquivo de exemplo.
- Status: em andamento

### SEC-002 — Transporte e API protegidos

- Descrição: exigir HTTPS/TLS em implantação não local e autenticação/autorização em endpoints sensíveis.
- Prioridade: crítica
- Fase: 12 — API central
- Dependências: AUTH-004, SEC-001
- Critérios de aceitação:
  - HTTP inseguro é recusado ou redirecionado conforme perfil documentado.
  - Certificados e confiança do cliente têm procedimento de rotação.
  - CORS, hosts e documentação pública usam defaults restritivos.
- Testes: TLS, certificado inválido, endpoint sem token, CORS/host e configuração de desenvolvimento versus produção.
- Status: pendente

### SEC-003 — Validação de entrada e consultas seguras

- Descrição: validar entradas de GUI/API/configuração e usar SQLAlchemy parametrizado para impedir injection e estados inválidos.
- Prioridade: crítica
- Fase: 2 — Configurações e banco
- Dependências: DB-001
- Critérios de aceitação:
  - Modelos impõem tamanho, formato, enum e limites.
  - Nenhuma entrada não confiável é concatenada em SQL/comando.
  - Mensagens externas não revelam stack ou estrutura interna.
- Testes: payloads limites e malformados, SQL injection, mass assignment e fuzzing passivo/unitário.
- Status: pendente

### SEC-004 — Upload e caminhos seguros

- Descrição: proteger fotos, vídeos, exports e arquivos de backup contra conteúdo malicioso, path traversal e abuso de tamanho.
- Prioridade: crítica
- Fase: 6 — Cadastro de pessoas
- Dependências: SEC-003, PRIV-003
- Critérios de aceitação:
  - Nome fornecido pelo usuário não determina caminho final.
  - Tipo real, extensão, dimensões e tamanho são validados.
  - Arquivos ficam fora de diretório executável/público e permissões são mínimas.
- Testes: ../, caminho absoluto, dupla extensão, arquivo não imagem, decompression bomb, oversized e symlink quando aplicável.
- Status: pendente

### SEC-005 — Proteção de dados em repouso

- Descrição: proteger credenciais de câmera, biometria, imagens, cache, fila offline e backups por criptografia/ACL adequadas ao ambiente.
- Prioridade: crítica
- Fase: 17 — Segurança e auditoria
- Dependências: SEC-001, DB-004, PRIV-002
- Critérios de aceitação:
  - Chaves são separadas dos dados e possuem plano de rotação.
  - Acesso a arquivos e tabelas segue menor privilégio.
  - Cópias temporárias são protegidas e removidas conforme política.
- Testes: permissões, chave ausente/incorreta, rotação em staging, acesso indevido e backup.
- Status: pendente

### SEC-006 — Auditoria de ações privilegiadas

- Descrição: registrar login, cadastro, edição, exclusão, exportação, mudança de permissão/configuração, ações em desconhecidos e diagnóstico remoto.
- Prioridade: crítica
- Fase: 17 — Segurança e auditoria
- Dependências: AUTH-002, DB-001, PRIV-005
- Critérios de aceitação:
  - Registro contém ator, ação, alvo, instante, origem e resultado sem segredo.
  - Usuário comum não altera/apaga auditoria.
  - Relógio, retenção e integridade têm política definida.
- Testes: cobertura de eventos, falha da auditoria, acesso negado, integridade e mascaramento.
- Status: pendente

### SEC-007 — Tratamento de exceções e logs seguros

- Descrição: tratar exceções globalmente, usar logs estruturados por nível e ocultar segredos, tokens, embeddings e dados pessoais desnecessários.
- Prioridade: alta
- Fase: 1 — Fundação e ambiente
- Dependências: SEC-001
- Critérios de aceitação:
  - Não existem except vazios nem falhas silenciosas.
  - IDs de correlação ligam erro, câmera, dispositivo e operação.
  - Encerramento controlado ocorre em erro fatal.
- Testes: exceções injetadas por camada, redaction, rotação de log, correlação e falha do destino de log.
- Status: em andamento — baseline da CLI coberto por logs JSON, redaction, correlação,
  rotação e fronteira fatal; integração com as camadas futuras permanece pendente

### SEC-008 — Supply chain e gates de segurança

- Descrição: fixar dependências compatíveis e mantidas, verificar vulnerabilidades/segredos/SAST e bloquear releases por achados críticos não tratados.
- Prioridade: alta
- Fase: 17 — Segurança e auditoria
- Dependências: TEST-001
- Critérios de aceitação:
  - Dependências e modelos têm origem, licença, hash/versão e justificativa.
  - Suppression exige justificativa, prazo e revisão.
  - Scans ativos permanecem proibidos sem autorização e alvo explícitos.
- Testes: pipeline com finding sintético, secret sintético, dependência vulnerável controlada e verificação de artefatos.
- Status: pendente

## Privacidade

### PRIV-001 — Finalidade, base legal e consentimento

- Descrição: documentar finalidade autorizada, público, locais, controlador/operador, base legal e consentimento quando aplicável antes de usar biometria real.
- Prioridade: crítica
- Fase: 1 — Fundação e ambiente
- Dependências: nenhuma
- Critérios de aceitação:
  - Uso real fica bloqueado enquanto base legal, aviso e responsáveis estiverem unspecified.
  - Cadastro registra versão do aviso/consentimento quando aplicável.
  - Mudança de finalidade exige revisão e não reutiliza dados automaticamente.
- Testes: validação de pré-condição, registro/revogação aplicável e auditoria.
- Status: pendente

### PRIV-002 — Minimização de biometria e imagens

- Descrição: coletar somente o necessário, permitir política de armazenar apenas embeddings e separar imagem original, recorte e frame completo.
- Prioridade: crítica
- Fase: 2 — Configurações e banco
- Dependências: PRIV-001
- Critérios de aceitação:
  - Armazenamento de frame completo é opt-in explícito e configurável.
  - Cada tipo de dado possui finalidade e necessidade documentadas.
  - Desativar armazenamento impede novas gravações e trata temporários.
- Testes: modos embedding-only/recorte/frame, defaults, temporários e mudança de configuração.
- Status: pendente

### PRIV-003 — Retenção e limpeza

- Descrição: aplicar prazos configuráveis por imagens, desconhecidos, eventos, logs, auditoria e backups.
- Prioridade: crítica
- Fase: 17 — Segurança e auditoria
- Dependências: PRIV-001, DB-001
- Critérios de aceitação:
  - Prazos permanecem unspecified até decisão formal e não há exclusão automática antes disso.
  - Job de limpeza é auditável, idempotente e limitado ao diretório/tabela esperados.
  - Hold legal ou obrigação aplicável tem fluxo explícito.
- Testes: relógio controlado, dry-run, limites de diretório, idempotência, hold e falha parcial.
- Status: pendente

### PRIV-004 — Exclusão completa e direitos da pessoa

- Descrição: localizar, exportar quando cabível e excluir/inativar pessoa, imagens, embeddings, índices, caches e réplicas conforme política legal.
- Prioridade: crítica
- Fase: 17 — Segurança e auditoria
- Dependências: REG-001, SYNC-005, PRIV-003
- Critérios de aceitação:
  - Operação exige autorização, confirmação e identificador de solicitação.
  - Propagação a clientes é verificável e não deixa reconhecimento ativo.
  - Exceções legais são documentadas sem reter além do necessário.
- Testes: mapa de dados, exclusão distribuída, cache offline, backup conforme política, exportação e auditoria.
- Status: pendente

### PRIV-005 — Acesso controlado a imagens e exportações

- Descrição: restringir visualização, download e exportação de frames, faces, eventos e biometria por função, câmera/local e finalidade.
- Prioridade: crítica
- Fase: 17 — Segurança e auditoria
- Dependências: AUTH-003, SEC-006
- Critérios de aceitação:
  - URLs/arquivos não são acessíveis diretamente sem autorização.
  - Exportações têm escopo, validade, marcação e auditoria adequados.
  - Pré-visualizações não vazam conteúdo em logs/cache indevido.
- Testes: acesso direto, enumeração, link expirado, exportação cruzada, cache e auditoria.
- Status: pendente

### PRIV-006 — Limites explícitos de uso

- Descrição: proibir busca em redes sociais, rastreamento externo, identificação secreta, coleta fora da finalidade, bases ilegais e compartilhamento automático com terceiros.
- Prioridade: crítica
- Fase: 20 — Empacotamento e documentação
- Dependências: PRIV-001
- Critérios de aceitação:
  - Documentação e configuração não oferecem esses fluxos.
  - Integração externa exige nova análise, base legal, threat model e decisão.
  - Avisos de uso responsável e LGPD acompanham instalação e operação.
- Testes: revisão de produto/API/docs e checklist de release.
- Status: pendente

## Desempenho e operação

### PERF-001 — Estratégia de concorrência não bloqueante

- Descrição: definir e implementar uso justificado de thread, processo, asyncio, worker e fila para captura, inferência, GUI, API, banco e sincronização.
- Prioridade: crítica
- Fase: 4 — Captura de uma câmera
- Dependências: TEST-001
- Critérios de aceitação:
  - GUI roda em thread apropriada e trabalho pesado não bloqueia event loop.
  - Falha/cancelamento se propaga de forma controlada.
  - Decisão registra custos de GIL, IPC, memória e portabilidade.
- Testes: responsividade, cancelamento, deadlock timeout, falha de worker e shutdown.
- Status: pendente

### PERF-002 — Filas limitadas e frame mais recente

- Descrição: limitar buffers, descartar frames antigos quando necessário e priorizar o frame mais recente.
- Prioridade: crítica
- Fase: 5 — Detecção facial
- Dependências: PERF-001
- Critérios de aceitação:
  - Capacidade e política de descarte são observáveis.
  - Carga sustentada mantém memória limitada.
  - Descarte não corrompe tracking nem evento sem sinalização.
- Testes: produtor mais rápido, fila cheia, memória prolongada e consistência de tracking.
- Status: pendente

### PERF-003 — Modelo compartilhado e limites de recursos

- Descrição: evitar cópias desnecessárias do modelo e limitar câmeras, CPU, RAM e GPU por dispositivo.
- Prioridade: alta
- Fase: 9 — Suporte a várias câmeras
- Dependências: FACE-003, DEVICE-002
- Critérios de aceitação:
  - Quantidade de sessões/modelos carregados é mensurável.
  - Configuração acima da capacidade é rejeitada ou degradada de forma explícita.
  - Isolamento escolhido não causa compartilhamento inseguro entre processos.
- Testes: contagem de modelos, múltiplas câmeras, limite excedido, falha de alocação e vazamento.
- Status: pendente

### PERF-004 — Degradação adaptativa

- Descrição: reduzir FPS/resolução ou frames processados em hardware lento conforme configuração, mantendo captura e registro coerentes.
- Prioridade: alta
- Fase: 18 — Otimização
- Dependências: PERF-002, PERF-003
- Critérios de aceitação:
  - Gatilhos usam métricas e têm histerese para evitar oscilação.
  - Qualidade mínima e impacto em precisão são documentados.
  - Operador visualiza modo degradado.
- Testes: carga crescente/decrescente, estabilidade, limites, recuperação e impacto na precisão.
- Status: pendente

### PERF-005 — Encerramento seguro

- Descrição: finalizar câmeras, filas, workers, transações, cache e GUI sem perda silenciosa ou recursos órfãos.
- Prioridade: crítica
- Fase: 18 — Otimização
- Dependências: CAM-003, SYNC-003
- Critérios de aceitação:
  - Sinais normais e fechamento da GUI iniciam sequência com timeout.
  - Eventos pendentes permanecem duráveis ou têm falha explícita.
  - Segunda chamada de shutdown é segura.
- Testes: SIGTERM/fechamento suportado, worker travado, banco indisponível, fila pendente e repetição.
- Status: pendente

### PERF-006 — Metas e benchmark de capacidade

- Descrição: medir FPS de captura/reconhecimento, latência, CPU, RAM, GPU, temperatura e escala por câmera/dispositivo.
- Prioridade: alta
- Fase: 18 — Otimização
- Dependências: PERF-003, TEST-007
- Critérios de aceitação:
  - Metas e hardware de referência permanecem unspecified até decisão.
  - Benchmark é reproduzível e separa CPU/GPU, número de câmeras e resolução.
  - Regressão acima da tolerância definida bloqueia release.
- Testes: benchmark controlado, soak test, múltiplas fontes e comparação com baseline.
- Status: pendente

## Testes e qualidade

### TEST-001 — Ambiente, padrões e automação de qualidade

- Descrição: configurar projeto Python modular com type hints, docstrings, Pytest, lint, formatação e type-check escolhidos.
- Prioridade: crítica
- Fase: 1 — Fundação e ambiente
- Dependências: nenhuma
- Critérios de aceitação:
  - Build/import, lint, format-check, type-check e testes têm comandos documentados.
  - Código evita arquivos monolíticos, caminhos absolutos, credenciais e except vazios.
  - Versões compatíveis são fixadas após pesquisa.
- Testes: execução dos comandos nativos, import smoke e verificação de configuração.
- Status: em andamento

### TEST-002 — Câmeras simuladas e integração de captura

- Descrição: testar captura, reconexão, múltiplas câmeras e falhas sem depender de hardware.
- Prioridade: crítica
- Fase: 19 — Testes completos
- Dependências: CAM-007, CAM-006
- Critérios de aceitação:
  - Cenários são determinísticos e executáveis em CI.
  - Cobrem frame válido, lento, corrompido, desconexão e recuperação.
  - Hardware real possui checklist separado, nunca alegado como automatizado.
- Testes: suíte cameras, soak simulado e checklist manual por dispositivo.
- Status: pendente

### TEST-003 — Testes biométricos positivos e negativos

- Descrição: validar detecção, embeddings, reconhecimento, desconhecidos e vivacidade com dados autorizados.
- Prioridade: crítica
- Fase: 19 — Testes completos
- Dependências: FACE-004, FACE-007, PRIV-001
- Critérios de aceitação:
  - Casos positivos e negativos incluem limiar e falsos positivos.
  - Dados de teste têm proveniência/autorização e descarte definido.
  - Falha de meta impede promoção.
- Testes: suíte offline versionada, regressão de modelo/limiar e relatório de métricas.
- Status: pendente

### TEST-004 — Integração de banco, API, autenticação e segurança

- Descrição: validar migrações, transações, contratos, RBAC, sessões e entradas hostis em ambiente isolado.
- Prioridade: crítica
- Fase: 19 — Testes completos
- Dependências: SYNC-001, AUTH-006, SEC-004
- Critérios de aceitação:
  - Banco temporário inicia do zero e é descartável.
  - Matriz de autorização cobre endpoints e operações sensíveis.
  - Testes não dependem de segredo/serviço de produção.
- Testes: integração, contract, authz negative, uploads, injection, migração e rollback.
- Status: pendente

### TEST-005 — Offline e sincronização distribuída

- Descrição: validar interrupções, retry, idempotência, conflitos, versões e múltiplos clientes.
- Prioridade: crítica
- Fase: 19 — Testes completos
- Dependências: SYNC-006
- Critérios de aceitação:
  - Nenhum evento confirmado é duplicado.
  - Reinício/rede intermitente não perde outbox.
  - Conflito e item inválido ficam visíveis e recuperáveis.
- Testes: chaos controlado local, timeout após commit, ordem trocada, reconciliação e fila cheia.
- Status: pendente

### TEST-006 — Interface e fluxos ponta a ponta

- Descrição: testar fluxos de login, câmera, cadastro, reconhecimento, histórico, desconhecidos, alertas, configurações e permissões.
- Prioridade: alta
- Fase: 19 — Testes completos
- Dependências: UI-006, ALERT-003
- Critérios de aceitação:
  - Caminhos críticos possuem automação quando viável e roteiro manual restante.
  - Erros não travam nem deixam estado incorreto.
  - Temas, resoluções e permissões essenciais são cobertos.
- Testes: testes Qt, E2E com fontes simuladas, acessibilidade básica e roteiro manual.
- Status: pendente

### TEST-007 — Carga, estabilidade e encerramento

- Descrição: medir uso prolongado, filas, vazamentos, reconexões, disco, recursos e desligamento.
- Prioridade: alta
- Fase: 19 — Testes completos
- Dependências: PERF-005, DB-007
- Critérios de aceitação:
  - Duração, carga e tolerâncias permanecem unspecified até metas de capacidade.
  - Evidência inclui séries de métricas e ambiente.
  - Erro crítico, vazamento crescente ou corrupção bloqueia release.
- Testes: load, soak, reconexões repetidas, pouco disco, worker travado e shutdown.
- Status: pendente

## Alertas

### ALERT-001 — Regras de alerta operacional e facial

- Descrição: gerar alertas para pessoa específica/bloqueada/desconhecida, lotação, câmera, servidor, banco, sincronização, recursos, armazenamento, fraude e reconhecimento repetidamente falho.
- Prioridade: alta
- Fase: 16 — Alertas
- Dependências: DB-005, FACE-007, DEVICE-002
- Critérios de aceitação:
  - Regras têm habilitação, severidade, escopo, limiar e janela.
  - Payload não inclui biometria/imagem além do autorizado.
  - Estado e origem do alerta são rastreáveis.
- Testes: uma regra por categoria, limites, regra desativada, escopo e conteúdo sensível.
- Status: pendente

### ALERT-002 — Canais de entrega seguros

- Descrição: exibir em interface/log/notificação local e permitir e-mail/webhook somente por configuração explícita.
- Prioridade: alta
- Fase: 16 — Alertas
- Dependências: ALERT-001, SEC-001
- Critérios de aceitação:
  - Integrações externas ficam desativadas por padrão.
  - Segredos de canal são protegidos e destinos validados.
  - Falha de entrega não bloqueia reconhecimento.
- Testes: defaults, entrega local, destino inválido, timeout, segredo mascarado e canal desativado.
- Status: pendente

### ALERT-003 — Deduplicação, retry e ciclo de vida

- Descrição: agrupar alertas repetidos, registrar tentativa/entrega/falha/reconhecimento e aplicar retry limitado.
- Prioridade: média
- Fase: 16 — Alertas
- Dependências: ALERT-001, ALERT-002
- Critérios de aceitação:
  - Janela evita tempestade sem ocultar agravamento.
  - Retry usa backoff e quarentena após limite.
  - Reconhecimento/resolução exige usuário autorizado quando aplicável.
- Testes: tempestade, agravamento, retry, poison message, resolução e auditoria.
- Status: pendente

### ALERT-004 — Alertas de autenticação suspeita

- Descrição: alertar login suspeito, muitas tentativas, bloqueio e recuperação anômala sem expor senha ou token.
- Prioridade: alta
- Fase: 16 — Alertas
- Dependências: AUTH-005, ALERT-002
- Critérios de aceitação:
  - Limiares e destinatários são configuráveis.
  - Evento correlaciona conta/origem de forma minimizada.
  - Alerta não permite enumeração adicional.
- Testes: rajada, distribuição lenta, usuário inexistente, desbloqueio e conteúdo do alerta.
- Status: pendente

## Dispositivos

### DEVICE-001 — Registro confiável de cliente

- Descrição: registrar cada computador cliente com identificador único, credencial própria, estado de aprovação e revogação.
- Prioridade: crítica
- Fase: 13 — Dispositivos e sincronização
- Dependências: SYNC-001, SEC-002
- Critérios de aceitação:
  - Dispositivo não aprovado não baixa cadastros nem envia eventos.
  - Credencial é rotacionável e revogável sem afetar outros clientes.
  - Clonagem de identificador não concede acesso.
- Testes: enrollment, aprovação, revogação, rotação, duplicata e acesso negado.
- Status: pendente

### DEVICE-002 — Inventário, heartbeat e painel

- Descrição: manter nome, versão do aplicativo, SO, recursos, última conexão, saúde, métricas, capacidade e estado online/offline.
- Prioridade: alta
- Fase: 13 — Dispositivos e sincronização
- Dependências: DEVICE-001
- Critérios de aceitação:
  - Heartbeat tem timeout configurável e não contém segredo.
  - Versão incompatível é sinalizada.
  - Painel diferencia ausência, degradação e manutenção.
- Testes: heartbeat, timeout, relógio, versão incompatível, dados inválidos e painel.
- Status: pendente

### DEVICE-003 — Atribuição de câmeras e configuração

- Descrição: associar câmeras ao computador responsável e distribuir apenas configuração autorizada e versionada.
- Prioridade: alta
- Fase: 13 — Dispositivos e sincronização
- Dependências: DEVICE-001, CAM-002, SYNC-005
- Critérios de aceitação:
  - Uma atribuição conflitante é rejeitada ou resolvida explicitamente.
  - Credenciais de câmera são entregues de modo protegido.
  - Cliente valida configuração antes de ativar.
- Testes: atribuição, transferência, conflito, dispositivo revogado, segredo e rollback.
- Status: pendente

### DEVICE-004 — Diagnóstico remoto autorizado

- Descrição: oferecer diagnóstico de câmera, rede, banco/cache e recursos, além de modo de manutenção, com ações remotas estritamente autorizadas.
- Prioridade: média
- Fase: 13 — Dispositivos e sincronização
- Dependências: DEVICE-002, AUTH-003, SEC-006
- Critérios de aceitação:
  - Diagnóstico read-only é separado de reinício/alteração.
  - Toda ação remota tem ator, alvo, resultado e timeout auditados.
  - Saída mascara endereços/segredos conforme necessidade.
- Testes: autorização, timeout, cliente offline, ação concorrente, mascaramento e auditoria.
- Status: pendente

## Rastreabilidade resumida

| Fase | Requisitos principais |
|---|---|
| 1 | SEC-001, SEC-007, PRIV-001, TEST-001 |
| 2 | DB-001 a DB-004, SEC-003, PRIV-002 |
| 3 | AUTH-001 a AUTH-006 |
| 4 | CAM-001 a CAM-003, CAM-007, PERF-001 |
| 5 | CAM-005, FACE-001, FACE-002, PERF-002 |
| 6 | REG-001 a REG-006, UI-002, SEC-004 |
| 7 | FACE-003 a FACE-006 |
| 8 | DB-005, UI-004 |
| 9 | CAM-004, CAM-006, PERF-003 |
| 10 | UI-001, UI-003, UI-006 |
| 11 | DB-006, REG-007, UI-005 |
| 12 | SYNC-001, SEC-002 |
| 13 | SYNC-002, SYNC-004, SYNC-005, DEVICE-001 a DEVICE-004 |
| 14 | SYNC-003, SYNC-006 |
| 15 | FACE-007 |
| 16 | ALERT-001 a ALERT-004 |
| 17 | DB-007, SEC-005, SEC-006, SEC-008, PRIV-003 a PRIV-005 |
| 18 | PERF-004 a PERF-006 |
| 19 | FACE-008, TEST-002 a TEST-007 |
| 20 | PRIV-006 e critérios documentais/de release dos requisitos anteriores |
