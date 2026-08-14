# Requisitos — Smart Environment

Baseline: 1.0
Atualizado em: 2026-08-11
Classificação do projeto: alto risco por envolver câmeras e contexto de trabalho

## Convenções

- `crítico`: sem o requisito, a etapa não avança.
- `alto`: necessário para a vertical ou para reduzir risco relevante.
- `médio`: importante, mas pode entrar após o MVP.
- `unspecified`: decisão ainda não tomada; não autoriza uma escolha implícita.
- “Sem identificação” descreve a intenção técnica. Um evento agregado ainda pode ser
  dado pessoal se local, horário ou baixa cardinalidade permitirem reidentificação.

Os antigos IDs `FACE-*`, `REG-*` e demais requisitos do baseline facial estão
aposentados e não serão reutilizados. O histórico permanece no Git.

## Governança e escopo

### GOV-001 — Finalidade operacional e atividade sem decisão automática

- **Descrição:** limitar o MVP a ocupação, sustentabilidade, recursos, patrimônio e
  estimativa de atividade observável, sem medir intenção ou produtividade real.
- **Fase:** SE-01 | **Prioridade:** crítico | **Dependências:** nenhuma.
- **Aceite:** documentos ativos excluem reconhecimento facial, emoção, intenção,
  produtividade real, ranking, controle de ponto e decisão disciplinar automatizada;
  estados de atividade são estimativas configuráveis e incluem `inconclusivo`.
- **Status:** concluído no rebaseline documental; implementação ainda inexistente.

### GOV-002 — Matriz de finalidades e dados

- **Descrição:** registrar separadamente finalidade, dado necessário, usuário, benefício,
  responsável e reutilizações proibidas para ocupação, energia e patrimônio.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** GOV-001.
- **Aceite:** cada tabela/evento e consulta remete a uma finalidade aprovada; usos
  incompatíveis são negados e a revisão tem responsável e data.
- **Status:** pendente.

### GOV-003 — Papéis de governança

- **Descrição:** identificar controlador, operadores de tratamento, encarregado/canal, dono do
  produto, segurança e aprovadores do piloto.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** GOV-002.
- **Aceite:** papéis e contatos válidos existem antes de qualquer dado real.
- **Status:** pendente; organizações e responsáveis estão `unspecified`.

### GOV-004 — Gate de mudança de finalidade

- **Descrição:** impedir que dados de ocupação sejam reaproveitados automaticamente
  para biometria, controle de ponto, comportamento ou sanção.
- **Fase:** transversal | **Prioridade:** crítico | **Dependências:** GOV-002.
- **Aceite:** nova finalidade exige novo projeto de requisitos, necessidade e
  proporcionalidade, avaliação jurídica/RIPD quando aplicável e aprovação explícita.
- **Status:** regra aceita; mecanismo de governança pendente.

### GOV-005 — Prontidão comercial e TCC

- **Descrição:** separar claramente protótipo acadêmico de produto pronto para produção.
- **Fase:** SE-12 | **Prioridade:** alto | **Dependências:** todas as fases aplicáveis.
- **Aceite:** licenças, riscos residuais, limites, runbooks, termos e evidência de gates
  são apresentados sem alegações não demonstradas.
- **Status:** pendente.

## Ambientes, câmera e captura

### CAM-001 — Fonte real e fonte simulada

- **Descrição:** definir `CameraSource` substituível para uma webcam e para testes.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** PRIV-004.
- **Aceite:** ambas entregam o mesmo contrato; testes não dependem de hardware real.
- **Status:** implementado; fonte real e doubles simulados usam o mesmo contrato.

### CAM-002 — Lifecycle e liberação segura

- **Descrição:** abrir, ler, interromper, reiniciar e liberar a câmera sem handle órfão.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** CAM-001.
- **Aceite:** ciclos repetidos, timeout, erro e cancelamento são testados; falha não
  encerra o processo nem trava o dispositivo.
- **Status:** em andamento; abertura, erro, cancelamento/exceção e liberação foram
  cobertos, mas timeout e ciclos repetidos ainda serão ampliados.

### CAM-003 — Frames transitórios

- **Descrição:** manter frames somente em buffers de memória limitados no baseline.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** CAM-001, PRIV-001.
- **Aceite:** nenhum frame/recorte entra em banco, rede, arquivo, log, cache ou crash
  dump do aplicativo; buffer é descartado após uso.
