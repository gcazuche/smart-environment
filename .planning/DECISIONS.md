# Decisões arquiteturais

Atualizado em: 2026-08-11

Decisões preservam história e podem ser revistas por evidência. `Supersedida` significa
que a decisão não orienta mais o produto ativo; não apaga o registro anterior.

## ADR-021 — NanoDet oficial como detector ativo do PoC

- **Status:** aceita para PoC em 2026-08-14; produção ainda não aprovada.
- **Decisão:** usar NanoDet-m-plus-1.5x ONNX do repositório oficial OpenCV no Hugging
  Face, filtrar somente `person` antes do NMS e executar localmente via OpenCV DNN/CPU.
- **Supply chain:** revisão `5bfd47077350a726ad440dd7bd1e1e35e8ebcfb2`, SHA-256
  `4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186` e licença
  Apache-2.0 registrados; peso fica fora do Git e tem download verificável.
- **Consequência:** substitui o híbrido HOG/cascade como padrão da CLI. Limiar 0,35 foi
  mantido porque 0,30/0,25 aumentaram falsos sinais no smoke; dataset e métricas seguem
  obrigatórios antes de qualquer alegação comercial.

## ADR-020 — Detector híbrido local para corpo parcial

- **Status:** supersedida pela ADR-021 em 2026-08-14; preservada como fallback histórico.
- **Decisão:** combinar o HOG de corpo inteiro com `haarcascade_upperbody.xml`, ambos
  distribuídos pelo OpenCV, normalizar iluminação e remover caixas sobrepostas.
- **Justificativa:** melhora o caso sentado/parcial sem nova dependência, download de
  pesos ou processamento em rede; o arquivo upper-body inclui licença permissiva
  BSD-like com requisitos de atribuição.
- **Consequência:** o smoke detectou presença, mas um pico de duas detecções ainda exige
  dataset autorizado, medição de falsos sinais e comparação antes de uso comercial.

## ADR-019 — Antecipar o protótipo visual do dashboard

- **Status:** aceita em 2026-08-14.
- **Decisão:** pausar SEB-017 e antecipar somente a camada visual da SE-06 com dados
  simulados; depois da revisão do usuário, retomar a detecção de corpo parcial.
- **Tecnologia:** React 19/TypeScript com Vinext/Vite e CSS responsivo. TypeScript é
  compilado para JavaScript e não altera o contrato web HTML/CSS/JavaScript do produto.
- **Limites:** nenhum Auth, banco, API, câmera real, stream ou armazenamento nesta fatia.
- **Consequência:** o protótipo não encerra a SE-06; componentes serão conectados apenas
  quando contratos e autorização de dados existirem.

## ADR-018 — Conda isolado como ambiente oficial

- **Status:** aceita em 2026-08-14.
- **Decisão:** usar exclusivamente o ambiente `smart-environment`, criado por
  `environment.yml`, para desenvolvimento, testes, câmera e build. Nunca instalar
  dependências do projeto no `base`.
- **Operação:** pessoas podem ativar o ambiente; automações e o Codex usam
  `conda run -n smart-environment` para evitar dependência do estado do shell.
- **Consequência:** o lock e a `.venv` anteriores são históricos. Mudanças futuras de
  dependência devem atualizar `environment.yml` e ser verificadas dentro do Conda.

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

## ADR-015 — PoC de câmera e pessoas antes do Supabase

- **Data:** 2026-08-14
- **Status:** aceita pelo usuário.
- **Decisão:** antecipar a prova local de webcam, caixas e contagem para SE-02; domínio e
  Supabase passam a SE-03.
- **Consequências:** valor visual é validado cedo e sem rede; o slice não persiste frames,
  não identifica pessoas e não classifica atividade.

## ADR-016 — Detector HOG/OpenCV como baseline substituível

- **Data:** 2026-08-14
- **Status:** aceita para PoC, não para produção.
- **Decisão:** começar com o detector de pessoas HOG/SVM já incluído no OpenCV 4.13,
  atrás de contrato substituível e sem download de pesos externos.
- **Justificativa:** patch pequeno, operação CPU/offline e licença Apache 2.0 do OpenCV.
- **Consequências:** HOG favorece corpo inteiro e pode falhar com pessoa sentada,
  parcialmente visível ou em iluminação difícil; SE-02 mede essa limitação e um modelo
  melhor poderá substituir o backend sem alterar câmera/CLI.

## ADR-017 — Atividade observável, não produtividade real

- **Data:** 2026-08-14
- **Status:** aceita como direção para SE-04.
- **Decisão:** no futuro estimar `trabalho_aparente`, `pausa_aparente` ou `inconclusivo`,
  com regras por contexto e tracking efêmero.
- **Consequências:** nenhuma inferência de intenção/emoção, identidade, controle de ponto,
  ranking ou punição automática; resultado sempre é apresentado como estimativa.
