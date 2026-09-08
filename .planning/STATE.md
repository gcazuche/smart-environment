# Estado GSD — Smart Environment

Atualizado em: 2026-09-08

## Ativação DB-01 — UUID configurado; primeiro login do dashboard pendente

- Em 08/09/2026, usuário autenticou o navegador integrado no Supabase. Projeto
  `smart-environment` identificado pela correspondência exata com a URL local.
- Leitura do banco confirmou uma única organização Smart Environment e um vínculo
  `admin` para a conta do e-mail configurado no bootstrap; conta Auth confirmada.
  UUID real preenchido em `dashboard/.env.local`, ainda ignorado pelo Git. Nenhuma
  chave foi exibida, nenhum bootstrap/migração foi reaplicado e nenhum dado de negócio
  ou permissão foi modificado no banco remoto.
- Consulta SELECT no SQL Editor confirmou: 8 tabelas esperadas, RLS habilitada em
  todas, SELECT de anon negado, SELECT de authenticated concedido, funções de relatório
  e revisão existentes. Isso verifica configuração estrutural; não equivale a testar
  sessão/JWT real, todos os casos de RLS ou gravação real pelo dashboard.
- `parseBackendConfig` validou arquivo local e UUID; build + 51 testes passaram em
  Conda smart-environment. Servidor local iniciou com `.env.local`; GET da raiz em
  `http://localhost:3000/` respondeu 200. Prévia preparada para primeiro login real.
- Próximo passo: usuário entrar no dashboard com a conta Auth já criada (senha definida
  por ele), validar carregamento do catálogo e cadastro/persistência de ambiente/câmera.
  Não solicitar senha no chat, não redefinir credenciais nem gerar usuário artificial.
  Ingestão Ubuntu, telemetria real e publicação continuam fora desta ativação.

### Histórico da preparação e do acesso

- Usuário solicitou conectar agora; informou não encontrar o UUID. O campo esperado
  é UUID de `public.organizations`, gerado pelo bootstrap, não o project ref Supabase.
- Encontrados URL/chave publicável preenchidos no exemplo do dashboard. Preservados
  em `.env.local` ignorado pelo Git; exemplo voltou a campos vazios. UUID local segue
  vazio, sem inventar ID. Nunca registrar valores das chaves no checkpoint.
- Diagnóstico somente leitura contra o endpoint configurado: `/auth/v1/settings` 200;
  `organizations?select=id&limit=0` 401 / 42501 com chave pública sem sessão. Isso não
  permite ler a organização nem comprova execução completa da migração/bootstrap.
- O bootstrap tem e-mail preenchido pelo usuário. Não reexecutar cegamente nem criar
  segunda organização: primeiro SELECT somente leitura do vínculo/organização existente.
- Painel Supabase aberto no navegador do aplicativo, mas está na tela de sign-in;
  necessário usuário entrar por conta própria. Nenhuma senha solicitada no chat,
  migração remota executada ou permissão remota concedida.
- Após login: conferir schema e conta, recuperar UUID; se bootstrap não foi aplicado,
  confirmar a concessão de administrador antes de fazê-la via UI; preencher UUID,
  reiniciar dashboard e validar autenticação/cadastros reais.
- Usuário instalou/conectou e autorizou usar o plugin Supabase. Registro da integração
  confirmou `installed=true`, `enabled=true`, sem dependências não resolvidas. Porém,
  a lista de ferramentas desta sessão não contém consultas/projetos/migrações Supabase;
  os recursos listam somente o plugin e suas skills. Isso não comprova acesso OAuth ao
  projeto. Nenhuma consulta administrativa ou escrita remota foi feita nesta tentativa.
- Endpoint MCP respondeu 401 em prova sem credenciais (serviço alcançável, não uma
  falha de credencial do usuário). Próximo passo: recarregar a sessão/conexão do plugin
  e redescobrir as ferramentas; limitar a operação ao projeto configurado no arquivo
  local. Consultar vínculos existentes antes de qualquer bootstrap; múltiplas
  organizações exigem escolha explícita. UUID continua pendente, sem valor inventado.

## Incremento atual — SEC-01: dependências antes da exposição

- Usuário autorizou seguir a sequência; Supabase continua reservado para criação
  posterior por ele. Nenhuma conexão remota, VM, publicação ou etapa de ingestão
  foi executada. Fechada primeiro a pendência de segurança da preparação local.
