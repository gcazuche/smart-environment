# Fase 1 — Resumo

Status: **concluída com ressalvas operacionais documentadas**.

## Objetivo alcançado

- Contexto GSD, requisitos, roadmap, decisões, riscos e pesquisas persistidos.
- Pacote Python modular com configuração validada e CLI `doctor` somente leitura.
- Logging JSON com allowlist, correlação, redaction, rotação POSIX e fronteira fatal.
- `uv.lock`, pré-requisito verificado `uv==0.11.17` e build backend fixado.
- Pytest, Ruff, format-check, mypy strict, unittest, compileall, build e instalação
  limpa aprovados.
- **28/28 testes** aprovados em Python 3.11.15 e 3.12.13.
- Webcam integrada confirmada por smoke de um frame em memória via DirectShow, sem
  persistência ou biometria.

## Decisões consolidadas

Python 3.11–3.12 é a matriz inicial. O motor facial será substituível e nenhum peso
será baixado antes de validar licença para o uso pretendido. Supabase é a preferência
central ainda sujeita a prova de conceito; SQLite permanece a primeira fronteira local
e offline. Frames completos são opt-in e vinculados a eventos, nunca gravação contínua
por pressuposto.

No Windows, logging em arquivo falha fechado e retorna a stderr porque `os.chmod` não
configura DACL. Um adaptador Win32 e diretório fora do repositório/OneDrive serão
necessários antes de ativá-lo.

## Ressalvas transferidas

- PRIV-001 foi fechado somente como gate negativo: o sistema não possui caminho de
  biometria real e deverá revalidar finalidade/base legal antes do cadastro da Fase 6.
- SEC-007 continua em andamento para integração das camadas futuras e DACL Windows.
- CAM-007 continua pendente: o smoke real não substitui adaptador, fonte simulada,
  timeout/reconexão e testes automatizados da Fase 4.
- Retenção, base legal, escala, hardware de produção, metas biométricas e licença dos
  pesos continuam `unspecified`.
- Nenhum serviço Supabase/PostgreSQL, modelo facial, GPU, API ou GUI foi validado.

## Próxima fase

A Fase 2 foi aberta apenas para configuração e persistência local. O primeiro slice
implementável é um runtime SQLite preguiçoso e transacional, sem criar tabelas
biométricas, conectar rede ou aceitar DSN arbitrária. O encerramento da fase continuará
bloqueado até a prova de conceito isolada de Supabase/PostgreSQL/pgvector/Storage.

Consulte `VERIFICATION.md` para comandos e evidências e
`.planning/phases/02-database/PLAN.md` para a próxima tarefa atômica.
