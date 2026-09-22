# Estado GSD — Smart Environment

Atualizado em: 2026-09-20

## SE-13 / DJ-02 a DJ-06 — aplicação Django migrada; aceite remoto pendente

- Pedido autorizado: terminar a transição. Aplicação principal agora `app/web/` +
  `manage.py`, Django/HTML/CSS/JavaScript puro. Não precisa de npm/TypeScript para
  rodar; `dashboard/` legado e trabalho anterior preservados, fora do fluxo principal.
- Login Supabase real implementado, mesmos usuários/organização e RLS, sem bootstrap.
  Sessões DB server-side, cookie HttpOnly com identificador, refresh/logout, CSRF,
  limite persistente de tentativas e papéis admin/viewer verificados no servidor.
  Autenticação recusa DEBUG/chave efêmera; produção exige HTTPS e hosts explícitos.
- Visão geral, perfil, câmeras, ambientes com todas as câmeras, formulários de
  câmera/ambiente/regra, indicadores, histórico, alertas/revisão e CSV implementados.
  Edições exigem versão original; exportação é da página consultada, não banco inteiro.
- Vídeo WebRTC/WHEP e polling portados para JS puro. Django encaminha sinalização e
  telemetria same-origin, nunca token para o browser nem vídeo pela view. Conexão
  manual, cleanup/aba oculta, leitura vencida desconhecida e overlay transitório.
  Ponte ao monitor loopback antiga é opt-in. Não abrimos câmera nesta migração.
- `prepare_web` executado localmente: configuração privada ignorada criada com segredo
  persistente e reaproveitamento allowlist do legado, sem exibir valores. `migrate`
  criou somente SQLite local de sessões/tentativas; não consultou/alterou Supabase.
- QA identificou Referrer-Policy/meta no-referrer incompatível com POST de formulário;
  corrigidos para same-origin. Origem externa/null permanece recusada e há regressões.
- Validação: **714 testes Python + 478 subtestes**, **17 testes JS**, Django check,
  Ruff/formato e pip check aprovados. Revisão independente sem novos P0/P1/P2 concretos.
  QA browser com base sintética isolada: login, navegação, ambiente com 2 câmeras,
  edição de ambiente/regra, criação de câmera, histórico/indicadores, revisão e logout.
  Perfil conferido em 390px. Evidência completa no arquivo abaixo; não é teste remoto.
- Guia completo novo PC/configuração/VM em `docs/django-migration.md`. Exemplos de
  Waitress (um processo, 8 threads) e Caddy em `config/web/`. CI principal Django;
  workflow manual preserva testes/audit do legado, sem dizer que seus riscos sumiram.
- Versão de pacote **0.3.0a1**, candidata Git **v0.3.0-alpha.1**, ainda NÃO publicada.
  Tags locais v0.1.0/v0.2.0 verificadas e preservadas; sem commit/tag/push. Consulte
  `docs/versioning.md`: árvore contém trabalho paralelo; revisar snapshot selecionado.
- Próximo aceite: conta real admin/viewer, CRUD/RLS/ingestão autorizados, deploy Ubuntu
  com TLS/proxy/permissões e vídeo real 720p/30 FPS medido. Não alegar treino concluído,
  produtividade inferida, instalação Linux ou desempenho da VM com base nestes testes.
- Especificação/evidências: `phases/se-13-django-migration/SPEC.md` e
  `COMPLETION-VERIFICATION.md`; DJ-01 abaixo é histórico, não o comportamento atual.
- QA encerrado, aba fechada, porta8001 sem listener. Cinco diretórios temporários
  de sessões fictícias ficaram no Temp após interrupção; limpeza bloqueada pela
  política da ferramenta, não contornada. Nenhum dado real ou arquivo Git envolvido.
- Limites de fotos/revisão humana/celular e pendências SE-04 continuam preservados.
  `h origin main` intocado. Nenhuma memória interna é exportada por estes documentos.

## Histórico de 19/09: SE-13 / DJ-01 — fundação Django

- Decisão confirmada: **Django + templates HTML/CSS/JavaScript puro, sem TypeScript
  no destino**. Prioridade atual é migração web, não treinamento de visão.
- Criados `manage.py`, `app/web/` e extra opcional `web` com Django 5.2.17 instalado
  no Conda smart-environment. Novo runtime independe de npm/Node, modelos e `.env`.
