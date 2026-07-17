# Estado GSD

Atualizado em: 2026-07-17

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch:** `main`
- **Commit da fundação executável:** `3512e90`
- **Checkpoint de planejamento:** o commit que contém este arquivo

## Posição atual

- **Fase atual:** 1 — Fundação e ambiente
- **Plano atual:** `.planning/phases/01-foundation/PLAN.md`
- **Tarefa atual:** FND-01-05 — validar ambiente limpo/lock e fechar a Fase 1
- **Última tarefa concluída:** FND-01-04 — logging seguro, com ressalvas documentadas
- **Próxima tarefa:** instalar/fixar ferramentas dev e executar build em venv limpo
- **Progresso global:** fundação mínima executável; nenhuma função biométrica entregue

## O que funciona

- Git local, estrutura de planejamento e pesquisas iniciais.
- Runtime Python 3.12.13 empacotado no workspace (fora do `PATH`).
- Configuração validada, uma câmera como limite padrão e diagnóstico somente leitura.
- Logging JSON com allowlist, correlação, redaction, rotação e fronteira fatal.
- Vinte e seis testes unitários stdlib e compilação do código.
- Pesquisa oficial para Supabase/pgvector/Storage e ESP32 persistida.

## O que não funciona/ainda não existe

- Captura, modelo facial, cadastro, reconhecimento, banco, API, GUI, autenticação,
  sincronização, alertas e empacotamento.
- Ambiente dev com pytest/Ruff/mypy ainda não instalado.
- ACL explícita de arquivo de log no Windows e bootstrap persistente ainda não existem;
  stderr estruturado é o único destino usado pelo entrypoint.

## Testes

- **Aprovados:** 26/26 unittest; compileall; limite de linha Python; smoke doctor;
  versão CLI; configuração inválida; redaction; correlação; rotação; fallback e exceção.
- **Pendentes:** pytest, Ruff, mypy, build/instalação limpa, Python 3.11 e lockfile.

## Erros conhecidos

- `python`, `py`, `pytest`, `ruff` e `mypy` não estão disponíveis no `PATH` do sistema.
  Não é erro do projeto; usar venv ou o runtime indicado durante esta sessão.

## Bloqueios

Python de sistema/venv, lockfile e ferramentas dev faltam para fechar a Fase 1.
SEC-007 permanece em andamento para integração futura e arquivo seguro no Windows.
Retenção/base legal, escala futura, licença de pesos e prova do Supabase bloqueiam
uso biométrico real e fases posteriores correspondentes.

## Decisões abertas

- Quantidade futura de webcams/ESP32 e de pessoas; protocolos finais do ESP32.
- Windows/Linux de produção, CPU/RAM/GPU e modelos predominantes de câmera.
- Região/plano/custos/quotas/restore do Supabase e topologia final do gateway.
- Retenção, base legal/consentimento e política de snapshots.
- Modelo/pesos com licença compatível com eventual uso comercial.

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

> Leia os cinco arquivos GSD obrigatórios e continue por FND-01-05: criar ambiente
> limpo, fixar dependências/ferramentas, executar gates e registrar os gaps. Não ative
> arquivo de log no Windows nem Supabase/biometria como produção sem os gates abertos.