- **Status:** implementado no caminho atual de um frame por vez; nenhuma API de
  arquivo/rede foi adicionada. Crash dump e inspeção sistêmica permanecem fora desta prova.

### CAM-004 — Saúde e estado desconhecido

- **Descrição:** distinguir ambiente vazio de câmera/modelo indisponível.
- **Fase:** SE-02 | **Prioridade:** alto | **Dependências:** CAM-002.
- **Aceite:** health, último sucesso e erro tipado são expostos; falha gera `unknown`,
  nunca `empty` por presunção.
- **Status:** em andamento; erros são tipados e não viram contagem vazia, mas health e
  último sucesso ainda não são expostos.

## Ocupação sem identificação

### OCC-001 — Detecção de pessoas 0/1/N

- **Descrição:** detectar pessoas presentes sem classificar identidade.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** CAM-003.
- **Aceite:** conjunto sintético/autorizado mede 0, 1 e N pessoas, oclusão, iluminação,
  falsos positivos e falsos negativos; modelo/pesos/licenças são registrados.
- **Status:** em andamento; NanoDet/OpenCV DNN passa 0/1/N com doubles e detectou
  presença no smoke real, mas dataset autorizado, falsos sinais e métricas
  representativas continuam pendentes.

### OCC-002 — Agregação temporal e espacial

- **Descrição:** produzir estado/contagem por ambiente e janela, não por indivíduo.
- **Fase:** SE-04 | **Prioridade:** crítico | **Dependências:** OCC-001, PRIV-003.
- **Aceite:** evento possui somente campos permitidos, janela finita e granularidade
  configurada; tracking efêmero não persiste além da janela necessária.
- **Status:** pendente.

### OCC-003 — Incerteza e qualidade

- **Descrição:** representar confiança e resultado inconclusivo sem inventar precisão.
- **Fase:** SE-04 | **Prioridade:** crítico | **Dependências:** OCC-001.
- **Aceite:** entrada inválida, modelo indisponível e baixa confiança resultam em
  `unknown`; métricas e limitações aparecem no relatório de validação.
- **Status:** pendente.

### OCC-004 — Limites da inferência individual

- **Descrição:** permitir somente estado de atividade observável e impedir emoção,
  intenção, produtividade real, jornada, nome, matrícula ou trajetória persistente.
- **Fase:** transversal | **Prioridade:** crítico | **Dependências:** GOV-001.
- **Aceite:** schema, eventos, API, UI e logs não possuem campos proibidos; estado de
  atividade é rotulado como estimativa, inclui `inconclusivo` e não gera sanção automática.
- **Status:** gate definido; verificação acompanha cada fase.

## Atividade observável

### ACT-001 — Estados observáveis e inconclusivo

- **Descrição:** estimar `trabalho_aparente`, `pausa_aparente` ou `inconclusivo` a partir
  de sinais visuais definidos, sem afirmar intenção ou produtividade.
- **Fase:** SE-04 | **Prioridade:** crítico | **Dependências:** OCC-001, OCC-003.
- **Aceite:** critérios são explícitos e testáveis; baixa confiança ou atividade ambígua
  resulta em `inconclusivo`; a UI usa linguagem de estimativa.
- **Status:** pendente.

### ACT-002 — Regras por contexto de trabalho

- **Descrição:** configurar sinais permitidos por tipo de ambiente e função, pois
  celular, conversa ou imobilidade podem representar trabalho legítimo.
- **Fase:** SE-04 | **Prioridade:** crítico | **Dependências:** GOV-002, ACT-001.
- **Aceite:** não existe regra universal oculta; versão, autor, justificativa e período
  de validade da configuração são auditáveis.
- **Status:** pendente.

### ACT-003 — Rastreamento efêmero por sessão

- **Descrição:** associar observações à mesma caixa apenas pelo tempo mínimo da sessão,
  sem reconhecimento facial ou reidentificação entre câmeras.
- **Fase:** SE-04 | **Prioridade:** crítico | **Dependências:** OCC-001, PRIV-003.
- **Aceite:** identificadores são voláteis, reiniciam com o processo e não entram em
  banco/log/exportação; múltiplas pessoas não misturam estados silenciosamente.
- **Status:** pendente.

### ACT-004 — Supervisão humana e uso não punitivo