- React/DOM/RSC 19.2.8, Vite 8.0.16, Cloudflare plugin 1.54.4 e Wrangler 4.129.0;
  transitivas compatíveis resolvidas sem force/overrides, mantendo Vinext beta.2.
- Audit passou de 19 para 2 entradas altas: image-size 2.0.2 e Vinext dependente.
  O beta.9 incorporaria a mesma biblioteca e esconderia o finding, não o corrigiria.
  Não há aprovação de produção, supressão de finding nem migração cosmética.
- Revisão do parser: somente imports/metadados de arquivos locais em dev/build nos
  caminhos encontrados; nenhuma entrada remota atual demonstrada. Exigir revisão
  de novos assets/imports, sem build de material não confiável com segredos.
- Host de desenvolvimento explícito localhost; imagens sociais deixam de refletir
  Host/forwarded host não confiável. Interface e cadastros existentes preservados.
- Build + 51 testes dashboard, ESLint, TypeScript global e árvore npm aprovados;
  servidor dev atualizado iniciou em localhost e a raiz respondeu HTTP 200.
  Detalhes e comandos:
  `docs/dependency-hardening.md`. Não revalidou câmeras/VM/produção.
- Próximos passos da sequência: criar/configurar Supabase e validar contas/cadastros
  reais; depois integrar ingestão no Ubuntu; depois medir 3–4 câmeras/720p/30 FPS.
  A correção/aceitação explícita do risco residual precede exposição/publicação.

## DB-01: integração preparada, ativação remota posterior

- Pedido do usuário: continuar sem criar/configurar projeto Supabase agora; ele fará
  isso depois. Não pedir URL como condição para continuar código/testes locais.
- Migração inicial adiciona organizações, membros admin/viewer, ambientes, câmeras,
  regras, amostras agregadas de 1 minuto, alertas e auditoria. RLS isola organizações;
  sem cadastro público de privilégios, escrita de observações pelo navegador ou DELETE.
- Adaptador Supabase conecta login, sessão, permissões, cadastro/edição, consultas,
  paginação/CSV e revisão/resolução de alertas com versões e autoria separadas.
- Ambientes têm coleção própria (inclusive vazios); monitor_id associa a telemetria
  sem sobrescrever nomes/configuração. Autorização é revalidada e dados de sessão
  não podem receber respostas antigas após logout/troca de conta.
- Sem configuração, acesso local permanece disponível somente em loopback; formulários
  não salvam e explicam a dependência. Variáveis parciais falham fechadas. `.env.example`
  público e bootstrap SQL manual foram preparados, sem segredos/projeto remoto.
- Testes locais: build + 48 testes dashboard passaram; 8 exercitam a migração real
  em PostgreSQL/PGlite com papéis distintos. Há contratos SDK com fetch interceptado.
  TypeScript global/lint passaram; corrigidos tipos não usados do Worker D1 legado.
  Regressão Python final: 127 testes + 11 subtestes aprovados no Conda smart-environment.
- Revisão independente encontrou/corrigiu NULL no lock otimista, associação de ambiente
  inválida, perda de autoria de revisão e corrida de snapshot antigo contra salvamento.
- Audit completo: 19 avisos PREEXISTENTES (16 altos/1 moderado/2 baixos); versões dos
  caminhos vulneráveis idênticas a HEAD. Supabase/PGlite sem finding nesta consulta.
  Não publicar/expor dev server à rede antes de remediar/validar o conjunto do framework.
  O zero do audit omit=dev não equivale a segurança do artefato de servidor.
- Limites: sem Supabase/Auth/PostgREST real, ingestão/alertas automáticos, gateway remoto,
  30 FPS na VM, testes de clique/teclado no navegador, deploy, commit/push ou fotos alteradas.
- Próximo passo de servidor: ingestão agregada autorizada no Ubuntu, deduplicação/retry,
  regra de agregação/retenção e operação das fontes. Ativação remota só quando o usuário
  criar o projeto; seguir `docs/supabase-setup.md` e validar contas reais e persistência.
- Checkpoints históricos abaixo preservados; DB-01 prevalece sobre afirmações antigas
  de que não há migração/adaptador, que formulários são sempre desabilitados ou que
  Fetcher/D1Database ainda impedem type-check.

