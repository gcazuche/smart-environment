# Estado GSD — Smart Environment

Atualizado em: 2026-08-11

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch no início de SE-01:** `main`
- **Fundação técnica histórica:** concluída; código preservado
- **Checkpoint funcional atual:** nenhuma funcionalidade Smart Environment implementada

## Posição atual

- **Etapa concluída:** SE-01 — Rebaseline Smart Environment
- **Plano da etapa:** `.planning/phases/se-01-replanning/PLAN.md`
- **Próxima etapa possível:** SE-02 — Domínio, dados e Supabase seguro
- **Próxima tarefa possível:** SEB-006 — matriz de finalidades e responsáveis
- **Autorização para SE-02:** não concedida; não iniciar automaticamente
- **Plano antigo:** `.planning/phases/02-database/` superado e somente histórico

## Resultado de SE-01

- Produto redefinido como gestão inteligente de ambientes.
- MVP fixado em uma webcam, frames transitórios, contagem sem identificação, evento
  agregado, Supabase e dashboard web.
- “Desempenho” limitado ao ambiente; distração/produtividade individual excluídas.
- Reconhecimento facial, embeddings, pgvector, vivacidade e PySide6 retirados do baseline.
- Roadmap incremental, requisitos, riscos, testes, stack e ADRs realinhados.
- Nenhum código funcional, dependência, banco, câmera ou serviço externo foi alterado.

## O que funciona hoje

- Ambiente reproduzível com `uv.lock` e Python 3.11/3.12.
- Configuração mínima, comando `doctor`, logging JSON seguro e tratamento de exceções.
- 28 testes da fundação aprovados no checkpoint anterior, junto com Ruff, mypy,
  compilação e build.
- Webcam `USB2.0 HD UVC WebCam` abriu em spike autorizado por DirectShow, leu um frame
  640×480 somente em memória e foi liberada; nenhum arquivo novo apareceu em `data/`.

## O que não existe

- Schema, migrações, projeto Supabase, Auth, RLS ou conexão PostgreSQL.
- Outbox SQLite, API, sincronização ou autenticação da aplicação.
- Captura contínua, fonte simulada ou OpenCV no lock principal.
- Detector de pessoas, agregador de ocupação ou métricas de qualidade.
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
2. Confirmar com o usuário que somente SE-02 está autorizada.
3. Resolver SEB-006 antes de criar schema ou conectar Supabase.
4. Usar apenas dados sintéticos até os gates de governança permitirem outra coisa.

## Prompt de retomada sugerido

> Continue somente pela Etapa SE-02 do Smart Environment. Primeiro faça SEB-006:
> matriz de finalidades, dados e responsáveis. Não abra a webcam, não crie detector,
> não use dados reais e não conecte Supabase antes de confirmar autorização e projeto.