- **Descrição:** impedir que uma estimativa visual seja a única base de decisão adversa.
- **Fase:** SE-04/transversal | **Prioridade:** crítico | **Dependências:** ACT-001, GOV-004.
- **Aceite:** nenhum alerta aplica sanção, ranking ou controle de ponto; revisão,
  correção, contestação e limitações ficam visíveis.
- **Status:** regra aceita; implementação pendente.

## Dados e Supabase

### DATA-001 — Domínio mínimo

- **Descrição:** modelar organização, local, ambiente, câmera e evento de ocupação.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** GOV-002.
- **Aceite:** cardinalidades, UTC, estados e validações estão explícitos; não existem
  pessoa, face, embedding, imagem ou vetor no schema do MVP.
- **Status:** pendente.

### DATA-002 — Integridade e migrações reversíveis

- **Descrição:** aplicar FK, unique/check, transações, índices e migrações revisadas.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** DATA-001.
- **Aceite:** banco vazio chega ao head; downgrade suportado funciona; falha reverte;
  estados impossíveis e contagens negativas são recusados.
- **Status:** pendente.

### DATA-003 — Supabase validado por PoC

- **Descrição:** usar Supabase/PostgreSQL como central preferencial, sem presumir que
  região, plano, Auth, RLS, quota, custo, backup ou restore já foram validados.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** DATA-001, SEC-001.
- **Aceite:** projeto autorizado e descartável demonstra migração, isolamento RLS
  positivo/negativo, backup/restore e eliminação; lacunas ficam registradas.
- **Status:** pendente; nenhum projeto/credencial remoto existe no repositório.

### DATA-004 — Retenção e eliminação por classe

- **Descrição:** manter tabela de retenção para evento, auditoria, exportação, outbox e
  backup, com job e evidência de eliminação.
- **Fase:** SE-02/SE-07 | **Prioridade:** crítico | **Dependências:** GOV-002.
- **Aceite:** prazos aprovados, legal hold excepcional, réplicas/exports/backups e teste
  de exclusão estão cobertos; nenhuma retenção é infinita por default.
- **Status:** pendente; prazos `unspecified`.

## Autenticação e autorização

### AUTH-001 — Autenticação central

- **Descrição:** usar Supabase Auth ou alternativa aprovada para sessões de usuário.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** DATA-003.
- **Aceite:** login/logout/expiração/revogação são testados; senha/token não aparece em
  código, URL, resposta indevida ou log.
- **Status:** pendente.

### AUTH-002 — Papéis e negação por padrão

- **Descrição:** implementar Administrador, Operador e Visualizador com menor privilégio.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** AUTH-001.
- **Aceite:** matriz positiva e negativa cobre cada operação; ação não concedida é negada.
- **Status:** pendente.

### AUTH-003 — Isolamento por organização e local

- **Descrição:** aplicar escopo no backend, consultas e RLS.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** AUTH-002, DATA-003.
- **Aceite:** testes cross-tenant/cross-site não retornam nem alteram dados; IDs
  adivinhados não ampliam acesso.
- **Status:** pendente.

## API e sincronização

### API-001 — Ingestão autenticada e versionada

- **Descrição:** aceitar somente eventos conhecidos de dispositivos registrados.
- **Fase:** SE-05 | **Prioridade:** crítico | **Dependências:** DATA-002, AUTH-003.
- **Aceite:** schema/versão/tamanho são validados; autenticação e escopo são obrigatórios;
  payload inesperado recebe erro seguro.
- **Status:** pendente.

### API-002 — Outbox local limitada

- **Descrição:** reter eventos agregados durante indisponibilidade temporária.
- **Fase:** SE-05 | **Prioridade:** alto | **Dependências:** API-001, DATA-004.
- **Aceite:** limite de tamanho/idade, confinamento, transação e limpeza são testados;
  pixels e identidade não entram na fila.
- **Status:** pendente.

### API-003 — Idempotência e retry

- **Descrição:** repetir envio com backoff/jitter sem duplicar efeitos.
- **Fase:** SE-05 | **Prioridade:** crítico | **Dependências:** API-001, API-002.
- **Aceite:** replay, timeout e resposta perdida mantêm uma única ocorrência lógica por
  `event_id`; conflito é auditado e não sobrescrito silenciosamente.
- **Status:** pendente.

### API-004 — Observabilidade minimizada