## Histórico — UI-02: controles e data/hora (parcial em 04/09)

- Pedido: corrigir controles sem ação e cabeçalho com data fixa; preservar o stream.
- Relógio pt-BR atualiza a cada segundo e ao reabrir a aba, com fuso explícito
  America/Sao_Paulo, dia/mês/ano e hora; SSR inicial sem data inventada.
- Adicionar/editar câmera e ambos os botões de novo ambiente abrem formulários
  com validação. Salvar está explicitamente desabilitado; não há persistência falsa,
  alteração da telemetria nem localStorage como banco.
- Histórico abre uma página própria; períodos atualizam o intervalo exibido. Não
  consulta banco ainda. Indicadores e alertas fictícios removidos; mostram serviço
  indisponível, não zero ocorrências. Regras abre uma explicação da integração pendente.
- Modais nativos tratam Escape/foco; navegação móvel expõe todas as seções. Stream
  e detecção preservados; contagens sem leitura não são apresentadas como zero.
- Lacuna bloqueante: usuário ainda não informou projeto/configuração Supabase.
  Pergunta enviada. CRUD, autenticação real, regras, consulta/exportação histórica
  e integração de novas câmeras NÃO foram implementados neste incremento.
- Validação: 32 testes JS/TS aprovados (8 novos), build e lint aprovados; type-check
  dos componentes tocados aprovado. Sem testes de clique/reprodução no navegador,
  sem acesso a câmeras, deploy, Supabase, commit/push ou alterações em datasets.
- Próximo passo: obter escolha/configuração do projeto Supabase, definir permissões
  e implementar a fatia persistente ambiente/câmera. Não basta preencher uma variável
  de ambiente: os formulários atuais ainda não possuem integração de salvamento.
- Detalhes: `docs/dashboard-controls.md`.

## Prioridade atual — ST-01: transmissão independente

- O usuário priorizou stream sem IA: destino VM Ubuntu/Hyper-V, 8 vCPU, 4 GB RAM
  ampliáveis, sem GPU, 3–4 câmeras 720p, meta 30 FPS de exibição por câmera.
- Implementado primeiro incremento local: player WHEP separado da detecção, métricas,
  ciclo de conexão e configuração MediaMTX com listeners somente em loopback.
- FFmpeg no Conda `smart-environment`; helper com download MediaMTX 1.20.1 verificado,
  padrão sintético e webcam. Nenhuma alteração no Conda base ou na VM.
- Guia/validação/limites: `docs/streaming-local.md`. Fonte sintética 720p30 e sinalização
  WHEP real verificadas; reprodução/30 FPS no navegador e VM ainda não comprovados.
- Webcam USB2.0 HD UVC WebCam testada sem IA: 113 frames em 14,96 s, cerca de 7,5 FPS
  reais apesar do modo anunciado 720p30. Saída FFmpeg com `-fps_mode passthrough`
  para não mascarar a cadência com duplicação. Causa da captura lenta ainda aberta.
- Validação ST-01: 127 testes Python + 11 subtestes e 24 testes dashboard aprovados;
  build/lint, Ruff e mypy do helper aprovados. Type-check global ainda encontra
  Fetcher/D1Database ausentes no Worker preexistente (módulos novos passaram).
- Cadastro persistente, múltiplas fontes, autenticação da rede e overlays da IA
  permanecem fora deste incremento. O antigo fluxo local continua disponível.
- Preparação de treinamento abaixo permanece preservada/pausada; nenhuma foto ou
  rótulo alterado, nenhum treinamento iniciado.

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch no início de SE-01:** `main`
- **Fundação técnica histórica:** concluída; código preservado
- **Checkpoint funcional atual:** dataset autorizado pré-rotulado; revisão humana pendente

## Posição atual

- **Etapa concluída:** SE-01 — Rebaseline Smart Environment
- **Etapa atual:** SE-04 — Ocupação e atividade observável
- **Plano atual:** `.planning/phases/se-04-activity-observation/STEP-03-AUTHORIZED-DATASET-SPEC.md`
- **Tarefa atual:** Etapa 3D gerou o piloto sem celular; corrigir as 33 anotações é o próximo gate
- **Autorização:** webcam e detecção local autorizadas pelo usuário em 2026-08-14
- **Plano antigo:** `.planning/phases/02-database/` superado e somente histórico

