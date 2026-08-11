# Decisões arquiteturais

Atualizado em: 2026-08-11

Decisões preservam história e podem ser revistas por evidência. `Supersedida` significa
que a decisão não orienta mais o produto ativo; não apaga o registro anterior.

## ADR-001 — Monólito modular com borda e serviço central

- **Data:** 2026-07-17; emendada em 2026-08-11
- **Status:** aceita.
- **Decisão:** manter um repositório modular. A borda controla câmeras e agrega
  ocupação; a API central autoriza/persiste; o navegador consome a API.
- **Consequências:** módulos possuem contratos e dados versionados; a rede não participa
  por frame; extração para serviços só ocorre quando carga/implantação justificar.

## ADR-002 — Python 3.11/3.12

- **Data:** 2026-07-17
- **Status:** aceita com ressalvas.
- **Decisão:** suportar Python `>=3.11,<3.13`, com matriz 3.11/3.12 e CPU baseline.
- **Consequências:** bibliotecas nativas entram somente após smoke nas duas versões;
  GPU tem matriz própria e nunca é requisito do MVP.

## ADR-003 — Motor facial substituível

- **Data:** 2026-07-17; revista em 2026-08-11
- **Status:** supersedida pelo ADR-010.
- **Decisão anterior:** criar `FaceEngine` com candidato InsightFace/ONNX.
- **Motivo da mudança:** o produto deixou de ter reconhecimento facial como objetivo;
  identidade e biometria são desnecessárias para ocupação.
- **Consequências:** nenhum peso, embedding, matching, pgvector ou vivacidade entra no
  roadmap ativo. Retorno exige nova finalidade e gate formal.

## ADR-004 — Supabase central preferencial; SQLite somente para resiliência local

- **Data:** 2026-07-17; emendada em 2026-08-11
- **Status:** proposta a validar em SE-02.
- **Decisão:** Supabase/PostgreSQL será a primeira direção central com dados sintéticos;
  SQLite poderá guardar configuração/outbox agregada quando SE-05 exigir modo offline.
- **Consequências:** Auth, RLS, região, custo, quotas, backup, restore e eliminação são
  gates; `service_role` fica no backend. `pgvector` e Storage de frames foram removidos.
- **Alternativa:** PostgreSQL gerenciado/local se a PoC reprovar critérios essenciais.

## ADR-005 — Concorrência por responsabilidade

- **Data:** 2026-07-17; emendada em 2026-08-11
- **Status:** proposta.
- **Decisão:** worker/thread por câmera, fila limitada/latest-frame, inferência fora da
  API, ASGI para I/O e outbox com backoff.
- **Consequências:** PySide6/Qt sai da decisão; limites, shutdown e falha isolada são
  requisitos antes de multicâmera.

## ADR-006 — Ferramenta GSD não instalada automaticamente

- **Data:** 2026-07-17
- **Status:** aceita.
- **Decisão:** manter artefatos GSD em Markdown e tratar instalador externo como opcional,
  após revisão de supply chain.

## ADR-007 — Logger reservado controla apenas seus handlers

- **Data:** 2026-07-17
- **Status:** aceita para o baseline.
- **Decisão:** `configure_secure_logging` controla somente `multicam`/`multicam.*`, usa
  allowlist/redaction e não remove handlers do host.
- **Consequências:** o namespace técnico legado permanece até migração planejada.

## ADR-008 — Webcam integrada e DirectShow como evidência local

- **Data:** 2026-07-17; reenquadrada em 2026-08-11
- **Status:** evidência de spike; implementação pendente em SE-03.
- **Decisão:** a webcam integrada é o primeiro sensor real. Neste Windows, MSMF falhou
  e DirectShow abriu um frame 640×480 em memória e liberou o dispositivo.
- **Consequências:** backend/índice não são identidade portátil; SE-03 deve redescobrir,
  suportar fonte simulada e verificar ausência de persistência.

## ADR-009 — Mudança de produto para Smart Environment

- **Data:** 2026-08-11
- **Status:** aceita.
- **Problema:** o planejamento anterior descrevia câmeras com reconhecimento facial,
  enquanto o objetivo atual é gestão inteligente de ambientes.
- **Decisão:** reorientar o produto para ocupação, sustentabilidade, recursos,
  patrimônio, alertas e dashboard web.
- **Consequências:** fundação técnica e evidência da webcam são preservadas; planos
  funcionais antigos são marcados como superados; código não é renomeado em SE-01.

## ADR-010 — Ocupação sem identificação e sem avaliação laboral individual

- **Data:** 2026-08-11
- **Status:** aceita como limite do MVP.
- **Decisão:** detectar/contar pessoas e agregar por ambiente/janela. Não reconhecer
  identidade nem inferir atenção, emoção, distração, produtividade ou jornada.
- **Consequências:** schema e API proíbem `person_id`, face, embedding e tracking
  persistente; alertas não fundamentam punição/culpa; mudança exige novo projeto/RIPD.
- **Motivo:** mede a necessidade operacional com menor intrusão e reduz risco de erro,
  discriminação e function creep.

## ADR-011 — Interface web substitui PySide6

- **Data:** 2026-08-11
- **Status:** aceita em nível de direção; framework `unspecified`.
- **Decisão:** usar HTML, CSS e JavaScript no navegador, consumindo API Python.
- **Consequências:** acesso por dispositivos diferentes e separação clara da borda;
  autenticação, acessibilidade, responsividade e ausência de vídeo são gates.

## ADR-012 — Frames efêmeros; eventos agregados como fronteira de dados

- **Data:** 2026-08-11
- **Status:** aceita para o MVP.
- **Decisão:** frames permanecem em buffers limitados na borda e são descartados. Só
  eventos de ocupação minimizados atravessam a rede e persistem.
- **Consequências:** Supabase Storage não é usado para frames; preview existe apenas em
  calibração local autorizada; testes verificam arquivos, banco, rede, logs e caches.
- **Ressalva:** agregado não é sinônimo automático de anônimo; granularidade e acesso
  ainda precisam de avaliação contra reidentificação.

## ADR-013 — Sustentabilidade começa como recomendação

- **Data:** 2026-08-11
- **Status:** aceita.
- **Decisão:** apresentar oportunidades estimadas e revisão humana antes de qualquer
  comando de iluminação, ventilação ou climatização.
- **Consequências:** economia estimada é distinta de medição; automação futura exige
  perigo analisado, override, redundância e fail-safe.

## ADR-014 — Alertas patrimoniais são não acusatórios

- **Data:** 2026-08-11
- **Status:** aceita.
- **Decisão:** um evento fora da regra gera alerta operacional, não afirma furto,
  identidade ou culpa.
- **Consequências:** revisão/correção humana e auditoria são obrigatórias; qualquer PoC
  visual de objeto terá dataset, licença e métrica próprios.