- **Descrição:** medir ingestão, fila, erro e latência sem expor segredos ou dados
  desnecessários.
- **Fase:** SE-05 | **Prioridade:** alto | **Dependências:** SEC-004.
- **Aceite:** métricas possuem cardinalidade limitada; logs usam allowlist e correlação;
  falhas são diagnosticáveis sem payload bruto.
- **Status:** pendente.

## Interface web

### WEB-001 — Ocupação e saúde atuais

- **Descrição:** mostrar estado atual, última atualização e saúde por ambiente permitido.
- **Fase:** SE-06 | **Prioridade:** crítico | **Dependências:** API-001, AUTH-003.
- **Aceite:** loading, empty, stale, unknown e error são distintos; dado vencido não é
  apresentado como atual.
- **Status:** protótipo visual concluído com dados simulados; integração, autenticação e
  estados de falha reais permanecem pendentes.

### WEB-002 — Histórico, filtros e gráficos

- **Descrição:** consultar períodos e ambientes autorizados em visualização compreensível.
- **Fase:** SE-06 | **Prioridade:** alto | **Dependências:** WEB-001.
- **Aceite:** timezone, paginação, filtro e dataset vazio são testados; números da UI
  reconciliam com a API.
- **Status:** protótipo inclui busca, filtro e gráficos simulados; API, paginação,
  timezone e reconciliação permanecem pendentes.

### WEB-003 — Responsividade e acessibilidade

- **Descrição:** funcionar em desktop/mobile, teclado e contraste adequado.
- **Fase:** SE-06 | **Prioridade:** alto | **Dependências:** WEB-001.
- **Aceite:** navegação por teclado, foco, labels, zoom e tamanhos alvo têm verificação;
  informação não depende somente de cor.
- **Status:** layout responsivo, semântica e lint de acessibilidade implementados;
  verificação visual de zoom, contraste e tamanhos-alvo permanece pendente.

### WEB-004 — Nenhum vídeo exposto

- **Descrição:** não publicar stream, frame, URL de câmera ou credencial no dashboard.
- **Fase:** SE-06 | **Prioridade:** crítico | **Dependências:** CAM-003.
- **Aceite:** rotas, bundle, respostas e armazenamento do navegador não contêm pixels
  ou endpoints de streaming no MVP.
- **Status:** atendido no protótipo visual: apenas ilustração CSS e dados simulados,
  sem stream, frame, URL de câmera ou cliente de rede; revalidar na integração.

## Sustentabilidade

### SUS-001 — Indicadores de uso do ambiente

- **Descrição:** calcular horas-ocupação, períodos vazios e picos por janela.
- **Fase:** SE-08 | **Prioridade:** alto | **Dependências:** OCC-002, WEB-002.
- **Aceite:** fórmulas versionadas, UTC/fuso, dados ausentes e reconciliação são testados.
- **Status:** pendente.

### SUS-002 — Estimativas honestas

- **Descrição:** diferenciar oportunidade estimada de economia medida.
- **Fase:** SE-08 | **Prioridade:** crítico | **Dependências:** SUS-001.
- **Aceite:** tarifa, potência, período e demais premissas aparecem; sem medidor, a UI
  nunca apresenta redução financeira/energética como fato observado.
- **Status:** pendente.

### SUS-003 — Recomendação com revisão humana

- **Descrição:** sugerir ação, sem comandar equipamento no MVP.
- **Fase:** SE-08 | **Prioridade:** crítico | **Dependências:** SUS-002.
- **Aceite:** usuário confirma/descarta; histórico diferencia sugestão de execução;
  falha/baixa confiança impede recomendação automática.
- **Status:** pendente.

## Recursos e patrimônio

### AST-001 — Inventário e zonas

- **Descrição:** cadastrar ativo, categoria, estado e zona sem vincular pessoa observada.
- **Fase:** SE-09 | **Prioridade:** alto | **Dependências:** AUTH-003.
- **Aceite:** CRUD, validação, escopo e auditoria passam; campos sensíveis desnecessários
  são ausentes.
- **Status:** pendente.

### AST-002 — Movimentação autorizada

- **Descrição:** registrar eventos manuais/sintéticos de entrada, saída e mudança de zona.
- **Fase:** SE-09 | **Prioridade:** alto | **Dependências:** AST-001.
- **Aceite:** origem, horário, estado e revisão são rastreáveis; operação indevida é negada.
- **Status:** pendente.

