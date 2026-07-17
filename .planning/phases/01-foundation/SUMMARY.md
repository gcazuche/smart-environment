# Fase 1 — Resumo

Status: **em andamento — logging seguro concluído com ressalvas; gates finais abertos**.

## Objetivo alcançado até aqui

- Contexto GSD, requisitos, roadmap, decisões, riscos e pesquisas persistidos.
- Pacote Python modular inicial com configuração validada.
- CLI `doctor` somente leitura, com saída humana/JSON e códigos de saída.
- Logging JSON com contexto allowlist, correlação, redaction, rotação e fronteira fatal.
- Vinte e seis testes unitários stdlib, compilação e smoke tests aprovados em Python
  3.12.13.
- Contexto confirmado para uma webcam inicial, Supabase/internet preferenciais,
  expansão ESP32 e frames por evento.

## Arquivos principais

- Criados: `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `main.py`,
  `app/`, `tests/`, `.planning/` e sentinelas de `data/`.
- Modificados: não havia arquivos de aplicação anteriores.

## Decisões

Python 3.12 é baseline; motor facial é substituível; InsightFace/ONNX é somente
candidato condicionado à licença dos pesos. Supabase/PostgreSQL/pgvector central e
SQLite local são propostas; dependências reais entram por fase e lockfile.

## Limitações e dívidas

- pytest, Ruff e mypy não estão instalados; esses gates não foram executados.
- SEC-007 permanece `em andamento` porque camadas futuras ainda não usam o contexto,
  ACL explícita no Windows não foi validada e o entrypoint não ativa arquivo de log.
- Build/instalação em venv limpo, Python 3.11 e lockfile continuam pendentes.
- Nenhuma câmera, biometria, GPU, banco, API ou GUI foi testada/implementada.
- Quantidade de pessoas, hardware, retenção e respostas jurídicas seguem `unspecified`.

## Como validar

Use os comandos e resultados em `VERIFICATION.md`. A fase não está concluída até os
gates restantes passarem e as lacunas P0 de contexto serem tratadas.

## Próxima fase

Ainda não autorizada: primeiro concluir FND-01-05 e o aceite da Fase 1; as ressalvas de
SEC-007 devem ser resolvidas antes de habilitar persistência de logs em produção.
