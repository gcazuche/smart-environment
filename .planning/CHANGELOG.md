# Changelog GSD

## 2026-08-27 — Dataset autorizado pré-rotulado sem celular

- As 62 fotos autorizadas foram reencodadas localmente com nomes neutros e remoção de
  metadados; 66 regiões de face, 166 zonas superiores de pessoa e 64 telas foram
  redigidas, enquanto o ZIP original permaneceu intocado.
- Auditoria visual separou oito rajadas sem vazamento entre splits e selecionou 33 frames
  representativos: 22 treino, 5 validação e 6 teste.
- O mapa YOLO contém somente `person`, `laptop`, `mouse` e `keyboard`; não há celular real,
  `cell_phone` não aparece no YAML nem nos arquivos de rótulo e ficará para coleta futura.
- O Intel YOLO26 gerou 27 pré-rótulos de pessoa, 2 de laptop, 12 de mouse e 21 de teclado.
  A inspeção confirmou omissões e falsos positivos, por isso o dataset segue
  `ready_for_training=false` e ainda não houve fine-tuning.
- Fingerprints vinculam a divisão às imagens auditadas; JPEGs, hashes, cenas e IDs foram
  verificados. O caminho está sob OneDrive, então eventual sincronização do Windows deve
  ser confirmada antes de alegar que os derivados não saíram do computador.
- 115 testes e 11 subtestes, Ruff, formatação, mypy e compileall passaram no Conda
  `smart-environment`.

## 2026-08-27 — Ambientes agrupam seus dispositivos

- A ação **Ver ambiente** deixou de ser decorativa e agora abre uma visão dedicada do
  ambiente selecionado.
- A visão reúne todas as câmeras que compartilham o mesmo ambiente, com total de
  dispositivos, câmeras online e pessoas detectadas no momento.
- Cada câmera continua com sua prévia anotada e pode ser aberta em seu detalhe individual;
  a navegação também oferece retorno para a lista de ambientes.
- Build Vinext, ESLint, testes web e 99 testes Python passaram após o ajuste.

## 2026-08-27 — Marca e linguagem da interface

- A marca do cabeçalho e da tela de acesso deixou de usar o gráfico de barras padrão;
  agora há um espaço neutro reservado para inserir a logo definitiva.
- A linguagem visível do dashboard foi revisada para retirar referências a protótipo,
  contexto acadêmico, demonstração e dados simulados.
- Build Vinext, ESLint e os testes de renderização passaram após a revisão.

## 2026-08-27 — Visão geral focada em indicadores

- O bloco de prévia “Suas câmeras” foi retirado da página inicial para deixar o resumo
  mais limpo e coerente.
- A lista completa, prévias anotadas e detalhes dos dispositivos continuam disponíveis
  na seção **Câmeras** da navegação.
- Build Vinext, ESLint e os testes de renderização passaram após o ajuste.

## 2026-08-27 — Acesso demonstrativo e perfil do dashboard

- A rota principal agora inicia em uma tela de login antes de exibir o painel.
- O protótipo aceita e-mail válido e senha mínima de seis caracteres, guarda somente
  metadados temporários em `sessionStorage` e nunca persiste a senha.
- O perfil do administrador deixou de ser decorativo: abre um modal com os dados da
  sessão e oferece logout; em telas pequenas há um atalho equivalente no cabeçalho.
- O polling do agente local só é ativado enquanto há sessão, e o logout limpa a sessão e
  interrompe as leituras do dashboard.
- Supabase Auth, backend remoto, expiração/revogação e permissões continuam pendentes;
  esta etapa é exclusivamente um fluxo de UX para o TCC.
- Build Vinext, ESLint e os dois testes de renderização passaram.

## 2026-08-23 — Referências sintéticas sem rosto

- Seis cenas independentes foram geradas para o TCC com pessoas fictícias vistas de
  costas ou mesa vazia; nenhum rosto, identidade, marca ou fotografia de terceiro entrou.
- Contrato fixa hashes, dimensões, proveniência e objetos esperados por cena; pixels,
  manifest, relatórios e prévias permanecem fora do Git.
- No limiar 0,25, laptop apareceu em 4/4 cenas esperadas e celular em 3/4; a cena ambígua
  perdeu o celular e produziu uma caixa duplicada/falsa de laptop. Média: 41,4 ms.
- Em 0,10, o quarto celular surgiu com falsos sinais adicionais, portanto o limiar oficial
  não foi reduzido e o sinal ainda não classifica comportamento.
- Webcam, monitor contínuo, tracking, pose, classificador, dashboard e Supabase não foram
  abertos ou integrados nesta etapa.