### AST-003 — Alerta não acusatório

- **Descrição:** sinalizar evento fora da regra sem afirmar furto, autor ou culpa.
- **Fase:** SE-10 | **Prioridade:** crítico | **Dependências:** AST-002, ALT-002.
- **Aceite:** linguagem neutra, revisão/correção humana e auditoria são obrigatórias;
  nenhum alerta associa automaticamente o evento a um colaborador.
- **Status:** pendente.

## Alertas e relatórios

### ALT-001 — Regras configuráveis

- **Descrição:** configurar lotação, vazio prolongado, fora de horário, dispositivo
  offline e eventos patrimoniais.
- **Fase:** SE-10 | **Prioridade:** alto | **Dependências:** OCC-002, AST-002.
- **Aceite:** limiar, janela, ambiente, severidade e habilitação são explícitos; default
  é desativado para canais externos.
- **Status:** pendente.

### ALT-002 — Ciclo de vida e deduplicação

- **Descrição:** abrir, confirmar, atribuir, resolver/corrigir e deduplicar alertas.
- **Fase:** SE-10 | **Prioridade:** alto | **Dependências:** ALT-001.
- **Aceite:** repetição não cria tempestade; transições inválidas são negadas; revisão
  humana e histórico permanecem disponíveis.
- **Status:** pendente.

### ALT-003 — Canais seguros e opt-in

- **Descrição:** entregar notificações minimizadas sem bloquear ingestão.
- **Fase:** SE-10 | **Prioridade:** médio | **Dependências:** ALT-002.
- **Aceite:** canal começa desligado; segredo/payload são protegidos; retry tem limite;
  indisponibilidade do provedor não perde o evento central.
- **Status:** pendente; canais `unspecified`.

### ALT-004 — Relatórios e exportações controlados

- **Descrição:** gerar indicadores permitidos com autoria, período e filtros claros.
- **Fase:** SE-10 | **Prioridade:** alto | **Dependências:** WEB-002, DATA-004.
- **Aceite:** RBAC, escopo, limite, auditoria e retenção da exportação são aplicados;
  arquivos não incluem frames ou identidade.
- **Status:** pendente.

## Privacidade, segurança e operação

### PRIV-001 — Minimização por padrão

- **Descrição:** excluir identidade, biometria, áudio, imagem persistida e tracking
  persistente do modelo de dados do MVP.
- **Fase:** SE-01/transversal | **Prioridade:** crítico | **Dependências:** GOV-001.
- **Aceite:** arquitetura e requisitos registram a proibição; schema/API/UI confirmam
  tecnicamente nas fases seguintes.
- **Status:** baseline documental concluído; verificação técnica pendente.

### PRIV-002 — Descarte verificável de frames

- **Descrição:** provar que buffers não viram persistência acidental.
- **Fase:** SE-02/SE-04 | **Prioridade:** crítico | **Dependências:** CAM-003.
- **Aceite:** testes cobrem arquivos, banco, rede, logs, cache e falha; preview de
  calibração é local, temporário, sinalizado e desligado fora do modo autorizado.
- **Status:** pendente.

### PRIV-003 — Granularidade contra reidentificação

- **Descrição:** reduzir inferência por mesa, pessoa, segundo ou ambiente de baixa
  ocupação, mesmo sem nome.
- **Fase:** SE-02/SE-04 | **Prioridade:** crítico | **Dependências:** GOV-002.
- **Aceite:** janela/zona/limiar mínimo são definidos por avaliação de risco; consulta e
  exportação não permitem reconstrução desnecessária de rotina individual.
- **Status:** pendente; granularidade `unspecified`.

### PRIV-004 — Gate antes de câmera real e transparência

- **Descrição:** autorizar local, enquadramento e pessoas antes de qualquer teste real;
  ampliar transparência, horários, retenção e canal antes do piloto.
- **Fase:** SE-02/SE-07 | **Prioridade:** crítico | **Dependências:** GOV-003.
- **Aceite:** em SE-03, teste real ocorre em cenário controlado, vazio ou apenas com o
  próprio responsável informado, áudio desligado e sem terceiros incidentais; qualquer
  outra pessoa aguarda o gate completo. Antes de SE-07, aviso e sinalização, finalidade,
  horários, dados, retenção e canal estão aprovados. Banheiro, vestiário, descanso e
  áreas de alta expectativa de privacidade são proibidos; menores/escolas ficam fora.
