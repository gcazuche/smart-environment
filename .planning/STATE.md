# Estado GSD — Smart Environment

Atualizado em: 2026-08-14

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch no início de SE-01:** `main`
- **Fundação técnica histórica:** concluída; código preservado
- **Checkpoint funcional atual:** primeiro incremento de SE-02 implementado

## Posição atual

- **Etapa concluída:** SE-01 — Rebaseline Smart Environment
- **Etapa atual:** SE-02 — Câmera e detecção local de pessoas
- **Plano atual:** `.planning/phases/se-02-person-detection/PLAN.md`
- **Tarefa atual:** SEB-017 — avaliar qualidade e detector de corpo parcial
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

## O que funciona hoje

- Ambiente reproduzível com `uv.lock` e Python 3.11/3.12.
- Configuração mínima, comando `doctor`, logging JSON seguro e tratamento de exceções.
- OpenCV/NumPy fixados no lock; câmera com fallback, CLI, loop local, caixas e contagem.
- 44 testes aprovados em Python 3.12, junto com Ruff, mypy e compilação.
- Webcam abriu por DirectShow em smoke autorizado, processou 30 frames em memória e
  foi liberada. A amostra teve zero detecções; qualidade para corpo parcial está pendente.
- A contagem inspecionada em `data/` permaneceu 5 antes e depois.

## O que não existe

- Schema, migrações, projeto Supabase, Auth, RLS ou conexão PostgreSQL.
- Outbox SQLite, API, sincronização ou autenticação da aplicação.
- Detector validado para pessoa sentada/corpo parcial, agregador ou métricas de qualidade.
- HTML/CSS/JavaScript do dashboard, gráficos, sustentabilidade ou patrimônio.
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
2. Continuar somente pelo plano `se-02-person-detection`, item SEB-017.
3. Avaliar detector de corpo parcial com licença comercial compatível e material autorizado.
4. Não criar schema, conectar Supabase ou classificar atividade nesta etapa.

## Prompt de retomada sugerido

> Continue somente pela Etapa SE-02 de câmera e detecção local. Implemente o próximo
> item do plano com fonte simulada e webcam autorizada, sem salvar frames, sem Supabase
> e sem classificar trabalho/relaxamento ainda.