- 99 testes e 11 subtestes, Ruff, formatação, mypy strict, compileall, build e `pip check`
  passaram no Conda `smart-environment`.

## 2026-08-22 — Smoke offline de objetos de escritório

- O núcleo YOLO26/OpenVINO foi generalizado com lista explícita de classes, preservando o
  adaptador de pessoas e sem baixar novo modelo ou dependência.
- Novo detector permite apenas `laptop`, `mouse`, `keyboard` e `cell_phone`; saídas fora
  da lista falham fechado e nunca geram rótulo de atividade.
- Nas três referências públicas, encontrou dois laptops corretos, com média de 43,2 ms;
  não encontrou o celular visível. O diagnóstico em 0,10 produziu o mesmo resultado.
- Relatório JSON e três prévias anotadas foram gravados em `data/evaluations/`, fora do
  Git. Webcam, celular, monitor contínuo, dashboard e Supabase não foram abertos/alterados.
- 97 testes e 11 subtestes, Ruff, formatação, mypy strict, compileall, build e `pip check`
  passaram no Conda `smart-environment`.

## 2026-08-22 — Referências reais de estações de trabalho

- Três imagens de escritórios ocupados do dataset específico no Hugging Face foram
  baixadas, revisadas visualmente e registradas com origem, licença, dimensões e SHA-256.
- Preparador reproduzível usa HTTPS restrito, download limitado, hashes fixados, validação
  JPEG e falha fechada; pixels e manifest local permanecem fora do Git.
- Uma seleção automática por coocorrência do Open Images foi rejeitada e removida depois
  que a inspeção revelou cenas sem contexto real de estação de trabalho.
- A licença CC-BY-NC-SA-4.0 limita o material ao TCC não comercial. Três imagens não
  sustentam treinamento, métrica representativa nem rótulo de produtividade/distração.
- 92 testes e 11 subtestes, Ruff, formatação, mypy strict, compileall, build e `pip check`
  passaram no Conda `smart-environment`.

## 2026-08-22 — Área da estação de trabalho por câmera

- Região retangular normalizada e validada adicionada sem dependência nova, funcionando
  de forma consistente em resoluções diferentes.
- Webcam e celular aceitam áreas independentes; o padrão neutro cobre o frame inteiro
  até que cada enquadramento seja calibrado.
- Prévia local desenha a área e indica pessoas dentro/fora por sobreposição geométrica;
  a API adiciona somente geometria e contagem agregada volátil.
- Estar dentro ou fora da área não classifica atividade, distração ou produtividade.
- 87 testes e 11 subtestes, Ruff, formatação, mypy strict, compileall, build local e
  `pip check` passaram no Conda `smart-environment`.
- Dashboard permaneceu compatível: ESLint, build Vinext e 2 testes de renderização passaram.

## 2026-08-22 — Contrato inicial de atividade observável

- Contexto inicial limitado a uma pessoa em estação fixa de escritório com computador.
- Cinco estados estáveis definidos: atividade compatível, uso aparente de celular, pausa
  aparente, ausente e inconclusivo.
- Política `office-computer` versionada registra janela de 10 s e limiares temporais
  iniciais, todos validáveis e calibráveis sem dependência nova.
- Contrato proíbe identidade, produtividade real, ranking e punição automática; celular
  descreve somente o objeto observado e não recebe o rótulo de distração.
- Etapa não abriu câmera, classificou frames, alterou dashboard ou persistiu eventos.
- 77 testes e 5 subtestes, Ruff, formatação, mypy strict, compileall, build local e
  `pip check` passaram no Conda `smart-environment`.

## 2026-08-18 — Vídeo anotado no dashboard local

- O agente mantém somente o JPEG anotado mais recente de cada câmera em memória e o
  substitui continuamente; nenhum writer de imagem foi adicionado.
- Endpoints de frame usam loopback, `no-store`, IDs validados e exigem origem ou
  referência do dashboard local; acesso sem esse contexto recebe 403.
- Os cartões e detalhes das câmeras agora exibem vídeo real com as caixas verdes do
  detector quando abertos em `localhost`.
- Smoke real retornou JPEG para webcam e celular, com ambas as fontes online; a versão
  publicada continua sem vídeo real até existir backend remoto autenticado.

## 2026-08-18 — Dashboard preparado para computador e celular

- Fonte OpenCV de rede privada adicionada para MJPEG/RTSP do celular, com rejeição de
  endereços públicos e credenciais embutidas.
- Agente multicâmera local processa webcam e celular com Intel/OpenVINO e entrega ao
  dashboard somente contagens, estado, backend e latência; frames não saem do processo.