- Login visual preserva logos/cores; campos/Entrar desabilitados, aviso explícito.
  Não há login simulado, sessão, DB, bootstrap, painel funcional ou dados de câmeras.
- `/` → `/login/`; `/health/` somente liveness, autenticação/dados explicitamente false.
  Rotas GET/HEAD, CSP sem conexões/submissões, settings apenas desenvolvimento loopback.
- **Não implantar/usar autenticação real com DEBUG/chave efêmera.** DJ-02 deve introduzir
  configuração segura, sessão server-side, refresh/logout, CSRF e papéis existentes.
- `dashboard/` legado permanece intacto nesta etapa até paridade. Sua existência com
  TS não significa que a migração já terminou; não excluir telas prematuramente.
- Suíte final: **560 testes Python + 263 subtestes**, zero falhas/skips; **2 testes JS**
  novos, Django check, Ruff/formato e pip check aprovados. Wheel gerado, seis assets
  conferidos por hash; não houve instalação limpa/Linux nem auditoria SCA nova.
- QA real local: desktop/celular, logos e toggle de detalhes confirmados. Servidor
  127.0.0.1:8000 e aba de teste encerrados; não há servidor novo deixado em execução.
- Plano/evidências em `phases/se-13-django-migration/{SPEC,VERIFICATION}.md`;
  tutorial em `docs/django-migration.md`. CI Conda preparado, não rodou no GitHub.
- Próximos: DJ-02 autenticação/permissões, DJ-03 consultas/navegação, DJ-04 cadastros,
  DJ-05 vídeo/telemetria, DJ-06 relatórios/QA/deploy/corte do legado.
- Vídeo continua separado da análise; mudar web não comprova 30 FPS na VM.
  Câmeras, Supabase, fotos e detector intocados. Pendências SE-04 abaixo preservadas.
- main/f5b1f18; tags v0.1.0/v0.2.0 existentes verificadas, sem commit/tag/push.
  Alterações preexistentes e `h origin main` preservados; contagens incluem árvore local.

## SE-04 / REV-01 a REV-04 — editor offline e métricas, revisão humana pendente

- Criados app/datasets/workstation_review.py, assets HTML/JS, módulo de métricas e
  scripts/review_workstation_signals.py. Sem mudanças no detector/modelo das câmeras.
- Editor autocontido: caixas por arraste/campos, apagar/desfazer, importar/exportar,
  decisões explícitas. Propostas ocultas/opcionais, nunca copiadas como verdade.
  Campos ainda não aplicados bloqueiam download/decisão. Sem rede/telemetria/storage.
- JSON vincula revisão ao hash exato do relatório e fontes públicas fixas; limites,
  dimensões/classes/estados validados. Dados pendentes não produzem métricas; exclusões
  exigem motivo e são divulgadas. Hash não autentica revisor nem prova qualidade.
- Métricas TP/FP/FN/precision/recall/F1 por classe/modo, IoU 0,50 e matching 1:1.
  Sem mAP/atividade/produtividade/treino. Só testes sintéticos foram pontuados.
- Pacotes reais finais em data/reviews/workstations-{wide,close}-20260916-v3,
  com 2 e 6 fotos, respectivamente, todas pendentes. V1/V2 anteriores preservadas.
  V3 impede anotar/aprovar enquanto a imagem não carregou ou falhou no decode.
- Validação: **547 testes Python + 252 subtestes** e **54 testes Node**, sem falhas/skips.
  Ruff/formato em 5 arquivos Python e Mypy em 3 fontes/CLI do incremento.
- QA visual/interações/download reais pendentes: navegador integrado recusou file://;
  não houve workaround/servidor alternativo. Abrir HTML manualmente no navegador local.
- Guia em docs/workstation-review.md, evidências em
  phases/se-04-activity-observation/STEP-06-REVIEW-VERIFICATION.md. Assets incluídos
  no package-data Python; artefatos e revisões em data/ continuam ignorados no Git.
- Próximos: conferir interface, revisar caixas segundo convenção, medir nas fontes
  reservadas antes de ajustar/treinar. Fotos privadas/VM/Supabase permanecem intocados.
- Sem commit/tag/push, mudanças anteriores preservadas. Pendências independentes de
  frontend/segurança e comissionamento VM não foram revalidadas aqui.

