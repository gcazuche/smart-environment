# Fase 1 — Contexto

## Objetivo

Criar uma base Python executável, segura por padrão e testável, acompanhada pelos
artefatos GSD necessários para retomar o trabalho sem depender da conversa.

## Requisitos

- TEST-001: testes automatizados e evidência.
- SEC-001: configuração sem segredos no repositório.
- SEC-007: tratamento de exceções e logs seguros (ainda pendente).
- Os demais requisitos permanecem planejados, não implementados.

## Estado atual de entrada

- Repositório Git vazio, branch `main`, sem commits.
- Python/pytest/ruff/mypy não estão no `PATH` do sistema.
- Runtime empacotado disponível: Python 3.12.13.
- Escala, hardware, SO de produção, banco/hospedagem e retenção: `unspecified`.

## Decisões relevantes

- Monólito modular preparado para cliente/servidor.
- Baseline Python 3.12 e suporte alvo a 3.11.
- Nenhum modelo/peso facial é baixado nesta fase.
- Nenhuma dependência externa é necessária para o smoke test inicial.

## Restrições

- Não criar captura, reconhecimento, banco, API ou GUI prematuramente.
- Não armazenar segredos, imagens reais ou embeddings reais.
- Não alegar teste de hardware.

## Arquivos da fase

- `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `main.py`.
- `app/` com configuração e diagnóstico.
- `tests/` com testes unitários stdlib.
- `.planning/` com especificação e checkpoint.

## Funcionalidades que não podem ser quebradas

Após a tarefa funcional:

- `python -m app doctor --json` deve retornar JSON e código coerente.
- `python -m unittest discover -s tests -v` deve funcionar sem serviços externos.
- mensagens de diagnóstico não podem expor valores sensíveis.
