# Estado GSD

Atualizado em: 2026-07-17

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch:** `main`
- **Commit da fundação executável:** `b762507`
- **Checkpoint de planejamento:** o commit que contém este arquivo

## Posição atual

- **Fase atual:** 1 — Fundação e ambiente
- **Plano atual:** `.planning/phases/01-foundation/PLAN.md`
- **Tarefa atual:** FND-01-04 — Adicionar logging e tratamento global seguros
- **Última tarefa concluída:** FND-01-03 — Diagnóstico executável
- **Próxima tarefa:** FND-01-05 — validar ambiente limpo/lock e fechar a Fase 1
- **Progresso global:** fundação mínima executável; nenhuma função biométrica entregue

## O que funciona

- Git local, estrutura de planejamento e pesquisas iniciais.
- Runtime Python 3.12.13 empacotado no workspace (fora do `PATH`).
- Configuração validada e diagnóstico somente leitura via `python -m app doctor`.
- Treze testes unitários stdlib e compilação do código.

## O que não funciona/ainda não existe

- Captura, modelo facial, cadastro, reconhecimento, banco, API, GUI, autenticação,
  sincronização, alertas e empacotamento.
- Ambiente dev com pytest/Ruff/mypy ainda não instalado.
- Logging estruturado/redaction e fronteira global de exceções ainda não implementados.

## Testes

- **Aprovados:** 13/13 unittest; compileall; parsing TOML; smoke doctor JSON/humano;
  versão CLI; rejeição de configuração inválida; busca passiva de padrões de segredos.
- **Pendentes:** pytest, Ruff, mypy, build/instalação limpa, Python 3.11 e lockfile.

## Erros conhecidos

- `python`, `py`, `pytest`, `ruff` e `mypy` não estão disponíveis no `PATH` do sistema.
  Não é erro do projeto; usar venv ou o runtime indicado durante esta sessão.

## Bloqueios

SEC-007, Python de sistema/venv e ferramentas dev faltam para fechar a Fase 1.
Decisões de escala/licença/implantação bloqueiam fases posteriores de visão, dados e
distribuição.

## Decisões abertas

- Quantidade inicial/futura de câmeras e pessoas.
- Windows/Linux de produção, CPU/RAM/GPU e tipos predominantes de câmera.
- PostgreSQL local versus Supabase e topologia de rede.
- Retenção, base legal/consentimento e política de snapshots.
- Uso comercial ou não, necessário para licenças de modelos/pesos.

## Arquivos importantes

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/DECISIONS.md`
- `.planning/ARCHITECTURE.md`
- `.planning/phases/01-foundation/PLAN.md`

## Comandos para continuar

```powershell
Get-Content .planning/PROJECT.md, .planning/REQUIREMENTS.md,
  .planning/ROADMAP.md, .planning/STATE.md, .planning/DECISIONS.md
git status --short
```

## Prompt de retomada sugerido

> Leia os cinco arquivos GSD obrigatórios, confirme as respostas de escala/hardware/
> banco/retenção e continue pela primeira tarefa não concluída da Fase 1, executando e
> registrando os testes antes de avançar.