## Resultado de SE-01

- Produto redefinido como gestão inteligente de ambientes.
- MVP fixado em uma webcam, frames transitórios, contagem sem identificação, evento
  agregado, Supabase e dashboard web.
- “Desempenho” limitado ao ambiente; distração/produtividade individual excluídas.
- Reconhecimento facial, embeddings, pgvector, vivacidade e PySide6 retirados do baseline.
- Roadmap incremental, requisitos, riscos, testes, stack e ADRs realinhados.
- Nenhum código funcional, dependência, banco, câmera ou serviço externo foi alterado.

## Mudança de direção em 2026-08-14

- O usuário esclareceu que “desempenho” inclui estimar se a pessoa aparenta estar
  trabalhando ou relaxando.
- A primeira implementação foi antecipada para webcam e detecção de pessoas antes de
  Supabase; atividade observável permanece para SE-04.
- A classificação terá estado `inconclusivo`, regras por contexto e uso não punitivo.
- Por decisão do usuário, a melhoria do detector foi pausada após o primeiro protótipo;
  o dashboard visual foi antecipado e a detecção será retomada depois.

## O que funciona hoje

- Ambiente Conda isolado `smart-environment` com Python 3.12.13 e `environment.yml`;
  nenhum comando de instalação desta migração foi direcionado ao `base`.
- Configuração mínima, comando `doctor`, logging JSON seguro e tratamento de exceções.
- OpenCV/NumPy fixados; câmera com fallback, CLI e detectores NanoDet/Intel substituíveis.
- 115 testes e 11 subtestes aprovados em Python 3.12, junto com Ruff e mypy strict.
- O smoke NanoDet via DirectShow processou 30 frames em memória, observou máximo de uma
  pessoa e liberou a câmera; qualidade ampla e estabilidade temporal seguem pendentes.
- A contagem inspecionada em `data/` permaneceu 5 antes e depois.
- Intel YOLO26n FP16/OpenVINO detectou duas pessoas na amostra indicada pela Intel, com
  média de 32,1 ms; NanoDet retornou três caixas e média de 90,1 ms na mesma imagem.
- Contrato Python imutável define os cinco estados observáveis e os limiares iniciais
  do cenário `office-computer`, sem abrir câmera, identificar pessoas ou classificar frames.
- Cada câmera aceita uma área retangular normalizada independente; a prévia local desenha
  a região e a API mantém apenas geometria e contagem espacial agregada em memória.
- Três imagens reais de escritórios ocupados foram revisadas visualmente e preparadas com
  origem, licença CC-BY-NC-SA-4.0, metadados e hashes fixados, fora do Git.
- O YOLO26/OpenVINO foi restringido a laptop, mouse, teclado e celular e executado somente
  nessas referências: dois laptops corretos, zero celulares e média de 43,2 ms por imagem.
  O diagnóstico em limiar 0,10 também não encontrou o celular; nenhuma atividade foi criada.
- Seis cenas sintéticas provisórias, sem rostos ou pessoas reais, foram fixadas por hash.
  No limiar 0,25, laptop apareceu nas 4 cenas esperadas e celular em 3/4; a cena ambígua
  perdeu o celular e criou uma caixa duplicada/falsa de laptop. Média: 41,4 ms por imagem.
  Em 0,10 o quarto celular apareceu junto de novos falsos sinais; o limiar não foi reduzido.
- As 62 fotos autorizadas foram reencodadas com nomes neutros, metadados removidos,
  66 regiões faciais, 166 zonas de cabeça e 64 telas redigidas; não há celular real nem
  classe de celular nesta versão. O original permaneceu intocado.
- Oito rajadas visuais foram mantidas inteiras por split e 33 frames representativos
  formam o piloto YOLO: 22 treino, 5 validação e 6 teste. Os pré-rótulos sugerem 27
  pessoas, 2 laptops, 12 mouses e 21 teclados, sempre com revisão obrigatória.
- Integridade confirmou 62/62 hashes de origem, 33/33 derivados, JPEGs sem segmentos de
  metadados sensíveis e somente IDs YOLO 0–3. O manifest permanece
  `ready_for_training=false` e `human_privacy_reviewed=false`.
