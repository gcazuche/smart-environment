# Changelog GSD

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
