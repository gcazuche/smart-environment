> [!IMPORTANT]
> **BASELINE FACIAL HISTÓRICO desde 2026-08-11.** As conclusões sobre FaceEngine,
> PySide6, pgvector, embeddings e vivacidade não orientam o Smart Environment ativo.
> OpenCV/Python/banco podem ser reaproveitados somente após revalidação na fase atual.

# Comparação tecnológica — Fase 1 (histórica)

**Projeto:** sistema multicâmera com reconhecimento facial
**Data de corte da pesquisa:** 2026-07-17
**Escopo:** pesquisa e decisão inicial; nenhuma dependência ou modelo foi instalado nesta etapa
**Fontes:** somente documentação oficial, metadados dos projetos e artigos/repositórios primários

## Como ler este documento

- **Fato confirmado:** está explicitamente sustentado por uma fonte primária ligada no texto.
- **Inferência:** conclusão técnica derivada dos fatos, ainda sujeita a teste no ambiente real.
- **Decisão:** baseline recomendado para o projeto; não equivale a compatibilidade já validada.
- **Lacuna:** informação que não pôde ser confirmada ou depende de hardware, licença, carga ou requisito ainda desconhecido.

Versão “mais recente” significa a versão exibida pela fonte oficial na data de corte. As versões abaixo são candidatas para o primeiro lockfile, não autorização para atualizar automaticamente. Pacotes binários, pesos de modelos e extensões de banco exigem lock por plataforma, hash, SCA e smoke test.

## Resumo executivo

| Camada | Decisão inicial | Estado | Justificativa curta |
|---|---|---|---|
| Python | Python 3.12 como baseline; 3.11 apenas como fallback temporário | Condicionada a smoke test | 3.12 tem um ano adicional de suporte de segurança e os componentes centrais publicam suporte/wheels; InsightFace ainda não declara `Requires-Python` |
| Detecção e embeddings | Adaptador próprio `FaceEngine`, com InsightFace 1.0.1 + ONNX Runtime como candidato | Bloqueada para produção até licenciar os pesos | O runtime é modular e funciona em CPU/GPU, mas os model packs fornecidos pelo InsightFace não têm licença geral de produção |
| Alternativas faciais | DeepFace somente para avaliação; FaceNet somente como referência algorítmica | Não escolhidas para o núcleo | DeepFace amplia muito a superfície TensorFlow e FaceNet não é um pacote moderno mantido |
| Captura e pré-processamento | OpenCV 4.13.0.92 inicialmente | Candidata | OpenCV 5.0 foi lançado há apenas 15 dias; a série 4.13 reduz o risco de migração de major |
| Inferência | ONNX Runtime 1.27.0 CPU obrigatório; variante NVIDIA GPU opcional | Candidata | Mesmo contrato ONNX, fallback explícito e wheels 3.11/3.12; GPU depende de matriz CUDA/cuDNN real |
| API | FastAPI 0.139.2 + Uvicorn, com inferência fora do event loop | Candidata | Tipagem, OpenAPI e ASGI; ainda está em 0.x e a versão é de 2026-07-16 |
| Desktop | PySide6 6.11.1 | Candidata, sujeita a revisão de licença/distribuição | Binding oficial Qt, suporte publicado para 3.11/3.12 e modelo sólido de sinais/threads |
| Banco central | PostgreSQL local/LAN 18.4, sempre no minor corrente | Recomendada | Fonte canônica local, integridade relacional, menor exposição de biometria e operação offline independente de nuvem |
| Serviço PostgreSQL gerenciado | Supabase como opção futura de implantação, não como baseline | Adiada | Reduz operação, mas adiciona fornecedor, rede, residência/DPA/custo e não substitui cache offline |
| ORM e migrações | SQLAlchemy 2.0.51 + Alembic 1.18.5 + Psycopg 3 | Recomendadas | Camada madura, sync/async e histórico explícito; autogenerate precisa de revisão humana |
| Busca vetorial central | pgvector 0.8.5; busca exata primeiro, HNSW só após benchmark | Recomendada | Vetores e metadados ficam transacionais e filtráveis na mesma fonte de verdade |
| Índice local | FAISS CPU apenas se cardinalidade/latência justificarem | Adiada | Muito eficiente em memória, mas exige sincronização, tombstones, versionamento e persistência próprios; GPU oficial é Linux |

## Snapshot de versões e manutenção

| Tecnologia | Versão observada em 2026-07-17 | Data publicada | Python declarado/artefato | Licença principal observada | Observação |
|---|---:|---:|---|---|---|
| InsightFace | 1.0.1 | 2026-05-23 | sem `Requires-Python`; wheel `py3-none-any` | código MIT; pesos/model packs com termos separados | ativo, mas licença dos pesos é bloqueador |
| DeepFace | 0.0.100 | 2026-05-09 | `>=3.7`; wheel `py3-none-any` | código MIT; modelos de terceiros exigem análise própria | ativo, dependências amplas |
| OpenCV Python | 5.0.0.93 | 2026-07-02 | wheels 3.11/3.12 | Apache-2.0 para OpenCV; componentes empacotados têm licenças próprias | major novo; baseline proposto é 4.13.0.92 |
| OpenCV Python | 4.13.0.92 | 2026-02-05 | wheels 3.11/3.12 | idem | baseline conservador |
| ONNX Runtime CPU/GPU | 1.27.0 | 2026-06-15 | `>=3.11`; wheels CPython 3.11/3.12 | MIT | GPU PyPI usa CUDA 12.x por padrão |
| FastAPI | 0.139.2 | 2026-07-16 | `>=3.10`; 3.11/3.12 classificados | MIT | projeto ainda 0.x |
| PySide6 | 6.11.1 | 2026-05-13 | `>=3.10`; wheel ABI3 e classificadores 3.11/3.12 | LGPLv3/GPLv3/comercial | obrigações de redistribuição precisam de revisão |
| PostgreSQL | 18.4 | minor corrente observado | n/a | PostgreSQL License | PG 18 suportado até 2030-11-14 |
| SQLAlchemy | 2.0.51 | 2026-06-15 | `>=3.7`; wheels 3.11/3.12 | MIT | 2.1.0b3 era pré-release; não escolhida |
| Alembic | 1.18.5 | 2026-06-25 | `>=3.10`; wheel universal | MIT | autogenerate não é prova de correção |
| pgvector (extensão SQL) | 0.8.5 | 2026-07-08 | PostgreSQL 13+ | PostgreSQL License | inclui correções posteriores a problemas de HNSW |
| pgvector-python | 0.5.0 | 2026-07-06 | `>=3.10` | MIT | integra Psycopg/SQLAlchemy |
| FAISS | 1.14.3 | 2026-06-13 | CPU: wheels 3.11/3.12; GPU: Linux | MIT | documentação de instalação ainda mostrava 1.14.2 |
| Python | 3.12.13 | 2026-03-03 | release de segurança, somente fonte | PSF | EOL em 2028-10 |
| Python | 3.11.15 | 2026-03-03 | release de segurança, somente fonte | PSF | EOL em 2027-10 |

