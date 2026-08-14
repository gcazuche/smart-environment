# Estado GSD — Smart Environment

Atualizado em: 2026-08-14

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch no início de SE-01:** `main`
- **Fundação técnica histórica:** concluída; código preservado
- **Checkpoint funcional atual:** dashboard visual antecipado implementado

## Posição atual

- **Etapa concluída:** SE-01 — Rebaseline Smart Environment
- **Etapa atual:** protótipo antecipado da SE-06 — Dashboard web
- **Plano atual:** `.planning/phases/se-02-dashboard-prototype/PLAN.md`
- **Tarefa atual:** revisão visual do dashboard; depois retomar SEB-017
- **Autorização:** webcam e detecção local autorizadas pelo usuário em 2026-08-14
- **Plano antigo:** `.planning/phases/02-database/` superado e somente histórico

## Resultado de SE-01

- Produto redefinido como gestão inteligente de ambientes.
- MVP fixado em uma webcam, frames transitórios, contagem sem identificação, evento
  agregado, Supabase e dashboard web.
- “Desempenho” limitado ao ambiente; distração/produtividade individual excluídas.
- Reconhecimento facial, embeddings, pgvector, vivacidade e PySide6 retirados do baseline.
- Roadmap incremental, requisitos, riscos, testes, stack e ADRs realinhados.
- Nenhum código funcional, dependência, banco, câmera ou serviço externo foi alterado.

## Mudança de direção em 2026-08-14

- O usuário esclareceu que “desempenho” inclui estimar se a pessoa aparenta estar
  trabalhando ou relaxando.
- A primeira implementação foi antecipada para webcam e detecção de pessoas antes de
  Supabase; atividade observável permanece para SE-04.
- A classificação terá estado `inconclusivo`, regras por contexto e uso não punitivo.
- Por decisão do usuário, a melhoria do detector foi pausada após o primeiro protótipo;
  o dashboard visual foi antecipado e a detecção será retomada depois.

## O que funciona hoje

- Ambiente Conda isolado `smart-environment` com Python 3.12.13 e `environment.yml`;
  nenhum comando de instalação desta migração foi direcionado ao `base`.
- Configuração mínima, comando `doctor`, logging JSON seguro e tratamento de exceções.
- OpenCV/NumPy fixados no lock; câmera com fallback, CLI, loop local, caixas e contagem.
- 44 testes aprovados em Python 3.12, junto com Ruff, mypy e compilação.
- Webcam abriu por DirectShow em smoke autorizado pelo Conda, processou 30 frames em
  memória, atingiu máximo de uma pessoa e foi liberada; qualidade ampla segue pendente.
- A contagem inspecionada em `data/` permaneceu 5 antes e depois.
- Dashboard responsivo em `dashboard/`, com visão geral, todas as câmeras, detalhe da
  webcam, ambientes, indicadores e alertas usando somente dados simulados.
- Build Vinext, lint ESLint e dois testes de renderização aprovados.

## O que não existe

- Schema, migrações, projeto Supabase, Auth, RLS ou conexão PostgreSQL.
- Outbox SQLite, API, sincronização ou autenticação da aplicação.
- Detector validado para pessoa sentada/corpo parcial, agregador ou métricas de qualidade.
- Integração do dashboard com câmera/API/Supabase, autenticação e dados persistentes.
- Alertas, múltiplas câmeras, ESP32, automação ou piloto.

## Bloqueios antes de dados reais

- finalidade detalhada, controlador, operadores de tratamento, encarregado e local autorizado;
- base legal/RIPD/avisos aplicáveis e áreas/horários permitidos;
- retenção, granularidade contra reidentificação e processo de direitos;
- região/plano/quotas/custo/backup/restore do Supabase;
- detector/pesos/licença comercial e critérios de qualidade.

## Decisões abertas

- framework web e biblioteca de gráficos;
- detector de pessoas e runtime de inferência;
- granularidade temporal/espacial do evento;
- estratégia Realtime versus polling;
- metas de FPS, latência, capacidade e custo;
- protocolo/modelos de câmeras futuras/ESP32;
- momento e estratégia para migrar o nome técnico `multicam`.

## Como retomar

1. Ler `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `DECISIONS.md` e este arquivo.
2. Revisar o protótipo em `dashboard/` e registrar ajustes objetivos.
3. Após aprovação visual, retomar `se-02-person-detection`, item SEB-017.
4. Não conectar dados reais, Supabase ou classificar atividade sem autorização própria.

## Prompt de retomada sugerido

> Revise o protótipo visual do dashboard. Se estiver aprovado, retome somente o item
> SEB-017 de detecção de corpo parcial, sem salvar frames, conectar Supabase ou
> classificar trabalho/relaxamento ainda.