- **Status:** pendente.

### PRIV-005 — Direitos, revisão e contestação

- **Descrição:** oferecer canal e processo para acesso, correção, oposição/bloqueio e
  revisão de resultado quando aplicável.
- **Fase:** SE-07/SE-12 | **Prioridade:** crítico | **Dependências:** GOV-003, DATA-004.
- **Aceite:** solicitação autenticada recebe rastreio e prazo; correção/exclusão alcança
  sistemas aplicáveis; ninguém é prejudicado por contestar uma estimativa.
- **Status:** pendente.

### SEC-001 — Segredos fora do código e cliente

- **Descrição:** separar configuração pública, segredo do backend e credencial por dispositivo.
- **Fase:** SE-02/transversal | **Prioridade:** crítico | **Dependências:** nenhuma.
- **Aceite:** `.env.example` contém apenas placeholders; `service_role` não entra no
  browser/dispositivo/log; rotação e revogação são testáveis.
- **Status:** baseline local parcial existente; Supabase pendente.

### SEC-002 — Defesa em profundidade de autorização

- **Descrição:** combinar autorização do backend, RLS e consultas parametrizadas.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** AUTH-003.
- **Aceite:** testes negativos cross-tenant e bypass por ID/role falham com resposta segura.
- **Status:** pendente.

### SEC-003 — Entradas, transporte e abuso

- **Descrição:** validar payload, tamanho, tipo, origem e frequência sobre HTTPS.
- **Fase:** SE-05 | **Prioridade:** crítico | **Dependências:** API-001.
- **Aceite:** injection, payload extra/grande, replay e rate abuse têm testes; TLS termina
  somente em proxy/backend confiável.
- **Status:** pendente.

### SEC-004 — Logs e auditoria seguros

- **Descrição:** usar allowlist, correlação e trilha de ações privilegiadas.
- **Fase:** transversal | **Prioridade:** alto | **Dependências:** baseline FND-01.
- **Aceite:** credenciais/pixels/PII desnecessária não aparecem; acesso, exportação,
  configuração e resolução de alerta deixam evidência íntegra.
- **Status:** logging da CLI concluído; auditoria de domínio pendente.

### SEC-005 — Supply chain e release

- **Descrição:** controlar versões, licenças, vulnerabilidades, segredos e componentes.
- **Fase:** SE-12 | **Prioridade:** alto | **Dependências:** stack implementada.
- **Aceite:** lock, SCA, SAST, busca de segredos e SBOM possuem ferramenta/escopo/resultado
  registrados; finding crítico é corrigido, contido ou aceito formalmente.
- **Status:** qualidade baseline existe; gates completos pendentes.

### OPS-001 — Limites e encerramento

- **Descrição:** manter filas, memória, CPU, retries e recursos sob limites explícitos.
- **Fase:** SE-03/transversal | **Prioridade:** alto | **Dependências:** CAM-002.
- **Aceite:** fila cheia descarta conforme política; shutdown libera recursos; soak não
  cresce sem limite.
- **Status:** pendente.

### OPS-002 — Backup e restore

- **Descrição:** documentar e testar recuperação de banco, configuração e outbox aplicável.
- **Fase:** SE-02/SE-07/SE-12 | **Prioridade:** crítico | **Dependências:** DATA-003.
- **Aceite:** restore descartável mede RPO/RTO; backup não é declarado válido apenas por existir.
- **Status:** pendente; metas `unspecified`.

### OPS-003 — Fail-safe de automação física

- **Descrição:** exigir modo sugestão, override, redundância e estado seguro antes de atuar.
- **Fase:** SE-12 | **Prioridade:** crítico | **Dependências:** SUS-003.
- **Aceite:** análise de perigo e falhas de sensor/rede/energia demonstram estado seguro;
  iluminação de segurança e equipamento crítico não são desligados por uma contagem.
- **Status:** pendente; automação está fora do MVP.

### OPS-004 — Runbook e observabilidade

- **Descrição:** documentar instalação, saúde, incidente, recuperação e rollback.
- **Fase:** SE-07/SE-12 | **Prioridade:** alto | **Dependências:** vertical implementada.
- **Aceite:** outra pessoa executa o runbook e recupera um cenário de falha documentado.
- **Status:** pendente.

### OPS-005 — Capacidade e custo