## SE-04 / DET-01 a DET-04 — recortes offline avaliados, não promovidos

- Modo experimental `letterbox-detail`: quadro inteiro + até quatro recortes 60%,
  equipamento consolidado por classe, pessoas só do quadro inteiro, falha aborta tudo.
  CLI opt-in `--include-detail`; `--reference-set wide` seleciona duas novas cenas.
- Oito fotos públicas avaliadas com mesmos pesos/limiar 0,25 e sem ajuste posterior
  de parâmetros. Laboratório vazio recuperou duas propostas de teclado; escritório,
  uma. Surgiram falso mouse/caixa de laptop indevida e o notebook encoberto segue perdido.
- Decisão: **não promover às câmeras**. Default stretch, associação geométrica e pesos
  inalterados; sem treino, pose, tracking, celular, câmera, VM ou banco remoto.
- Medianas locais finais: close letterbox 31,752 ms vs detalhe 162,856 ms; wide 32,170
  vs 164,307 ms (~5,1x). Não são FPS de vídeo, desempenho VM ou métricas de precisão.
- Artefatos fora do Git: data/evaluations/workstation-detail-20260915-v2 e
  workstation-detail-wide-20260915-v1; rodada close v1 preservada. Oito comparações
  inspecionadas pelo assistente, não anotadas/aprovadas por humano.
- Validação final: **506 testes Python + 213 subtestes**, zero skips; Ruff/formato em
  8 arquivos e Mypy em 4 fontes do incremento. Revisão estática independente sem
  bloqueantes concretos; inclui teste adicional do perfil do wrapper real no relatório.
- Fonte: docs/workstation-evaluation.md e
  phases/se-04-activity-observation/STEP-05-DETAIL-DETECTION-VERIFICATION.md.
- Próximo: anotações humanas, negativos monitor/estojo, orçamento CPU e separação por
  cena antes de calibrar/treinar. Conjunto pequeno não mede mAP ou produtividade.
- main/f5b1f18 e tags locais v0.1.0/v0.2.0 preservados. Sem commit/tag/push. Incrementos
  anteriores e `h origin main` intactos. Segurança frontend/aceite VM continuam pendentes.

## SE-04 / PUB-01 a PUB-04 — comparação pública offline

- Retomado o pedido de melhoria com imagens da internet. Seis referências Commons
  com autoria/licença/hash fixos, separadas das fotos privadas. Sem fine-tuning,
  captura, uso da VM, banco remoto, novos pesos ou publicação Git.
- `IntelYoloDetector` agora aceita `resize_mode="letterbox"`, preservando proporções
  e invertendo padding; `stretch` continua default nos consumidores de câmera.
- Nova evidência geométrica experimental conta pessoa/laptop/mouse/teclado e
  proximidade. `activity_state` sempre inconclusivo; falha não vira zero. Sem celular.
- CLI `scripts/evaluate_workstation_signals.py` compara ambos usando um runner CPU,
  mesmas fontes/limiar e pastas novas. Downloads somente com `--download`, hashes
  antes da inferência, limite de 16 MiB, créditos preservados mesmo na falha parcial.
- Execução real: 6 imagens, 5 repetições, limiar 0,25. Stretch: 5 pessoa/5 laptop/
  0 mouse/1 teclado; letterbox: 5/4/0/1. Uma duplicação aparente de laptop removida
  na foto 05; laptop da foto 04 e mouse da 06 perdidos por ambos. Não são métricas GT.
- Medianas detect: 31,509 / 31,861 ms no PC; não comprovam FPS de vídeo/VM. Relatório
  e 18 prévias em data/evaluations/public-workstations-validated-20260915 (fora do Git).
- Fonte detalhada: docs/workstation-evaluation.md e
  phases/se-04-activity-observation/STEP-04-PUBLIC-EVALUATION-VERIFICATION.md.
- `AGENTS.md` criado com regras permanentes para a pasta levada a outro PC.
- Validação final: **468 testes Python + 126 subtestes**; Ruff e formato em 9 arquivos
  do incremento; Mypy nos 5 arquivos de código/CLI. A suíte inclui mudanças anteriores
  do worktree, não equivale a um snapshot publicado. 69 testes novos nesta etapa.
