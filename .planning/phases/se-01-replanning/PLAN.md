# SE-01 — Plano atômico

Data: 2026-08-11
Escopo: documentação somente

| Tarefa | Resultado | Estado |
|---|---|---|
| SE-01-01 | inventário preservar/adaptar/superar | concluída |
| SE-01-02 | visão, problema, público, MVP e sucesso | concluída |
| SE-01-03 | limites de privacidade, segurança e uso laboral | concluída |
| SE-01-04 | arquitetura e stack Smart Environment | concluída |
| SE-01-05 | requisitos, roadmap, backlog, riscos, testes e ADRs | concluída |
| SE-01-06 | checkpoint, legado e validação | concluída |

## SE-01-01 — Inventário

- Confirmar branch/worktree, documentos, código e estado da antiga Fase 2.
- Classificar itens como preservado, adaptado ou superado.
- **Aceite:** nenhum trabalho antigo incompatível é executado por engano.

## SE-01-02 — Produto

- Reescrever visão, problema, público, MVP, fora de escopo e definição de sucesso.
- **Aceite:** uma única vertical explica o valor sem biometria ou avaliação individual.

## SE-01-03 — Governança

- Modelar finalidade, minimização, reidentificação, transparência, retenção, revisão
  humana, direitos e gates antes de dados reais.
- **Aceite:** “distração” não permanece como funcionalidade; alertas e energia têm
  limites não punitivos/fail-safe.

## SE-01-04 — Arquitetura

- Desenhar borda→evento agregado→API→Supabase→web.
- Separar stack ativa, candidata, removida e `unspecified`.
- **Aceite:** frames não atravessam borda; PySide6/pgvector/FaceEngine não são baseline.

## SE-01-05 — Rastreabilidade

- Criar requisitos verificáveis e um roadmap incremental de 12 etapas.
- Atualizar backlog, riscos, testes e decisões.
- **Aceite:** cada requisito tem fase/aceite/estado e cada etapa tem objetivo/fora.

## SE-01-06 — Checkpoint

- Atualizar README, STATE, CHANGELOG e artefatos da fase.
- Marcar a antiga Fase 2 e pesquisas incompatíveis como históricas.
- Executar revisão de links, termos, diff, testes e gates aplicáveis.
- **Aceite:** somente documentação mudou; SE-02 permanece não iniciada.

## Rollback

Reverter o checkpoint documental restaura o baseline anterior; nenhum schema, dado,
dependência ou serviço precisa de rollback porque não foi alterado.