- **Descrição:** medir antes de prometer escala ou economia.
- **Fase:** SE-07/SE-11/SE-12 | **Prioridade:** alto | **Dependências:** vertical implementada.
- **Aceite:** FPS, latência, CPU/RAM, rede, armazenamento e custo Supabase têm baseline e limites.
- **Status:** pendente.

## Testes e dispositivos futuros

### TEST-001 — Gates automatizados de qualidade

- **Descrição:** manter testes, lint, formato, tipos, compilação e build reproduzível.
- **Fase:** transversal | **Prioridade:** crítico | **Dependências:** FND-01.
- **Aceite:** comandos documentados passam no ambiente suportado; falha bloqueia avanço.
- **Status:** baseline concluído em Python 3.11/3.12; novas camadas devem estender a suíte.

### TEST-002 — Câmera simulada e contratos

- **Descrição:** testar captura/erros sem câmera real.
- **Fase:** SE-02 | **Prioridade:** crítico | **Dependências:** CAM-001.
- **Aceite:** frames válidos/inválidos, timeout, EOF, falha e ciclos passam deterministicamente.
- **Status:** em andamento; contratos principais passam deterministicamente, mas timeout
  explícito ainda precisa de implementação e teste.

### TEST-003 — Avaliação de ocupação

- **Descrição:** medir detector/agregador em conjunto representativo e autorizado.
- **Fase:** SE-02/SE-04/SE-07 | **Prioridade:** crítico | **Dependências:** OCC-003.
- **Aceite:** métricas, amostra, condições, limitações e regressão são versionadas; não
  há alegação genérica de acurácia.
- **Status:** pendente.

### TEST-004 — Vertical e piloto

- **Descrição:** exercitar webcam→evento→API→Supabase→dashboard e cenários de falha.
- **Fase:** SE-07 | **Prioridade:** crítico | **Dependências:** WEB-004, API-003.
- **Aceite:** happy path, autorização negativa, rede offline, replay, retenção, exclusão
  e zero persistência de pixels têm evidência.
- **Status:** pendente.

### DEV-001 — Registro e revogação de dispositivo

- **Descrição:** dar identidade técnica própria a cada agente de borda.
- **Fase:** SE-11 | **Prioridade:** alto | **Dependências:** API-001.
- **Aceite:** enrollment único, rotação/revogação e último heartbeat são testados.
- **Status:** pendente.

### DEV-002 — Isolamento multicâmera

- **Descrição:** uma fonte falha sem derrubar as demais.
- **Fase:** SE-11 | **Prioridade:** alto | **Dependências:** CAM-004, OPS-001.
- **Aceite:** supervisor limita restart/backoff e mantém estados individuais.
- **Status:** pendente.

### DEV-003 — Gateway ESP32/IP seguro

- **Descrição:** receber câmera futura por conexão autenticada de saída, sem stream público.
- **Fase:** SE-11 | **Prioridade:** alto | **Dependências:** DEV-001, DEV-002.
- **Aceite:** credencial individual, TLS, limites, formato validado e revogação passam;
  modelo/placa/protocolo permanecem específicos da PoC.
- **Status:** pendente.

### DEV-004 — Escala medida

- **Descrição:** limitar quantidade de fontes conforme capacidade observada.
- **Fase:** SE-11 | **Prioridade:** alto | **Dependências:** DEV-002, OPS-005.
- **Aceite:** teste 1→N registra saturação e degradação; configuração recusa limite inseguro.
- **Status:** pendente.

## Decisões que bloqueiam dados reais

- controlador, operadores, encarregado e local do piloto;
- finalidade detalhada, base legal e avaliação/RIPD aplicável;
- granularidade temporal/espacial e limiar contra reidentificação;
- retenção por classe, exclusão, backup e canal de titulares;
- região/plano/quotas/custo do Supabase;
- detector/pesos/licença e critérios mínimos de qualidade;
- enquadramento, aviso e áreas permitidas da câmera.

Até esses itens serem resolvidos na fase correspondente, usar apenas dados sintéticos
ou material explicitamente autorizado para teste técnico controlado.

## Rastreabilidade

A tabela de etapas e requisitos está em `.planning/ROADMAP.md`. O backlog atômico está
em `.planning/BACKLOG.md`; evidências da etapa corrente ficam em
`.planning/phases/se-01-replanning/`.