- Estado Git verificado: main/HEAD f5b1f18; tags locais v0.1.0 **e v0.2.0** apontam
  para esse commit. Não mover/recriar tags; os incrementos posteriores estão locais.
  Preservar `h origin main` e demais alterações preexistentes. Não foi consultado remoto.
- Próximo: revisão humana/dataset representativo, rótulos de ações observáveis,
  clipes autorizados e critérios antes de treino/promoção. Etapa privada 3D segue pausada.
- Pendência distinta anterior: mitigação image-size local iniciada em 12/09; não foi
  retomada aqui nem revalidada no frontend. Riscos de exposição/VM continuam abertos.

As seções seguintes são checkpoints históricos; datas e contagens não são atuais.

## PERF-01 / OPS-02 — preparação local sem acesso à VM

- Escopo atual: continuar pendências locais e melhorar desempenho enquanto o usuário
  não tem acesso à VM. Nenhuma câmera, treino, implantação ou dado remoto em uso.
- Estado Git atualizado: main/HEAD f5b1f18, tag local v0.1.0 existente, criada pelo
  usuário. Histórico abaixo é datado. Não foi consultada publicação remota; preservar
  arquivo não rastreado do usuário `h origin main`, sem incluir no novo commit.
- Próximo marco preparado v0.2.0, manifests/lock coerentes, sem commit/tag/push feitos
  pelo agente. Comandos revisados em docs/versioning.md não reutilizam v0.1.0.
- Captura readinto/slot bruto/cópia apenas no consumo; sequência repetida é ignorada.
  Telemetry.tick a 1 Hz e fechamento final no shutdown; observações seguem imediatas.
- Polls do painel serializados, timeout/backoff e pausa oculta; expiração com deadline
  independente, sem relógio global 500 ms. Falhas transitórias removem análise velha
  preservando player; recusa de acesso ainda o desmonta. JPEG local com backpressure.
- Backup offline da outbox completa para destino novo privado, verify e restore
  separado de ativação, sem alteração da fila original. Ensaios só em dados sintéticos.
- CI Conda Ubuntu preparado, sem disparo no GitHub; audit alto permanece gate real.
  Instalação limpa Linux, browser/WebRTC real e VM não foram validados nesta rodada.
- Build auxiliar Sites falhou no shim npm Windows (caminho npm-prefix.js incorreto);
  fallback com o build nativo do projeto aprovado, executado via Conda smart-environment.
  Não houve alteração da instalação global ou tentativa de hospedagem.
- Evidência final Windows/Conda smart-environment: 399 testes Python + 11 subtestes
  (inclui 42 de backup, zero skips), build + 66 testes do dashboard, ESLint, TypeScript,
  Ruff do servidor/testes/benchmark e Mypy dos 10 módulos de servidor aprovados.
  YAML do workflow/perfil lido e invariantes básicos verificados; não equivale a rodar CI.
  Árvore npm válida. Audit completo reexecutado: 2 altas image-size/vinext, gate aberto.
- Microbenchmark repetido: 640x360, 150 frames x 5 amostras, chunks4KiB, mediana
  0,716041 -> 0,397766 ms/montagem, pico Python 1.405.787 -> 692.353 bytes. Somente
  montagem sintética em memória, não FPS/rede/codec/modelo nem consumo total do processo.
- Pytest usou basetemp novo fora do OneDrive devido à ACL da pasta temporária padrão;
  nenhuma permissão foi alterada nem diretório preexistente removido. Testes Node
  reexecutados com conda --no-capture-output para contornar erro cp1252 do wrapper.
- Permanecem: aceite VM/720p/30 FPS, Auth/ingestão remotos, QA visual, dependências
  residuais, retenção/custódia e avaliação do detector. Fotos/treino continuam pausados.

## VCS-01 / OPS-01 — versões preservadas e diagnóstico de instalação

- Pedido do usuário: continuar pendências e avisar quando um marco justificar nova versão,
  fornecendo comandos, sem substituir marcos anteriores. Regra permanente documentada em
  `docs/versioning.md`; não criar commit/tag/push/Release sem nova autorização explícita.
- Estado verificado: branch main, HEAD 332af86, nenhuma tag local. Trabalho SRV-01 e
  este incremento ainda no worktree; nenhum commit/tag/push feito. Tags remotas não
  consultadas; guia exige conferi-las antes de criar a primeira tag proposta v0.1.0.
