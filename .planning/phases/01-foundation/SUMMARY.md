# Fase 1 — Resumo

Status: **em andamento — primeira etapa funcional entregue**.

## Objetivo alcançado até aqui

- Contexto GSD, requisitos, roadmap, decisões, riscos e pesquisas persistidos.
- Pacote Python modular inicial com configuração validada.
- CLI `doctor` somente leitura, com saída humana/JSON e códigos de saída.
- Treze testes unitários stdlib, compilação e smoke tests aprovados em Python 3.12.13.

## Arquivos principais

- Criados: `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `main.py`,
  `app/`, `tests/`, `.planning/` e sentinelas de `data/`.
- Modificados: não havia arquivos de aplicação anteriores.

## Decisões

Python 3.12 é baseline; motor facial é substituível; InsightFace/ONNX é somente
candidato condicionado à licença dos pesos; PostgreSQL/pgvector central e SQLite
local são propostas; dependências reais entram por fase e lockfile.

## Limitações e dívidas

- pytest, Ruff e mypy não estão instalados; esses gates não foram executados.
- Logging/redaction e tratamento global de exceções (SEC-007) estão replanejados.
- Build/instalação em venv limpo, Python 3.11 e lockfile continuam pendentes.
- Nenhuma câmera, biometria, GPU, banco, API ou GUI foi testada/implementada.
- Respostas operacionais e jurídicas continuam `unspecified`.

## Como validar

Use os comandos e resultados em `VERIFICATION.md`. A fase não está concluída até os
gates restantes passarem e as lacunas P0 de contexto serem tratadas.

## Próxima fase

Ainda não autorizada: primeiro concluir FND-01-04, FND-01-05 e o aceite da Fase 1.