- Dashboard passou a listar os dois dispositivos e consultar a API apenas em localhost.
- 68 testes Python, Ruff, mypy, build Vinext, ESLint e testes web foram aprovados.
- Terceira versão privada do dashboard publicada após alinhar o contrato da API.
- No teste físico, webcam/DirectShow e celular/MJPEG ficaram simultaneamente online; a
  leitura observada indicou uma pessoa em cada fonte e nenhum frame foi persistido.

## 2026-08-18 — Intel Person Detection integrado para comparação

- YOLO26n FP16 via OpenVINO entrou como detector experimental selecionável por
  `multicam camera --detector intel`; NanoDet permanece como padrão e fallback.
- Ambiente Conda recebeu versões fixadas de OpenVINO, Ultralytics e cliente Hugging Face.
- Revisão Intel, fontes, peso e artefatos exportados têm SHA-256 verificados; nada entrou
  no Git em `models/`.
- Em uma amostra pública indicada pela Intel, o novo detector retornou duas pessoas e
  média de 32,1 ms; NanoDet retornou três caixas e 90,1 ms. Não há conclusão de acurácia.
- 60 testes, Ruff e mypy strict passaram. A webcam não abriu nos backends Windows nesta
  tentativa; o smoke de hardware deve ser repetido quando o dispositivo estiver livre.

## 2026-08-14 — NanoDet oficial integrado

- NanoDet-m-plus-1.5x do OpenCV/Hugging Face substitui HOG/cascade como padrão da CLI.
- Peso e licença têm revisão e SHA-256 fixados; download reprodutível foi adicionado.
- Inferência roda localmente em OpenCV DNN/CPU e descarta classes diferentes de pessoa.
- Limiar 0,35 foi mantido; 0,30 e 0,25 geraram mais caixas e foram rejeitados.
- Frames permaneceram em memória e o dashboard/Supabase não foram conectados.

## 2026-08-14 — Detecção de corpo parcial retomada

- Detector híbrido combina HOG de corpo inteiro e cascade upper-body do OpenCV.
- Equalização em cinza, origem visual das caixas e deduplicação foram adicionadas.
- 48 testes passaram; smoke de 30 frames terminou com uma pessoa e máximo observado de
  duas, mantendo `data/` em 5 → 5 arquivos.
- O resultado confirma presença e lifecycle, não precisão; falsos sinais e latência
  ainda precisam de dataset autorizado/sintético.

## 2026-08-14 — Dashboard privado publicado

- Primeira versão do dashboard Smart Environment publicada com acesso privado.
- A publicação reúne visão geral, todas as câmeras, detalhe da webcam, ambientes,
  indicadores e alertas com dados explicitamente simulados.
- Nenhuma webcam, stream, API ou instância Supabase foi conectada nesta entrega.

## 2026-08-14 — Dashboard visual antecipado

- Melhoria do detector pausada por decisão do usuário para antecipar a experiência web.
- Dashboard responsivo criado em React/TypeScript com visão geral, lista de todas as
  câmeras, detalhe da webcam, ambientes, indicadores e alertas.
- Inclusão de busca/filtro de câmera, modal de novos dispositivos e estados futuros
  para câmera IP e gateway ESP32.
- Dados, gráficos, eventos e prévia visual são simulados; nenhum frame, API, Auth,
  Supabase ou persistência foi conectado.
- Build Vinext, ESLint e dois testes de renderização aprovados; QA visual humana pendente.

## 2026-08-14 — Ambiente oficial migrado para Conda

- Ambiente isolado `smart-environment` criado com Python 3.12.13; nenhum comando de
  instalação ou atualização desta migração foi direcionado ao `base`.
- `environment.yml` tornou-se a fonte ativa de criação/sincronização do ambiente.
- OpenCV, NumPy, pytest, coverage, Ruff, mypy e build foram instalados no novo ambiente.
- Comandos ativos do README e da estratégia de testes passaram a usar Conda; `.venv` e
  `uv.lock` permanecem apenas como evidência histórica, não como workflow atual.
- Todos os gates passaram no Conda; smoke de 30 frames detectou no máximo uma pessoa
  e manteve a contagem inspecionada em `data/` em 5 → 5.

## 2026-08-14 — Primeiro protótipo de câmera e detecção (SE-02)

- OpenCV 4.13.0 e NumPy 2.3.5 adicionados ao lock.
- Fonte de webcam com fallback Windows, validação de frame e liberação determinística.
- Detector HOG substituível, caixas, contagem e janela local; nenhum writer ou cliente
  de rede foi adicionado ao caminho de frames.
- CLI `multicam camera` adicionada, com modo invisível obrigatoriamente limitado.
- 44 testes automatizados cobrem câmera fake, fallback, 0/1/N, loop, encerramento e CLI.
- Smoke autorizado abriu a webcam via DirectShow e processou 30 frames; zero pessoas
  foram detectadas nessa amostra, então a qualidade para corpo parcial segue pendente.
