# Stack técnica — Smart Environment

Atualizado em: 2026-08-11

Versões entram no `uv.lock` somente quando uma fase realmente usa a dependência. Uma
biblioteca candidata não é tratada como instalada, segura ou compatível sem evidência.

## Stack ativa e planejada

| Camada | Direção | Estado | Gate antes de adotar |
|---|---|---|---|
| Linguagem | Python `>=3.11,<3.13` | fundação validada em 3.11/3.12 | manter matriz e lock reproduzível |
| Interface | HTML, CSS e JavaScript | planejada | UX responsiva, acessibilidade e política de sessão |
| Framework web | sem escolha final | `unspecified` | PoC mínima; evitar framework sem necessidade |
| API | FastAPI + servidor ASGI | candidata | versão pinada, contratos, auth e testes de abuso |
| Captura | OpenCV `4.13.0.92`, CPU-first | selecionada para SE-02 | fonte simulada, lifecycle e matriz Windows |
| Detecção de pessoas | HOG padrão do OpenCV atrás de adaptador | baseline de PoC | Apache 2.0; validar limitação em pessoas sentadas/parciais |
| Persistência central | Supabase/PostgreSQL | preferencial, não validada | Auth, RLS, região, quota, custo, backup e restore |
| ORM/migrações | SQLAlchemy + Alembic | candidatas | schema mínimo, upgrade/downgrade e transações |
| Outbox local | SQLite | candidata | confinamento, limites, retenção e idempotência |
| Realtime | Supabase Realtime ou polling | `unspecified` | autorização, custo, reconexão e carga |
| Gráficos | biblioteca web a selecionar | `unspecified` | acessibilidade, tamanho, licença e manutenção |
| Testes | pytest + unittest | baseline existente | testes por camada e evidência de hardware separada |
| Qualidade | Ruff + mypy strict | baseline existente | gates verdes em cada tarefa |
| Segurança | busca de segredos, SCA, SAST e SBOM | incremental | ferramentas/escopo registrados; sem alegação genérica |

## Dependências existentes

O código atual usa apenas a fundação Python necessária para configuração, diagnóstico,
logging e testes. OpenCV foi usado em um ambiente efêmero para o smoke autorizado da
webcam e ainda não pertence ao lock principal.

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
- detector de pessoas e runtime de inferência;
- versões de FastAPI, OpenCV, SQLAlchemy, Alembic e SDKs;
- região/plano do Supabase e requisitos de residência/restore;
- empacotamento da borda e implantação do backend;
- gateway e protocolo de câmeras futuras/ESP32.
