# Stack técnica — Smart Environment

Atualizado em: 2026-08-22

O ambiente ativo é recriado por `environment.yml` no Conda `smart-environment`.
`uv.lock` permanece somente como evidência histórica. Uma biblioteca candidata não é
tratada como instalada, segura ou compatível sem evidência.

## Stack ativa e planejada

| Camada | Direção | Estado | Gate antes de adotar |
|---|---|---|---|
| Linguagem | Python `>=3.11,<3.13` | fundação validada em 3.11/3.12 | manter matriz e lock reproduzível |
| Interface | React 19 + TypeScript, HTML/CSS gerados | protótipo visual ativo | UX responsiva, acessibilidade e política de sessão |
| Framework web | Vinext/Vite no Sites | selecionado para protótipo | build, compatibilidade Cloudflare e revisão antes de integrar dados |
| API | FastAPI + servidor ASGI | candidata | versão pinada, contratos, auth e testes de abuso |
| Captura | OpenCV `4.13.0.92`, CPU-first | selecionada para SE-02 | fonte simulada, lifecycle e matriz Windows |
| Detecção de pessoas | NanoDet-m-plus-1.5x ONNX via OpenCV DNN/CPU | baseline ativo de PoC | Apache-2.0, revisão/hash fixados; medir falsos sinais e latência |
| Detector experimental | Intel Person Detection, YOLO26n FP16 via OpenVINO 2026.2.1 | integrado para comparação acadêmica | revisão/hashes fixados; AGPL-3.0; medir webcam e dataset |
| Atividade observável | contrato Python tipado + zonas normalizadas + objetos COCO restritos | smoke offline detectou 2 laptops e 0 celulares, sem inferência de atividade | validar celular e negativos em câmera controlada antes de integrar |
| Referências de estação | 3 JPEGs revisados do Hugging Face, CC-BY-NC-SA-4.0 | smoke qualitativo não comercial, hashes fixados | substituir/complementar antes de treinamento, métricas ou produto |
| Persistência central | Supabase/PostgreSQL | preferencial, não validada | Auth, RLS, região, quota, custo, backup e restore |
| ORM/migrações | SQLAlchemy + Alembic | candidatas | schema mínimo, upgrade/downgrade e transações |
| Outbox local | SQLite | candidata | confinamento, limites, retenção e idempotência |
| Realtime | Supabase Realtime ou polling | `unspecified` | autorização, custo, reconexão e carga |
| Gráficos | biblioteca web a selecionar | `unspecified` | acessibilidade, tamanho, licença e manutenção |
| Testes | pytest + unittest | baseline existente | testes por camada e evidência de hardware separada |
| Qualidade | Ruff + mypy strict | baseline existente | gates verdes em cada tarefa |
| Segurança | busca de segredos, SCA, SAST e SBOM | incremental | ferramentas/escopo registrados; sem alegação genérica |

## Dependências existentes

O código atual usa a fundação Python, OpenCV e NumPy fixados em `pyproject.toml`; o
Conda oficial instala o projeto editável por `environment.yml`. O NanoDet é baixado
separadamente do Hugging Face por script com revisão e SHA-256 fixados.
O Intel Person Detection é opcional, instalado no mesmo Conda e exportado localmente;
Ultralytics fica restrito à preparação do modelo e OpenVINO executa a inferência.

## Itens retirados do baseline

| Item antigo | Situação nova |
|---|---|
| InsightFace/FaceEngine | fora do MVP; nenhum peso será baixado |
| ONNX para embeddings faciais | fora do MVP; runtime de inferência será decidido com o detector de pessoas |
| pgvector/FAISS | sem necessidade enquanto não houver vetores |
| PySide6 | substituído pelo direcionamento de interface web |
| Supabase Storage para frames | fora do MVP porque frames não serão persistidos |
| Vivacidade e matching facial | fora do roadmap ativo |

Esses itens continuam citados apenas em pesquisa histórica. Reintroduzi-los exigirá
uma nova decisão, justificativa proporcional, licença e gate de privacidade.

## Política para modelos de visão

1. Verificar separadamente licença do código, pesos, dataset e uso comercial.
2. Registrar origem, hash/versão, pré-processamento e limitações.
3. Comparar ao menos uma alternativa leve CPU-first em dados sintéticos/autorizados.
4. Medir 0, 1 e N pessoas, oclusão, iluminação, falso positivo e falso negativo.
5. Não inferir identidade, emoção, intenção ou produtividade real; atividade futura é
   estimativa contextual e inclui `inconclusivo`.
6. Manter fallback `unknown`; falha de modelo não equivale a ambiente vazio.

## Política de dependências

- preferir fonte oficial e projeto mantido;
- fixar versão e registrar licença antes do merge;
- manter runtime, desenvolvimento e componentes opcionais separados;
- executar SCA e smoke test de atualização;
- suportar CPU; GPU só entra após matriz real de driver/runtime;
- não colocar SDK ou chave privilegiada do Supabase no navegador ou dispositivo;
- não adicionar uma dependência apenas porque apareceu no planejamento anterior.

## Decisões ainda abertas

- framework web, biblioteca de gráficos e estratégia Realtime;
- detector final após medir NanoDet e Intel/OpenVINO em amostras representativas;
- versões de FastAPI, OpenCV, SQLAlchemy, Alembic e SDKs;
- região/plano do Supabase e requisitos de residência/restore;
- empacotamento da borda e implantação do backend;
- gateway e protocolo de câmeras futuras/ESP32.
