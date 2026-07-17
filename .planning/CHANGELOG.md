# Changelog GSD

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