Fontes do snapshot: [InsightFace no PyPI](https://pypi.org/project/insightface/), [DeepFace no PyPI](https://pypi.org/project/deepface/), [OpenCV no PyPI](https://pypi.org/project/opencv-python/), [ONNX Runtime CPU](https://pypi.org/project/onnxruntime/), [ONNX Runtime GPU](https://pypi.org/project/onnxruntime-gpu/), [FastAPI no PyPI](https://pypi.org/project/fastapi/), [PySide6 no PyPI](https://pypi.org/project/PySide6/), [política de versões PostgreSQL](https://www.postgresql.org/support/versioning/), [SQLAlchemy no PyPI](https://pypi.org/project/SQLAlchemy/), [Alembic no PyPI](https://pypi.org/project/alembic/), [changelog pgvector](https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md), [pgvector-python no PyPI](https://pypi.org/project/pgvector/), [releases FAISS](https://github.com/facebookresearch/faiss/releases), [Python 3.12.13](https://www.python.org/downloads/release/python-31213/) e [Python 3.11.15](https://www.python.org/downloads/release/python-31115/).

## 1. InsightFace vs DeepFace vs FaceNet

### Comparação

| Critério | InsightFace 1.0.1 | DeepFace 0.0.100 | FaceNet |
|---|---|---|---|
| Natureza | biblioteca/toolbox de análise facial e model zoo | wrapper de alto nível sobre vários detectores e modelos | método de embeddings apresentado em artigo de 2015; “FaceNet” não designa um pacote Python oficial atual |
| Pipeline | detecção, alinhamento, embedding e outros módulos; desde 0.2 usa modelos ONNX | API uniforme para verificação, busca, atributos e anti-spoofing, selecionando backends diversos | arquitetura/treinamento por triplet loss; a implementação popular `davidsandberg/facenet` usa TensorFlow antigo |
| Runtime dominante | ONNX Runtime | TensorFlow/Keras no caminho principal, além de backends opcionais | implementação de referência testada com TensorFlow 1.7 |
| CPU/GPU | troca do Execution Provider do ONNX Runtime | depende do backend; no caminho TensorFlow, GPU nativa no Windows moderno é um problema | implementação popular não é compatível com a stack moderna sem reengenharia |
| Manutenção observada | release 1.0.1 em 2026-05-23 | release 0.0.100 em 2026-05-09 | repositório popular registra últimas novidades/modelos em 2018 |
| Instalação | `pip install insightface` mais uma variante ORT; requisitos do setup incluem `onnxruntime` e `opencv-python` sem teto | `pip install deepface`; requisitos mínimos amplos incluem TensorFlow, Keras, OpenCV e Flask | não há distribuição moderna indicada para este projeto; build antigo/manual |
| Licença | código MIT; modelos fornecidos são declarados para pesquisa não comercial e os packs de reconhecimento exigem contato de licenciamento | código MIT; **inferência:** licença de cada peso/backend continua aplicável e deve ser inventariada | artigo pode ser estudado; implementação e pesos precisam ser avaliados separadamente |
| Adequação ao núcleo | boa tecnicamente, condicionada à licença e a smoke tests | boa para comparar modelos rapidamente, fraca para uma dependência central controlada | inadequada como biblioteca de produção atual |

O próprio projeto InsightFace informa que o código é MIT, mas que os dados de treinamento e modelos fornecidos são para pesquisa não comercial; o aviso atual também manda contatar `recognition-oss-pack@insightface.ai` para licenciar packs como `buffalo_l`. Isso significa que “biblioteca open source” não torna os pesos automaticamente utilizáveis em um produto. Fontes: [repositório oficial InsightFace](https://github.com/deepinsight/insightface) e [pacote oficial](https://pypi.org/project/insightface/).

O `setup.py` atual do InsightFace declara `onnxruntime` e `opencv-python` diretamente, sem separar CPU/GPU ou GUI/headless. Essa escolha pode reinstalar a variante CPU do ORT ou o OpenCV com GUI em um ambiente que pretendia usar `onnxruntime-gpu`/`opencv-python-headless`. É um risco de resolução que precisa ser reproduzido no lock, não contornado silenciosamente com `--no-deps`. Fonte: [setup do pacote InsightFace](https://github.com/deepinsight/insightface/blob/master/python-package/setup.py).

DeepFace é útil como bancada porque expõe vários modelos, detectores e anti-spoofing por uma API. Entretanto, seus requisitos oficiais têm mínimos amplos e sem limites superiores para TensorFlow, Keras, OpenCV e outras bibliotecas, o que aumenta tamanho, tempo de instalação, drift e risco de conflito. Fontes: [repositório DeepFace](https://github.com/serengil/deepface), [requirements oficial](https://github.com/serengil/deepface/blob/master/requirements.txt) e [módulo principal](https://github.com/serengil/deepface/blob/master/deepface/DeepFace.py).

Para Windows, a documentação oficial do TensorFlow diz que GPU CUDA nativa é suportada somente até TensorFlow 2.10; a partir de 2.11, o caminho oficial é WSL2. Isso não impede DeepFace em CPU, mas reduz sua atratividade para um desktop Windows com aceleração GPU nativa. Fontes: [instalação pip do TensorFlow](https://www.tensorflow.org/install/pip) e [builds Windows](https://www.tensorflow.org/install/source_windows).

O artigo FaceNet reporta 99,63% no LFW e 95,12% no YouTube Faces. Esses números são evidência histórica do método, **não** previsão de acurácia deste sistema, pois detector, pesos, câmera, população, limiar e protocolo mudam. A implementação popular declara testes com Ubuntu 14.04, Python 2.7/3.5 e TensorFlow 1.7; portanto, não é uma dependência aceitável para Python 3.11/3.12. Fontes primárias: [artigo FaceNet](https://arxiv.org/abs/1503.03832) e [implementação davidsandberg/facenet](https://github.com/davidsandberg/facenet).

### Desempenho e qualidade

Não existe comparação honesta de “InsightFace vs DeepFace vs FaceNet” usando apenas números publicados: DeepFace é um orquestrador, InsightFace combina detectores/modelos e FaceNet é uma família de arquitetura/método. Tabelas com hardware, detector, tamanho de entrada e protocolo diferentes não são comparáveis.

O benchmark obrigatório deve usar vídeos autorizados e representativos do ambiente:

1. FAR/FMR e FRR/FNMR em modo de conjunto aberto, incluindo pessoas não cadastradas.
2. ROC/DET, limiar por versão do modelo e margem entre primeira e segunda correspondência.
3. Resultado por iluminação, pose, oclusão, distância, câmera e grupos relevantes, com revisão de viés.
4. Latência p50/p95/p99 por estágio, FPS útil, frames descartados, RAM, VRAM e uso de CPU/GPU.
5. Robustez a reconexão, múltiplos rostos, fotos/telas e oclusões; vivacidade é um controle separado, não presumido pelo modelo.
6. Repetibilidade por hash dos pesos, versão do detector, preprocessamento, normalização e dimensão do embedding.

### Decisão

1. Definir contratos internos `FaceDetector`, `EmbeddingProvider` e `FaceMatcher` para impedir acoplamento a um fornecedor/model pack.
2. Usar InsightFace 1.0.1 + ONNX Runtime como **candidato técnico** para o spike e benchmark.
3. Não baixar automaticamente nem distribuir `buffalo_*` ou outro pack em produção até registrar licença, origem, finalidade permitida, hash e política de atualização.
4. Se a licença não for compatível, selecionar detector e modelo ONNX com licença comercial/produção verificável e mantê-los atrás dos mesmos contratos.
5. Usar DeepFace apenas em ambiente de pesquisa para comparação controlada, nunca como dependência transitiva do cliente/servidor de produção sem nova decisão.
6. Não usar `davidsandberg/facenet` nem outra stack TensorFlow 1.x como base.

### Lacunas

- Modelo, pesos, origem dos dados, licença de produção e dimensão final do embedding ainda não foram escolhidos.
- Não há evidência local de que InsightFace 1.0.1 instala e infere em Python 3.12 no Windows/Linux alvo.
- A eficácia e a licença do mecanismo de vivacidade ainda não foram pesquisadas/validadas.
- Não se conhece o número de pessoas, câmeras, FPS, resolução, distância e hardware; logo não há meta de throughput defensável.
- Não há base representativa autorizada nem aprovação de tratamento biométrico para calibrar limiares.

## 2. OpenCV

### Fatos, vantagens e desvantagens

OpenCV fornece captura de USB, arquivo e streams IP, conversão de cor, resize, geometria e codecs por `VideoCapture`. É apropriado para I/O e pré-processamento, mas não será a implementação de identidade facial. `VideoCapture` permite escolher backends como FFmpeg, GStreamer, Media Foundation e DirectShow; cada URL/câmera tem limitações próprias e a presença do backend depende de como o wheel foi construído. Fontes: [referência VideoCapture](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html), [opções de build](https://docs.opencv.org/4.x/db/d05/tutorial_config_reference.html) e [flags de backends](https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html).

Vantagens:

- API estável e ampla para frames, codecs e pré-processamento.
- Wheels oficiais do time OpenCV para Python 3.11/3.12 em Windows/Linux/macOS.
- FFmpeg está incluído nos wheels; backends nativos podem ser selecionados explicitamente.
- Diagnóstico de build por `cv2.getBuildInformation()` e nome do backend por `getBackendName()`.

Desvantagens/riscos:

- Wheels PyPI são CPU-only; CUDA requer build próprio, que eleva custo operacional.
- Buffering, timeout, hardware decode e transporte RTSP variam por backend/câmera; um teste com arquivo não valida RTSP.
- Os quatro pacotes (`opencv-python`, `opencv-contrib-python` e variantes `-headless`) compartilham o namespace `cv2` e não devem coexistir.
- Wheels não-headless trazem componentes de GUI que não são necessários quando PySide6 cuida da interface; isso aumenta tamanho e análise de licenças.
- InsightFace/DeepFace declaram `opencv-python` diretamente, criando conflito potencial com a preferência `headless`.

O projeto oficial recomenda instalar **apenas um** dos quatro pacotes e usar a variante headless quando outra GUI, como Qt, será responsável pela interface. Os wheels incluem OpenCV, FFmpeg e, nas variantes com GUI, Qt; as licenças desses componentes devem permanecer no inventário de distribuição. Fonte: [opencv-python no PyPI](https://pypi.org/project/opencv-python/).

### Versão e instalação propostas

- Baseline do spike: `opencv-python-headless==4.13.0.92` para workers/servidor.
- Desktop: preferir o mesmo headless e converter frames para `QImage`/`QPixmap`; não usar `cv2.imshow`.
- Se o resolver do InsightFace impedir uma instalação íntegra, registrar o conflito e decidir entre ambiente de inferência isolado ou uma distribuição OpenCV única comprovada. Não instalar dois `cv2`.
- Não adotar `5.0.0.93` na primeira integração: foi publicado em 2026-07-02 e precisa de testes de regressão de API, codecs e modelos.
- Reavaliar OpenCV 5 após o pipeline estar coberto por testes; 4.13 não é uma promessa de suporte indefinido.

### Gate de aceite

Testar, em cada SO alvo: câmera USB real, vídeo de arquivo, pelo menos uma câmera RTSP autorizada, autenticação/URL mascarada em logs, timeout, reconexão, liberação de `VideoCapture`, backend efetivo, H.264/H.265 quando exigido e comportamento sob perda de pacotes. A disponibilidade de aceleração de decode não deve ser inferida da presença de GPU.

## 3. ONNX Runtime: CPU vs GPU

### Comparação

| Critério | `onnxruntime` CPU | `onnxruntime-gpu` NVIDIA |
|---|---|---|
| Instalação | `pip install onnxruntime==1.27.0` | `pip install onnxruntime-gpu==1.27.0` |
| Portabilidade | caminho mais simples em Windows/Linux e sem driver CUDA | requer GPU/driver compatível e runtime CUDA/cuDNN |
| Python | `>=3.11`; wheels 3.11/3.12 confirmados | `>=3.11`; wheels Windows/Linux 3.11/3.12 confirmados |
| Tamanho/complexidade | menor e reproduzível | wheel muito maior, VRAM e DLLs adicionais |
| Throughput | baseline obrigatório; suficiente ou não depende da carga | pode aumentar throughput, mas cópia CPU↔GPU, batch e concorrência podem anular o ganho |
| Fallback | `CPUExecutionProvider` | lista ordenada `CUDAExecutionProvider`, depois CPU, se a política permitir |
| Operação | sem CUDA/cuDNN | observabilidade de provider, memória e falha de DLL obrigatória |

O ONNX Runtime particiona o grafo entre Execution Providers e usa a ordem configurada. Assim, passar CUDA antes de CPU permite fallback de nós não suportados; isso não prova que toda inferência ocorreu na GPU. Fonte: [Execution Providers](https://onnxruntime.ai/docs/execution-providers/).

Desde ORT 1.19, o pacote GPU no PyPI usa CUDA 12.x por padrão. A documentação informa que cuDNN 8 e 9 não são intercambiáveis e que wheels GPU a partir de 1.22 são somente CUDA 12. Ela também oferece `preload_dlls()` desde 1.21. Fontes: [instalação oficial](https://onnxruntime.ai/docs/install/) e [CUDA Execution Provider](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html).

### Decisão operacional

1. Manter CPU como perfil obrigatório e teste de aceitação em toda release.
2. Manter GPU como extra/artefato de implantação separado, nunca instalar simultaneamente as duas distribuições que expõem o mesmo módulo `onnxruntime`.
3. Configurar providers explicitamente; registrar provider solicitado, providers disponíveis e provider efetivo sem incluir imagem/embedding.
4. Se GPU for obrigatória para um nó, falhar o health check quando CUDA não carregar. Se fallback for permitido, emitir alerta claro e recalcular capacidade.
5. Comparar embeddings CPU/GPU com tolerância definida e medir p95/p99, VRAM e temperatura sob múltiplas câmeras.
6. Só habilitar TensorRT, DirectML ou outro provider mediante nova decisão e matriz própria.

### Risco de compatibilidade não resolvido

A tabela CUDA EP oficial consultada enumera explicitamente versões somente até ORT 1.20.x, embora o PyPI já publique 1.27.0; a página de build diz genericamente CUDA 12.x + cuDNN 9. Portanto, a combinação exata de wheel 1.27.0, driver, CUDA e cuDNN no hardware alvo **não está confirmada pela tabela consultada**. O gate deve executar `onnxruntime.get_available_providers()`, carregar o modelo real, fazer inferência e inspecionar logs/debug info. Não basta importar o pacote.

No Windows, o runtime Visual C++ também é requisito documentado. A estratégia de distribuir DLLs NVIDIA, usar pacotes `nvidia-*` ou depender de instalação do sistema será definida somente após inventário do hardware e revisão das licenças.

## 4. FastAPI

### Avaliação

FastAPI 0.139.2 declara Python 3.10+, usa Starlette/Pydantic e gera OpenAPI/JSON Schema a partir dos contratos tipados. É adequado para autenticação, administração, sincronização, configuração, health/readiness e eventos. Fonte: [FastAPI no PyPI](https://pypi.org/project/fastapi/).

Vantagens:

- contratos HTTP tipados e documentação OpenAPI;
- ecossistema ASGI e bom suporte a I/O assíncrono;
- injeção de dependências útil para autenticação, sessão de banco e políticas;
- testes de API sem servidor externo e separação clara da GUI.

Desvantagens/riscos:

- ainda está em 0.x; a política oficial reconhece que minors podem conter mudanças incompatíveis;
- Pydantic, Starlette e servidor ASGI formam uma matriz que deve ser travada/testada em conjunto;
- endpoints `async` não tornam inferência CPU/GPU não bloqueante;
- cada worker de processo pode duplicar modelo e VRAM se a inferência for carregada dentro da API.

A recomendação oficial é fixar uma faixa conhecida do FastAPI, deixar o próprio FastAPI selecionar Starlette compatível e testar upgrades. Fonte: [política de versões FastAPI](https://fastapi.tiangolo.com/deployment/versions/).

### Decisão

- Candidata inicial: `fastapi==0.139.2`, instalada com Uvicorn explícito e lock completo. Por ter sido publicada um dia antes desta pesquisa, só entra no baseline após regressão; se falhar, usar a última patch comprovada da mesma faixa e registrar a exceção.
- Não fixar Starlette manualmente fora da resolução do FastAPI.
- Endpoints fazem validação, autorização, transações curtas e enfileiramento; captura e inferência ficam em workers/serviços fora do event loop.
- Dimensionar workers considerando uma conexão/pool e memória por processo. A documentação de containers ressalta o trade-off entre múltiplos processos e memória. Fonte: [FastAPI em containers](https://fastapi.tiangolo.com/deployment/docker/).
- Evitar extras/CLIs de nuvem não utilizados; manter dependências do servidor separadas das de visão e desktop.

## 5. PySide6

### Avaliação

PySide6 é o binding oficial Qt for Python. A documentação atual requer Python 3.10+, recomenda ambiente virtual e informa que os wheels incluem os binários Qt. O PyPI classifica Python 3.11 e 3.12 e publica wheels ABI3. Fontes: [getting started](https://doc.qt.io/qtforpython-6/gettingstarted.html) e [PySide6 no PyPI](https://pypi.org/project/PySide6/).

Vantagens:

- toolkit desktop maduro e multiplataforma;
- sinais/slots e `QThread` permitem isolar captura/trabalho sem tocar widgets fora da thread principal;
- Qt Widgets atende uma console operacional densa; QML pode ser avaliado depois;
- ferramentas oficiais de deployment existem.

Desvantagens/riscos:

- wheels e distribuição final são grandes;
- bloquear o event loop congela toda a interface;
- empacotamento de plugins de plataforma/multimídia precisa de teste por SO;
- licença LGPLv3/GPLv3/comercial e módulos eventualmente GPL-only exigem decisão jurídica/empacotamento.

Fontes: [exemplo oficial de threads e sinais](https://doc.qt.io/qtforpython-6/examples/example_widgets_thread_signals.html), [sinais/slots](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html), [deployment](https://doc.qt.io/qtforpython-6/deployment/index.html), [licenciamento Qt for Python](https://doc.qt.io/qtforpython-6/) e [obrigações LGPL da Qt](https://www.qt.io/development/open-source-lgpl-obligations).

### Decisão

- Candidata: `PySide6==6.11.1`.
- Todos os widgets e imagens da tela são atualizados na thread principal.
- Workers publicam DTOs/frames limitados por sinais enfileirados; a GUI nunca recebe objetos de sessão SQLAlchemy nem controla o ciclo de vida do modelo diretamente.
- Usar fila “latest frame” limitada para não acumular RAM quando a renderização é mais lenta que a câmera.
- Fazer spike de empacotamento e revisar LGPL/comercial antes de distribuir executável. Este documento não é parecer jurídico.

## 6. PostgreSQL local vs Supabase

### Comparação

| Critério | PostgreSQL local/LAN | Supabase gerenciado | Supabase self-hosted |
|---|---|---|---|
| Núcleo | PostgreSQL controlado pela equipe | PostgreSQL dedicado por projeto mais Auth, API, Realtime, Storage e serviços da plataforma | conjunto Supabase operado pela própria equipe |
| Offline no cliente | não elimina cache/fila local, mas funciona sem Internet na LAN | não elimina cache/fila; depende da conectividade até a região | depende da rede até a instalação |
| Biometria | pode permanecer na rede/local sob controle direto | exige avaliar região, contrato/DPA, subprocessadores, egress e política LGPD | dados ficam no ambiente escolhido, mas toda a segurança/operação é local |
| Operação | patch, TLS, SCRAM, backup, restore, monitoramento e HA são responsabilidade local | boa parte da plataforma é gerenciada conforme plano | provisionamento, hardening, manutenção, HA, backup/DR e monitoramento são responsabilidade local |
| Portabilidade | PostgreSQL padrão; máxima transparência | PostgreSQL no núcleo, mas APIs/serviços adicionais podem gerar acoplamento | PostgreSQL mais uma pilha de serviços |
| Backup | política/RPO/RTO precisam ser implementados e restaurados em teste | recursos e retenção variam por plano; objetos de Storage não são restaurados pelo backup do banco | recursos gerenciados como PITR/branching não vêm automaticamente |
| Complexidade V1 | banco + extensão | fornecedor e serviços potencialmente duplicados pelo FastAPI | maior quantidade de componentes sem valor necessário para V1 |

Supabase documenta que cada projeto gerenciado tem PostgreSQL dedicado e adiciona Auth, APIs, Realtime e Storage. A arquitetura continua baseada em PostgreSQL, o que ajuda portabilidade quando são usados padrões do banco. Fontes: [visão da plataforma](https://supabase.com/docs/guides/platform) e [arquitetura](https://supabase.com/docs/guides/getting-started/architecture).

No self-hosting, a própria documentação atribui ao operador provisioning, hardening, manutenção do PostgreSQL, alta disponibilidade, backup/recuperação e monitoramento; recursos gerenciados como branching, backups e PITR não são automaticamente equivalentes. Fonte: [self-hosting Supabase](https://supabase.com/docs/guides/self-hosting).

No serviço gerenciado, backups e retenção dependem do plano; backups do banco não restauram objetos deletados do Storage. Fonte: [backups Supabase](https://supabase.com/docs/guides/platform/backups).

PostgreSQL mantém cada major por cinco anos. Na data de corte, 18.4 é o minor corrente do major 18, suportado até 2030-11-14; 17.10 é suportado até 2029-11-08. A política manda usar sempre o minor corrente. Fontes: [política de versões](https://www.postgresql.org/support/versioning/) e [lançamento PostgreSQL 18](https://www.postgresql.org/about/news/postgresql-18-released-3142/).

### Decisão

1. PostgreSQL 18.4 local/LAN é a fonte canônica inicial; atualizar para minors 18.x após backup, teste de restore e regressão.
2. Todos os clientes acessam dados centrais pelo FastAPI; nenhuma GUI recebe credenciais diretas do banco ou do Supabase.
3. Usar TLS quando a conexão sair do host, autenticação SCRAM, papéis de menor privilégio, banco não exposto à Internet e segredo fora do repositório.
4. Definir backup criptografado, retenção, RPO/RTO, restauração periódica e monitoramento antes de dados reais.
5. Manter migrations SQLAlchemy/Alembic portáveis. Recursos exclusivos Supabase só entram por decisão explícita.
6. Reavaliar Supabase gerenciado se operação, disponibilidade ou acesso remoto justificarem; antes disso, confirmar região disponível, DPA/termos, requisitos LGPD, plano, egress, backup/PITR, extensão pgvector e teste de restore.
7. Não implantar a pilha Supabase self-hosted na V1: ela adiciona serviços que o FastAPI já cobre e não transfere a responsabilidade operacional.

### Lacunas

- Topologia final (mesmo host, servidor LAN ou datacenter), SO e método de instalação do PostgreSQL não foram definidos.
- RPO, RTO, volume de eventos/imagens e janela de retenção são desconhecidos.
- Não houve teste de restore, failover, upgrade PG 18 ou extensão pgvector no SO alvo.
- Região, custo, termos, DPA e requisitos de residência de dados do Supabase devem ser pesquisados no momento de uma eventual adoção; não são presumidos aqui.
- A documentação de upgrade self-hosted observada usa PostgreSQL 17 como default, enquanto o baseline local proposto é PG 18; migração entre ambientes exige compatibilidade comprovada, não dump/restore presumido. Fonte: [upgrade self-hosted para PG 17](https://supabase.com/docs/guides/self-hosting/postgres-upgrade-17).

## 7. SQLAlchemy e Alembic

### Avaliação

SQLAlchemy 2.0.51 é a linha estável observada; 2.1.0b3 era beta e não deve ser adotada. O dialeto PostgreSQL suporta Psycopg 3 em modo sync e async. Fontes: [SQLAlchemy 2.0 ORM](https://docs.sqlalchemy.org/en/20/orm/), [dialeto PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) e [PyPI](https://pypi.org/project/SQLAlchemy/).

Alembic 1.18.5 fornece histórico de schema, upgrades/downgrades e autogenerate. A documentação alerta que autogenerate não é perfeito e que as migrations candidatas devem ser revisadas/corrigidas manualmente. Fontes: [Alembic no PyPI](https://pypi.org/project/alembic/), [changelog](https://alembic.sqlalchemy.org/en/latest/changelog.html) e [limitações de autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html).

Vantagens:

- mapeamento tipado, unit of work e queries parametrizadas;
- suporte PostgreSQL/Psycopg 3 e opção sync/async;
- migrations reproduzíveis e revisáveis;
- integração pgvector-python com SQLAlchemy/Psycopg.

Desvantagens/riscos:

- lazy loading em contexto async pode causar I/O implícito/`MissingGreenlet`;
- `Session`/`AsyncSession` não deve ser compartilhada entre threads/tasks concorrentes;
- abstração não substitui conhecimento de SQL, índices, locks e plano de execução;
- downgrade destrutivo pode ser impossível; rollback de aplicação não equivale sempre a downgrade de schema.

### Decisão

- `SQLAlchemy==2.0.51` e `Alembic==1.18.5` como candidatas; Psycopg 3 terá versão fixada no lock após o resolver.
- Sessão por request/unidade de trabalho e sessão distinta por tarefa; nunca guardar sessão em singleton ou widget.
- Servidor pode usar `AsyncSession` para I/O concorrente; migrations permanecem sync e controladas.
- Relacionamentos necessários são carregados explicitamente; evitar lazy I/O em async.
- Produção usa somente Alembic; `metadata.create_all()` fica restrito a testes descartáveis.
- Cada migration é imutável após publicada, revisada, testada em banco vazio e em cópia da versão anterior; backup/restore é o plano para alterações irreversíveis.
- Extensão `vector` é criada por migration explícita e o startup falha com diagnóstico se a versão não atender ao mínimo.

## 8. pgvector vs FAISS

### Comparação

| Critério | pgvector 0.8.5 | FAISS 1.14.3 |
|---|---|---|
| Papel ideal | índice vetorial junto aos dados relacionais canônicos | biblioteca de busca vetorial em memória/arquivo, CPU/GPU |
| Consistência | transação ACID com pessoa, status, permissão, versão e embedding | aplicação precisa coordenar índice e banco, inclusive falhas parciais |
| Filtros | SQL, joins, RLS/políticas e filtros relacionais | filtros/metadados precisam ser implementados ao redor do índice |
| Busca exata | padrão, com recall perfeito | índices `Flat` exatos |
| Busca aproximada | HNSW e IVFFlat | várias famílias de índices e quantização |
| HNSW | melhor trade-off speed/recall que IVFFlat segundo o projeto, sem treinamento; build usa mais memória | HNSW disponível entre vários algoritmos |
| GPU | depende do PostgreSQL/CPU; sem aceleração CUDA padrão | pacote GPU oficial; wheels observados somente para Linux |
| Windows | extensão requer build Visual C++/`nmake` ou imagem/empacotamento adequado | `faiss-cpu` publica wheels Windows 3.11/3.12; GPU não |
| Backup/restore | segue backup/PITR do PostgreSQL | arquivo/índice e metadados precisam de versionamento, checksum e rebuild |
| Escala | adequada ao desconhecido atual; precisa de benchmark | especialmente forte em coleções muito grandes e/ou GPU, mas a escala necessária não foi informada |

pgvector faz busca exata por padrão e suporta HNSW/IVFFlat para busca aproximada, além de distância L2, produto interno e cosseno. O tipo `vector` armazena até 16.000 dimensões; índices HNSW/IVFFlat do tipo `vector` suportam até 2.000, portanto embeddings faciais usuais de 512 dimensões cabem — a dimensão real ainda será escolhida. O projeto recomenda monitorar recall comparando resultados aproximados com a busca exata. Fonte: [repositório pgvector](https://github.com/pgvector/pgvector).

O changelog 0.8.x registra correções relevantes: 0.8.3 corrigiu possível corrupção de índice HNSW e regressão no PostgreSQL 18; 0.8.4 corrigiu erros de vacuum HNSW; 0.8.5 é a versão observada mais recente. Por isso, não aceitar versão antiga por conveniência do instalador. Fonte: [changelog pgvector](https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md).

FAISS oferece busca exata/aproximada, índices comprimidos e CPU/GPU. O guia oficial de instalação ainda mostrava conda 1.14.2 enquanto o release/PyPI já apresentava 1.14.3; isso é drift documental e deve ser tratado por smoke test. O build fonte exige C++20, CMake e BLAS, com CUDA opcional. Fontes: [repositório FAISS](https://github.com/facebookresearch/faiss), [instalação oficial](https://github.com/facebookresearch/faiss/blob/main/INSTALL.md), [faiss-cpu 1.14.3](https://pypi.org/project/faiss-cpu/1.14.3/) e [faiss-gpu](https://pypi.org/project/faiss-gpu/).

### Decisão

1. Central: `pgvector==0.8.5` e adaptador `pgvector==0.5.0` no Python.
2. Começar com busca exata e embeddings normalizados. Para vetores L2-normalizados, comparar cosseno ou produto interno de forma consistente com a especificação do modelo; não misturar métricas/limiares.
3. Indexar apenas após medir cardinalidade e p95. HNSW é a primeira candidata se a busca exata não cumprir SLO; calibrar `m`, `ef_construction` e `ef_search` por recall, memória e latência.
4. Filtros de pessoa ativa, local, permissão, versão/modelo e tenant devem ocorrer na consulta canônica; validar plano com `EXPLAIN (ANALYZE, BUFFERS)`.
5. FAISS não é fonte de verdade da V1. Só adotá-lo no cliente se o cache autorizado for grande o bastante para justificar a complexidade.
6. Se FAISS entrar, construir um índice novo por `embedding_set_version`, validar dimensão/modelo/checksum, trocar atomicamente, manter tombstones e conseguir reconstruir tudo do banco/cache assinado.

### Lacunas

- Quantidade de pessoas/templates por pessoa e frequência de atualização são desconhecidas.
- Não há SLO de latência/recall nem benchmark exato vs HNSW vs FAISS.
- A instalação pgvector 0.8.5 em PostgreSQL 18 no Windows alvo não foi executada.
- Requisitos de multi-tenant e filtros por local/permissão ainda não foram fechados; eles afetam estratégia de índice.

## 9. Compatibilidade Python 3.11 vs 3.12

### Ciclo de vida

Em 2026-07-17, Python 3.11 e 3.12 já estão em fase de correções de segurança. 3.11 termina em 2027-10 e 3.12 em 2028-10. As releases atuais 3.11.15 e 3.12.13, ambas de 2026-03-03, são source-only; os últimos instaladores binários oficiais dessas séries foram 3.11.9 e 3.12.10. Fontes: [status das versões CPython](https://devguide.python.org/versions/), [Python 3.11.15](https://www.python.org/downloads/release/python-31115/) e [Python 3.12.13](https://www.python.org/downloads/release/python-31213/).

Python 3.12 removeu `distutils` da stdlib e `venv` deixou de instalar `setuptools` por padrão, podendo quebrar pacotes/builds antigos. Fonte: [What’s New in Python 3.12](https://docs.python.org/3/whatsnew/3.12.html).

### Matriz de evidência

Legenda: **confirmado** = metadata/classificador e/ou wheel oficial adequado; **condicional** = metadata ampla, mas stack completa precisa de execução; **não declarado** = o projeto não publica suporte explícito suficiente.

| Componente | Python 3.11 | Python 3.12 | Evidência/limite |
|---|---|---|---|
| InsightFace 1.0.1 | não declarado | não declarado | wheel universal sem `Requires-Python`; upload ter sido feito por CPython 3.11 não é garantia de runtime |
| DeepFace 0.0.100 | condicional | condicional | declara `>=3.7`; TensorFlow oficial lista 3.9–3.12, mas o conjunto de backends não foi resolvido/testado |
| OpenCV 4.13/5.0 | confirmado | confirmado | wheels oficiais para ambos |
| ONNX Runtime 1.27 CPU | confirmado | confirmado | `>=3.11` e wheels CPython por SO |
| ONNX Runtime 1.27 GPU | confirmado quanto ao wheel | confirmado quanto ao wheel | wheel não confirma driver/CUDA/cuDNN/modelo |
| FastAPI 0.139.2 | confirmado | confirmado | `>=3.10` e classificadores |
| PySide6 6.11.1 | confirmado | confirmado | `>=3.10`, ABI3 e classificadores |
| SQLAlchemy 2.0.51 | confirmado | confirmado | metadata e wheels |
| Alembic 1.18.5 | confirmado | confirmado | `>=3.10`, wheel universal |
| pgvector-python 0.5.0 | confirmado | confirmado | `>=3.10`, wheel universal |
| FAISS CPU 1.14.3 | confirmado | confirmado | wheels Windows/Linux/macOS observados |
| FAISS GPU 1.14.3 | confirmado somente Linux | confirmado somente Linux | sem wheel GPU nativo Windows observado |

### Decisão

- Baseline pretendido: `Python >=3.12,<3.13`, usando uma distribuição confiável que forneça o patch de segurança e lock por SO.
- CI/smoke inicial: 3.11 e 3.12 para expor regressões de dependências; a release de produção suporta apenas as combinações que passarem a matriz completa.
- Se InsightFace ou outro componente essencial falhar em 3.12, 3.11 pode ser fallback temporário, com risco aceito e plano de migração antes de 2027-10.
- A frase “3.12 validado” só pode ser usada depois de instalação limpa, `pip check`, imports, inferência CPU, câmera, banco e empacotamento no SO alvo. Esta pesquisa confirma **disponibilidade declarada**, não execução.
- Como as releases de segurança atuais não trazem instaladores oficiais, registrar fornecedor/distribuição, patch exato, checksum e política de atualização. Não congelar para sempre em 3.12.10 só porque foi o último instalador python.org.

## 10. Topologia de dependências e instalação

Separar dependências e artefatos reduz conflito e superfície:

| Perfil | Conteúdo | Regra |
|---|---|---|
| `server` | FastAPI, Uvicorn, SQLAlchemy, Alembic, Psycopg, pgvector-python | não importa Qt, OpenCV ou modelo facial |
| `desktop` | PySide6, cliente HTTP, DTOs | não recebe credenciais do PostgreSQL |
| `vision-cpu` | OpenCV único, InsightFace/adaptador, `onnxruntime` | perfil obrigatório e sempre testado |
| `vision-nvidia` | OpenCV único, InsightFace/adaptador, `onnxruntime-gpu` | artefato separado; não coexistir com ORT CPU |
| `research` | DeepFace e comparadores | nunca entra no executável/servidor de produção |
| `dev` | testes, lint, type check, SCA/SBOM | sem pesos de produção no repositório |

Regras:

1. Gerar locks distintos por SO, arquitetura, Python e perfil CPU/GPU; usar hashes quando a ferramenta permitir.
2. Executar `pip check` e inventariar distribuições após instalar; garantir exatamente um pacote `cv2` e uma variante ORT.
3. Não usar `--no-deps` como solução permanente para os requisitos rígidos do InsightFace. Se for necessária substituição/override, ela deve estar expressa no lock e coberta por teste.
4. Modelos são artefatos versionados separadamente com `model_id`, versão, dimensão, preprocessamento, normalização, distância, limiar, licença, URL/origem, SHA-256 e assinatura quando disponível.
5. Não fazer download automático de pesos no primeiro uso em produção; provisionar de origem aprovada e verificar hash antes de carregar.
6. Fazer SCA/SBOM do wheel e das bibliotecas nativas incluídas; PyPI metadata não cobre CVEs ou licença de todos os binários empacotados.

## 11. Gates obrigatórios antes de fechar o stack

| Prioridade | Gate | Evidência de saída |
|---|---|---|
| P0 | Licença do detector, embedding e vivacidade | registro de origem, termos aprovados, finalidade, redistribuição e hashes |
| P0 | Resolver limpo em Python 3.12 nos SOs alvo | lock reproduzível, `pip check`, SBOM e imports |
| P0 | Resolver de fallback Python 3.11 | resultado documentado; sem tratá-lo automaticamente como versão suportada |
| P0 | Conflito InsightFace/OpenCV/ORT | exatamente um `cv2` e um ORT; CPU e GPU em artefatos separados |
| P0 | Inferência CPU real | modelo carrega, dimensão/normalização conferem, resultado determinístico dentro da tolerância |
| P0 | GPU real quando exigida | provider CUDA disponível/efetivo, matriz driver/CUDA/cuDNN registrada, teste de carga e fallback |
| P0 | Banco e extensão | PostgreSQL 18 minor corrente + pgvector 0.8.5, migrations up/down/restore e consulta vetorial |
| P1 | Captura | USB, arquivo e RTSP autorizados; timeout, reconexão, backend e liberação de recursos |
| P1 | Benchmark facial | FAR/FRR, desconhecidos, condições reais, p95/p99, CPU/GPU, memória e múltiplas câmeras |
| P1 | pgvector exato/HNSW e eventual FAISS | recall contra exato, latência, RAM, build/rebuild, filtro e exclusão |
| P1 | GUI | thread principal responsiva, filas limitadas, encerramento e empacotamento por SO |
| P1 | API | testes de contrato/auth/sync; inferência não bloqueia event loop; memória por worker |
| P1 | Backup e restore | RPO/RTO definidos e restauração completa testada, inclusive extensão/vetores |
| P1 | Licenças de distribuição | Qt/PySide6, OpenCV/FFmpeg, ORT, modelos e notices revisados |

## 12. Riscos principais e decisões que não podem ser presumidas

| Risco/lacuna | Impacto | Tratamento |
|---|---|---|
| Pesos InsightFace sem licença de produção aprovada | impede uso legal/comercial | bloquear promoção; escolher/licenciar modelo alternativo |
| Python 3.12 não declarado pelo InsightFace | instalação ou inferência pode falhar | spike 3.12; 3.11 temporário somente com plano de saída |
| OpenCV headless vs dependência `opencv-python` | namespaces/binários conflitantes | resolver/lock e import test; isolar worker se necessário |
| ORT 1.27 sem matriz CUDA/cuDNN detalhada na tabela consultada | GPU pode importar mas não executar | probe e inferência no hardware real; registrar DLLs/driver |
| OpenCV 5 muito recente | regressão de API/codecs | iniciar 4.13 e criar campanha de upgrade |
| FastAPI 0.139.2 publicado há um dia | regressão ainda não observada localmente | testes e pin; rollback para patch comprovada |
| DeepFace/TensorFlow em Windows GPU | stack grande ou WSL2 | não usar no núcleo |
| pgvector/PG18 no Windows ainda sem build testado | instalação pode exigir toolchain | spike com instalador/container alvo e backup/restore |
| Busca aproximada sem cardinalidade/SLO | falso ganho e perda de recall | exata primeiro; HNSW/FAISS só após benchmark |
| FAISS separado do banco | identidade removida pode permanecer no índice | índice versionado, troca atômica, tombstones e rebuild |
| PostgreSQL local sem operação definida | perda/indisponibilidade | patch, TLS, backup, restore, monitoramento e RPO/RTO |
| Supabase sem análise de região/contrato | risco LGPD, custo e lock-in | avaliação formal somente se adotado |
| Qt/PySide6 sem decisão de licença | bloqueio de distribuição | revisão jurídica e teste de empacotamento |
| Hardware/carga desconhecidos | nenhuma promessa de FPS/latência é válida | inventário e benchmark representativo |
| Dados biométricos sem base legal/política | risco alto a titulares e conformidade | privacy-by-design, minimização, retenção, acesso e aprovação antes de dados reais |

## Decisão final desta pesquisa

O caminho com menor acoplamento para a primeira implementação é:

`Python 3.12 → OpenCV 4.13 → adaptador facial → modelo ONNX licenciado → ONNX Runtime CPU/GPU → PySide6 no cliente; FastAPI → SQLAlchemy/Alembic → PostgreSQL 18 + pgvector no servidor.`

Essa é uma **hipótese técnica priorizada**, não uma stack validada. Três condições são bloqueadoras antes de implementar reconhecimento real: licença dos pesos, smoke test Python/OpenCV/InsightFace/ORT por plataforma e benchmark/calibração em dados autorizados representativos. DeepFace e FAISS permanecem ferramentas opcionais de avaliação/otimização, não dependências centrais. Após a confirmação de contexto, Supabase tornou-se o candidato preferencial de hospedagem PostgreSQL, ainda sem prova de conceito e sem substituir o desenho offline/local.

## Índice de fontes primárias/oficiais

### Reconhecimento facial

- [InsightFace — repositório e termos de modelos](https://github.com/deepinsight/insightface)
- [InsightFace — PyPI](https://pypi.org/project/insightface/)
- [InsightFace — setup.py](https://github.com/deepinsight/insightface/blob/master/python-package/setup.py)
- [DeepFace — repositório](https://github.com/serengil/deepface)
- [DeepFace — PyPI](https://pypi.org/project/deepface/)
- [DeepFace — requirements](https://github.com/serengil/deepface/blob/master/requirements.txt)
- [FaceNet — artigo original](https://arxiv.org/abs/1503.03832)
- [FaceNet — implementação primária popular](https://github.com/davidsandberg/facenet)
- [TensorFlow — instalação pip](https://www.tensorflow.org/install/pip)
- [TensorFlow — builds Windows](https://www.tensorflow.org/install/source_windows)

### Visão, inferência e interface

- [opencv-python — PyPI](https://pypi.org/project/opencv-python/)
- [OpenCV — VideoCapture](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html)
- [OpenCV — backends Video I/O](https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html)
- [ONNX Runtime — instalação](https://onnxruntime.ai/docs/install/)
- [ONNX Runtime — Execution Providers](https://onnxruntime.ai/docs/execution-providers/)
- [ONNX Runtime — CUDA EP](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)
- [ONNX Runtime CPU — PyPI](https://pypi.org/project/onnxruntime/)
- [ONNX Runtime GPU — PyPI](https://pypi.org/project/onnxruntime-gpu/)
- [PySide6 — PyPI](https://pypi.org/project/PySide6/)
- [Qt for Python — getting started](https://doc.qt.io/qtforpython-6/gettingstarted.html)
- [Qt — obrigações LGPL](https://www.qt.io/development/open-source-lgpl-obligations)

### API, banco e vetores

- [FastAPI — PyPI](https://pypi.org/project/fastapi/)
- [FastAPI — política de versões](https://fastapi.tiangolo.com/deployment/versions/)
- [PostgreSQL — versionamento](https://www.postgresql.org/support/versioning/)
- [PostgreSQL 18 — anúncio](https://www.postgresql.org/about/news/postgresql-18-released-3142/)
- [Supabase — plataforma](https://supabase.com/docs/guides/platform)
- [Supabase — self-hosting](https://supabase.com/docs/guides/self-hosting)
- [Supabase — backups](https://supabase.com/docs/guides/platform/backups)
- [SQLAlchemy 2.0 — documentação](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy — PyPI](https://pypi.org/project/SQLAlchemy/)
- [Alembic — documentação](https://alembic.sqlalchemy.org/en/latest/)
- [Alembic — PyPI](https://pypi.org/project/alembic/)
- [pgvector — repositório](https://github.com/pgvector/pgvector)
- [pgvector-python — repositório](https://github.com/pgvector/pgvector-python)
- [FAISS — repositório](https://github.com/facebookresearch/faiss)
- [FAISS — instalação](https://github.com/facebookresearch/faiss/blob/main/INSTALL.md)

### Python

- [CPython Developer Guide — status das versões](https://devguide.python.org/versions/)
- [Python 3.12.13](https://www.python.org/downloads/release/python-31213/)
- [Python 3.11.15](https://www.python.org/downloads/release/python-31115/)
- [Python 3.12 — mudanças](https://docs.python.org/3/whatsnew/3.12.html)
