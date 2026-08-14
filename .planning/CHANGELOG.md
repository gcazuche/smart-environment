# Changelog GSD

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
