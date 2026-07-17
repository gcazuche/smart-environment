# Stack técnica inicial

Versões exatas serão travadas em lockfile somente antes da primeira dependência ser
instalada. Não se declara compatibilidade de GPU sem executar a matriz correspondente.

| Camada | Escolha inicial | Versão/política | Estado e justificativa |
|---|---|---|---|
| Linguagem | Python | `>=3.11`; baseline 3.12 | Fundação stdlib testada em 3.12.13; stack de visão ainda não validada |
| Captura | OpenCV | candidata `4.13.0.92` | Major 5 é recente; I/O/codec será validado por fonte/SO |
| Detecção/embedding | adaptador `FaceEngine` | InsightFace `1.0.1` é candidato | pesos/model packs bloqueados até licença e smoke test |
| Inferência | ONNX Runtime | candidata `1.27.0`; CPU obrigatório | GPU em artefato/matriz separados; provider testado em runtime |
| API | FastAPI + Uvicorn | candidata FastAPI `0.139.2` | Tipagem/OpenAPI; patch recém-publicado exige regressão e pin |
| Interface | PySide6 | candidata `6.11.1` | LGPL/comercial; revisar distribuição e manter loop isolado |
| ORM | SQLAlchemy | candidata `2.0.51` | linha 2.0 estável; sessões e queries parametrizadas |
| Migrações | Alembic | candidata `1.18.5` | autogenerate sempre revisado e testado |
| Banco central | PostgreSQL | candidata `18.4`, minor corrente | fonte canônica; suporte operacional e restore obrigatórios |
| Vetores centrais | pgvector | candidata `0.8.5` | busca exata primeiro; filtros relacionais e versão mínima |
| Cache/fila de borda | SQLite | stdlib/driver a definir | operação offline transacional |
| Índice local opcional | FAISS CPU | candidata `1.14.3`, após benchmark | não será fonte de verdade; GPU oficial é Linux |
| Senhas | Argon2id | parâmetros calibrados | bcrypt é fallback de migração, não default |
| Tokens | JWT curto + rotação/allowlist | algoritmo e biblioteca a fixar | HTTPS obrigatório; validar issuer/audience |
| Testes | pytest + unittest | pytest a fixar; unittest stdlib | Fase 1 não depende de download |
| Qualidade | Ruff, mypy | a fixar | lint, formato e type-check em CI |
| Segurança | pip-audit, gitleaks, Semgrep | gates incrementais | somente scanners passivos nesta etapa |

## Dependências opcionais de GPU

- NVIDIA/CUDA deve usar o pacote/provider documentado pelo ONNX Runtime e uma matriz
  explícita de driver, CUDA, cuDNN, modelo e sistema operacional.
- CPU continua sendo caminho suportado e coberto por testes.
- O sistema nunca escolhe GPU apenas pela presença do hardware; testa o provider e
  volta para CPU com alerta claro.

## Política de dependências

1. Fonte oficial e manutenção ativa verificadas.
2. Licença do código e dos pesos analisada separadamente.
3. Versão mínima/máxima registrada e travada em lockfile com hashes quando viável.
4. SCA e smoke test antes de aceitar atualização.
5. Dependências de desktop, servidor, visão e GPU ficam em extras separados.

Consulte `.planning/research/TECHNOLOGY_COMPARISON.md` para evidências e lacunas.
