# Fase 1 — Pesquisa

## Ambiente local

- `git` está disponível.
- `python`, `py`, `pytest`, `ruff` e `mypy` não estão no `PATH`.
- O runtime do workspace fornece Python 3.12.13, suficiente para testes stdlib.

## Alternativas de bootstrap

### Instalar todas as dependências agora

- Vantagem: habilita lint e stack completo.
- Desvantagem: amplia superfície, demora e antecipa decisões/licenças.
- Decisão: rejeitada nesta tarefa.

### Núcleo stdlib e extras por fase

- Vantagem: smoke test offline e pequeno; dependências entram quando têm uso/teste.
- Desvantagem: pytest/Ruff/mypy ficam pendentes até preparar o ambiente dev.
- Decisão: adotada.

### Layout `app/` versus `src/`

- `src/` reduz imports acidentais da árvore de trabalho.
- `app/` corresponde à estrutura solicitada e simplifica os primeiros comandos.
- Decisão: `app/` nesta versão, com pacote instalável; reavaliar antes da expansão.

## Referências

- Comparação de stack: `../../research/TECHNOLOGY_COMPARISON.md`.
- Segurança/privacidade: `../../research/SECURITY_PRIVACY.md`.
- Ferramenta GSD: `../../research/GSD_TOOLING.md`.