- `CHANGELOG.md` registra v0.1.0 como PREPARADO, NÃO PUBLICADO, marco de desenvolvimento.
  Manifests já estão em 0.1.0. Futuras correções/features deverão ter novas entradas/tags,
  sem --force, retag ou alteração destrutiva da cópia atual para consultar código antigo.
- Novo `python -m app.server --preflight [--json]` verifica Conda, Python, dependências,
  integridade do modelo e presença dos executáveis; --config opcional verifica formato
  e permissões aparentes. Sem rede/câmera/inferência/subprocessos/criação de SQLite.
  Não ter falhas não equivale a conectividade, escrita real, segurança ou teste na VM.
- Corrigidos erros de tipos TOML e inicialização do Runtime que escapavam como traceback;
  diagnóstico de executável inacessível agora gera falha sanitizada. 19 regressões novas.
- Python: 341 testes + 11 subtestes; dashboard: build + 60 testes reexecutados. Ruff e
  Mypy aprovados nos módulos do servidor (9 arquivos). Preflight real no Conda Windows
  encontrou as dependências/artefatos; configuração remota permaneceu não verificada.
- Novo aviso de sharp gerou baseline de 6 altas. Correção complementar: override
  limitado ao Miniflare instalado resolve sharp 0.35.4 e binários; pais preservados.
  Cinco testes adicionais comprovam versões corrigidas, codecs e integração Images
  local. Audit final: 2 altas image-size/vinext, nenhuma crítica; exposição pública
  continua sem aprovação. ESLint/TypeScript/árvore npm e ci dry-run aprovados.
  Instalação limpa e execução nativa Linux permanecem pendentes. Ver relatório atualizado.
- Próximos passos: usuário guardar marco v0.1.0 com comandos revisados; resolver/avaliar
  risco image-size antes de exposição; executar preflight e piloto
  na VM quando disponível. Fotos/treinamento continuam pausados; não reiniciar bootstrap.

## SRV-01 — processamento Ubuntu implementado; comissionamento pendente

- Arquitetura: MediaMTX 1.20.1 em loopback para RTSP/WHEP, mídia UDP somente LAN/VPN;
  Caddy HTTPS encaminha para gateway Python autenticado com JWT Supabase e membership.
  Não houve deploy, acesso à VM, captura real ou escrita no Supabase nesta entrega.
- `app.server`: 1 modelo OpenVINO CPU compartilhado, até 4 decoders com slot de frame
  único, análise padrão 2 FPS/câmera (0,2–5 configurável), stale sem contagem fictícia.
  Catálogo autorizado expira em 30 s sem atualização; fontes somente no mapa local.
- SQLite persiste minutos, episódios e outbox. Agregação distingue occupied/empty/unknown;
  entrega idempotente ignore-duplicates, backoff e dead letters preservadas. Fila cheia
  interrompe ingestão sem descartar dados silenciosamente. Sem pixels ou caixas em disco.
- Dashboard: `VITE_PROCESSING_SERVER_URL` opcional, várias transmissões autenticadas,
  caixas recentes com expiração, FPS do vídeo separado do FPS de inferência. Sem a
  variável, o monitor e piloto local existentes são preservados. `.env.local` intocado.
- Guia `docs/server-processing.md`, perfil Conda `environment.server.yml`, exemplos
  TOML/MediaMTX/Caddy/systemd em `config/server/`. Webcam via publicador e túnel SSH;
  RTSP H264 nativo; MJPEG Android convertido no publicador (CPU adicional).
- Validação local inicial: Python 322 testes + 11 subtestes; dashboard build + 55 testes,
  TypeScript e ESLint aprovados. Mypy aprovou os 8 módulos do servidor. Atualizar esta
  evidência se houver novas alterações. Ruff aprovado; OpenVINO CPU/4 threads carregou
  e inferiu frame sintético em memória. Testes não comprovam 30 FPS em Hyper-V.
- Próximo passo COM o usuário: preparar VM/IP privado, instalar perfil, copiar modelo,
  preencher secret somente no servidor/UUIDs existentes, confiar no TLS e testar padrão
  sintético. Depois uma câmera real, duas e quatro, medindo CPU/RAM/FPS/latência e ingestão.
  Alertas de dependências residuais do dashboard continuam sem aprovação de exposição pública.

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