- Nas tentativas inspecionadas, a contagem de arquivos em `data/` permaneceu 5 → 5.

## 2026-08-11 — Rebaseline Smart Environment (SE-01)

- Objetivo alterado de câmeras com reconhecimento facial para gestão inteligente de
  ambientes, ocupação, sustentabilidade, recursos e patrimônio.
- MVP definido como uma webcam autorizada, frames transitórios, detecção/contagem sem
  identificação, evento agregado, API/Supabase e dashboard HTML/CSS/JavaScript.
- “Desempenho” limitado ao desempenho operacional do ambiente; reconhecimento facial,
  distração, emoção, produtividade individual, áudio e punição automatizada retirados.
- Arquitetura, stack, requisitos, roadmap, backlog, riscos, testes, ADRs, README e
  estado foram realinhados; antiga Fase 2 marcada como superada.
- Fundação Python, configuração, logging, lockfile, testes e evidência da webcam foram
  preservados; pacote/CLI `multicam` permanece como nome técnico legado.
- Nenhum código funcional, dependência, banco, câmera ou serviço externo foi alterado.
- Próxima etapa possível: SE-02, ainda não autorizada; primeiro gate é a matriz de
  finalidades, dados e responsáveis.

## 2026-07-17 — Fase 1 concluída e Fase 2 aberta

- Ambiente `.venv` recriado a partir de `uv.lock`, com `uv==0.11.17` como pré-requisito
  verificado; build backend fixado em `setuptools==83.0.0` e `wheel==0.47.0`.
- Corrigidos isolamento do logger sob pytest, tipo de `_open`, falso positivo S105,
  imports, formatação e cache pytest com ACL incompatível.
- Logging em arquivo no Windows agora falha fechado, sem criar caminho, até existir
  um adaptador DACL validado.
- `configure_secure_logging` aceita apenas `multicam`/`multicam.*`; logger do host foi
  coberto por regressão e mantém seus handlers intactos.
- **28/28** testes aprovados em Python 3.11.15 e 3.12.13; Ruff, format-check, mypy,
  unittest, compileall, build, wheel limpo, compatibilidade e busca passiva local por
  padrões de segredos aprovados.
- Webcam integrada validada em spike autorizado: MSMF não abriu; DirectShow leu um
  frame 640×480 em memória e liberou o dispositivo; nenhuma imagem/arquivo novo foi
  criado em `data/`.
- Fase 1 encerrada com ressalvas operacionais; Fase 2 aberta por DB-02-01.
- Próxima tarefa: DB-02-02, runtime SQLite local e transacional, sem biometria ou rede.

## 2026-07-17 — Contexto de implantação e logging seguro

- Escopo confirmado: uma webcam integrada na primeira versão, múltiplas
  webcams/ESP32 no futuro, internet e Supabase preferenciais, operação offline e
  frames de eventos; postura de licenças comerciais para o TCC.
- Pesquisa oficial de Supabase/PostgreSQL/pgvector/Storage e ESP32 persistida, sem
  declarar prova de conceito, hardware ou serviço real como validados.
- Limite padrão alterado de quatro para uma câmera; capacidade futura segue
  configurável e limitada.
- Logging JSON implementado com eventos fixos, `SecureLogContext`, correlação,
  redaction de credenciais/PII, rotação, fallback e fronteira global de exceções.
- Tracebacks não persistem mensagem bruta ou caminho; arquivo opcional registra tipos,
  hash da origem, função e linha. Permissões POSIX são reaplicadas após rotação.
- Revisão independente não encontrou bloqueador de código após as correções.
- **26/26** testes stdlib e `compileall` aprovados; ACL Windows, file sink real,
  pytest/Ruff/mypy, venv limpa e lockfile permanecem pendentes.

## 2026-07-17 — Inicialização

- Repositório inventariado: Git vazio, branch `main`, sem commits.
- Requisitos recebidos e lacunas de escala/hardware/implantação registradas.
- Planejamento, pesquisa, arquitetura, riscos e estratégia de testes iniciados.
- Fase 1 definida como fundação mínima, sem captura ou biometria.
- Pacote Python, configuração validada e comando `doctor` implementados.
- Treze testes unitários, compilação, parsing TOML e smoke tests aprovados em Python
  3.12.13; gates dependentes de pytest/Ruff/mypy permanecem pendentes.
- Revisão independente corrigiu distinção checkout/wheel, contrato Python `<3.13`,
  teste real do JSON/exit codes e rastreabilidade de SEC-007.