- O smoke simultâneo abriu a webcam por DirectShow e o celular por MJPEG privado; as
  duas fontes ficaram online e o Intel/OpenVINO detectou uma pessoa em cada leitura
  observada, sem persistir frames.
- Agente local processa a webcam e uma URL MJPEG/RTSP privada do celular em workers
  isolados e expõe contagem, estado, backend, latência e um JPEG anotado volátil por
  câmera em `127.0.0.1:8765`, aceito somente da página local.
- Dashboard responsivo em `dashboard/`, com duas câmeras, estados agregados locais,
  ambientes, indicadores e alertas; a visão geral concentra indicadores e eventos,
  enquanto a lista e os detalhes das câmeras ficam na seção dedicada; os gráficos
  históricos seguem simulados.
- A aba **Ambientes** agrupa dinamicamente as câmeras pelo ambiente retornado pelo agente;
  **Ver ambiente** abre o resumo agregado e a grade com todas as prévias daquele local,
  com acesso aos detalhes de cada dispositivo.
- Acesso do dashboard protegido por uma tela de login local demonstrativa; o perfil do
  administrador permite consultar a sessão e sair, sem armazenar senhas. A consulta das
  câmeras só começa depois do login.
- A marca visual usa um espaço reservado para a logo definitiva, e a interface não exibe
  referências a protótipo, contexto acadêmico ou demonstração.
- Build Vinext, lint ESLint e dois testes de renderização aprovados.
- Interface privada publicada em
  `https://smart-environment-monitor.angel-of-the-night16.chatgpt.site`.

## O que não existe

- Schema, migrações, projeto Supabase, Auth, RLS ou conexão PostgreSQL.
- Outbox SQLite, API remota, sincronização ou autenticação de produção da aplicação.
- Dataset representativo, métricas de falso sinal/latência e detector aprovado para produção;
  as referências públicas, sintéticas e o piloto autorizado servem somente para preparação
  e avaliação qualitativa enquanto as caixas não forem revisadas.
- Ground truth humano das 33 imagens; `laptop` tem somente dois pré-rótulos em treino e
  nenhum em validação/teste, então essa classe ainda não pode ser avaliada.
- Backend remoto/Supabase, autenticação, vídeo remoto e dados persistentes no dashboard
  publicado.
- Supabase Auth, expiração/revogação de sessão e permissões reais; o login atual é somente
  um fluxo local de demonstração para UX do TCC.
- Avaliação representativa das duas câmeras, alertas reais, ESP32, automação ou piloto.
- Calibração física ou seleção da área pelo dashboard, tracking, pose, objetos nas câmeras,
  agregação temporal e classificador de atividade.

## Bloqueios antes de dados reais

- finalidade detalhada, controlador, operadores de tratamento, encarregado e local autorizado;
- base legal/RIPD/avisos aplicáveis e áreas/horários permitidos;
- retenção, granularidade contra reidentificação e processo de direitos;
- região/plano/quotas/custo/backup/restore do Supabase;
- detector/pesos/licença acadêmica aberta e critérios de qualidade.

## Decisões abertas

- framework web e biblioteca de gráficos;
- escolha entre NanoDet e Intel/OpenVINO após métricas representativas;
- granularidade temporal/espacial do evento;
- estratégia Realtime versus polling;
- metas de FPS, latência, capacidade e custo;
- protocolo/modelos de câmeras futuras/ESP32;
- momento e estratégia para migrar o nome técnico `multicam`.

## Como retomar

1. Ler `REQUIREMENTS.md`, `ROADMAP.md`, `DECISIONS.md`, este arquivo e a especificação da SE-04.
2. Revisar as 33 prévias em `data/datasets/workstation-prelabels-v1/previews/`, removendo
   falsos positivos e adicionando objetos omitidos, especialmente laptops.
3. Manter `cell_phone` fora do mapa até existir coleta própria com exemplos positivos.
4. Não executar fine-tuning enquanto `ready_for_training=false`; manter pose, tracking,
   classificação e persistência fora deste incremento.
5. Confirmar a sincronização do OneDrive antes de afirmar que os derivados não saíram do PC.

## Prompt de retomada sugerido

> Continue a Etapa 3D de SEB-016: revise comigo as 33 imagens pré-rotuladas de pessoa,
> laptop, mouse e teclado, sem adicionar celular e sem iniciar o treinamento antes de
> aprovar o ground truth.
