# Decisões arquiteturais

Decisões podem ser revistas por evidência. Itens ainda condicionais são marcados como
`proposta`, não como fato consumado.

## ADR-001 — Monólito modular com cliente de borda e servidor central

- **Data:** 2026-07-17
- **Status:** aceita
- **Problema:** permitir uso em um computador agora e distribuição futura sem criar
  um conjunto prematuro de microsserviços.
- **Alternativas:** monólito único; microsserviços; monólito modular + cliente/servidor.
- **Decisão:** módulos no mesmo repositório, com contratos explícitos; captura e
  reconhecimento rodam no cliente, API e dados canônicos no servidor.
- **Justificativa:** reduz complexidade operacional inicial e preserva a fronteira
  necessária para vários dispositivos.
- **Consequências:** módulos não podem acessar persistência alheia diretamente; APIs e
  eventos precisam de versionamento.
- **Revisão:** quando carga ou implantação independente justificar extração.

## ADR-002 — Python 3.12 como baseline de desenvolvimento

- **Data:** 2026-07-17
- **Status:** aceita com ressalvas
- **Problema:** escolher uma versão moderna compatível com bibliotecas nativas.
- **Alternativas:** 3.11, 3.12, 3.13+.
- **Decisão:** suportar `>=3.11`; validar inicialmente em 3.12; não prometer 3.13+
  antes da matriz das dependências de visão.
- **Justificativa:** o runtime local disponível é Python 3.12.13 e 3.11/3.12 possuem
  ecossistema maduro para o stack proposto.
- **Consequências:** CI deverá testar 3.11 e 3.12; GPU terá matriz separada.
- **Revisão:** a cada atualização do lockfile.

## ADR-003 — Motor facial atrás de uma interface substituível

- **Data:** 2026-07-17
- **Status:** proposta condicionada
- **Problema:** precisão, desempenho, manutenção e licenças variam por modelo.
- **Alternativas:** InsightFace/ONNX Runtime; DeepFace; FaceNet; OpenCV SFace.
- **Decisão:** definir `FaceEngine` independente. InsightFace + ONNX Runtime é o
  candidato técnico inicial, mas nenhum modelo será distribuído até licença e uso
  (inclusive comercial, se aplicável) serem validados.
- **Justificativa:** evita aprisionar domínio e dados em um fornecedor/modelo.
- **Consequências:** embeddings carregam `model_id`, versão, dimensão e normalização;
  embeddings de modelos diferentes nunca são comparados diretamente.
- **Revisão:** Fase 5, antes de baixar qualquer peso.

## ADR-004 — PostgreSQL/pgvector central e SQLite local

- **Data:** 2026-07-17
- **Status:** proposta
- **Problema:** combinar fonte canônica, busca vetorial e operação offline.
- **Alternativas:** PostgreSQL puro/BYTEA; PostgreSQL+pgvector; Supabase; FAISS;
  banco vetorial dedicado.
- **Decisão:** PostgreSQL + pgvector no servidor; SQLite com BLOBs versionados e fila
  no cliente; FAISS somente se benchmark justificar índice local grande.
- **Justificativa:** integridade transacional e busca vetorial ficam próximas; SQLite
  fornece fila durável sem serviço adicional na borda.
- **Consequências:** dados locais sensíveis exigem permissões/criptografia adequadas;
  Supabase segue opção de hospedagem, não muda o modelo lógico.
- **Revisão:** após confirmação de escala e implantação.

## ADR-005 — Concorrência por responsabilidade

- **Data:** 2026-07-17
- **Status:** proposta
- **Problema:** impedir que I/O, inferência e GUI se bloqueiem mutuamente.
- **Alternativas:** somente threads; somente asyncio; multiprocessing; workers externos.
- **Decisão:** thread por captura com fila limitada/latest-frame; pool/processo de
  inferência configurável; thread principal exclusiva da GUI; asyncio para API e
  sincronização; banco por unidades de trabalho curtas.
- **Justificativa:** OpenCV é I/O/native-heavy, inferência precisa de isolamento e a
  GUI tem afinidade de thread.
- **Consequências:** filas devem ter backpressure, encerramento explícito e métricas.
- **Revisão:** benchmarks das Fases 9 e 18.

## ADR-006 — Nenhuma instalação automática da ferramenta GSD

- **Data:** 2026-07-17
- **Status:** aceita
- **Problema:** o fluxo pode ser reproduzido manualmente e instaladores remotos têm
  risco de supply chain.
- **Alternativas:** instalar via `npx`; usar a skill disponível; fluxo manual.
- **Decisão:** usar a skill GSD disponível e os arquivos `.planning`; documentar o
  instalador oficial como opcional, sem executá-lo sem autorização.
- **Justificativa:** preserva o fluxo exigido sem modificar o ambiente global/local.
- **Consequências:** comandos GSD são documentação até o usuário optar pela instalação.
- **Revisão:** por solicitação do usuário.
