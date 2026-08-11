# Estratégia de testes — Smart Environment

Atualizado em: 2026-08-11

## Princípios

- Teste automatizado usa dados sintéticos e fonte de câmera simulada por padrão.
- Hardware, Supabase e piloto são suítes separadas, autorizadas e claramente rotuladas.
- Resultado não executado permanece pendente; planejamento não é evidência funcional.
- Cenários negativos e de falha têm o mesmo peso do happy path.
- Privacidade é invariant verificável: pixels não persistem nem saem da borda no MVP.
- Uma contagem é estimativa técnica; qualidade deve ser medida por condição de uso.

## Camadas

| Camada | Exemplos | Gate |
|---|---|---|
| Unidade | validação, agregação, fórmulas, estados, RBAC | cada tarefa |
| Contrato | `CameraSource`, evento, API, repositories | mudança de interface/schema |
| Integração local | SQLite/outbox, migrações, lifecycle OpenCV simulado | SE-02 a SE-05 |
| Integração remota | Supabase Auth/RLS/Postgres/restore descartável | SE-02 e release |
| Interface | DOM, autenticação, gráfico, acessibilidade, responsividade | SE-06 |
| Visão | 0/1/N, oclusão, iluminação, densidade, FP/FN, latência | SE-04/SE-07 |
| E2E | webcam→evento→API→Supabase→dashboard | SE-07 |
| Segurança | abuso, autorização negativa, injection, segredo, SCA/SAST | incremental/SE-12 |
| Operação | rede offline, replay, soak, backup/restore, rollback, fail-safe | SE-07/SE-12 |

## Gates existentes da fundação

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app main.py tests
.\.venv\Scripts\ruff.exe format --check app main.py tests
.\.venv\Scripts\mypy.exe app main.py tests
.\.venv\Scripts\python.exe -m compileall -q app main.py tests
uv build --offline --cache-dir .uv-cache
uv --cache-dir .uv-cache pip check --python .\.venv\Scripts\python.exe
```

Esses comandos validam a fundação atual. Ainda não validam OpenCV, detector,
Supabase, API, interface ou qualquer requisito Smart Environment funcional.

## Suítes obrigatórias por etapa

### SE-02 — Dados e Supabase

- schema vazio→head e downgrade suportado;
- FK, unique/check, timestamps e rollback;
- payload proibido sem identidade/pixels;
- Auth expiração/revogação;
- matriz RBAC e RLS positiva/negativa, inclusive cross-tenant;
- backup/restore e eliminação em projeto autorizado;
- nenhuma chave privilegiada no bundle, log ou Git.

### SE-03 — Uma webcam

- fonte simulada determinística, frame inválido, EOF e timeout;
- start/stop/restart e abertura/leitura/liberação repetidas;
- fila cheia, cancelamento e shutdown;
- smoke manual autorizado em hardware, separado do CI, em cenário controlado vazio
  ou somente com o próprio responsável informado; nenhuma terceira pessoa é capturada
  antes do gate completo de transparência de SE-07;
- arquivos/banco/rede/logs inspecionados para ausência de pixels.

### SE-04 — Ocupação

- 0, 1 e N pessoas; parcial/oclusão; luz e densidade;
- falso positivo, falso negativo e estado `unknown`;
- agregação de janela, deduplicação e tracking efêmero;
- CPU, memória, FPS e latência preliminares;
- nenhum identificador persiste entre janelas/câmeras;
- relatório informa amostra, condições e limitações, sem acurácia inventada.

### SE-05/SE-06 — API e web

- schema/tamanho/tipo inválidos, injection, replay e rate limit;
- queda de rede, resposta perdida, retry e idempotência;
- loading/empty/stale/unknown/error;
- acesso por papel/local e tentativa cross-tenant;
- teclado, foco, contraste, zoom, mobile e informação sem depender de cor;
- ausência de stream, pixel, URL de câmera ou segredo no navegador.

### SE-07 — Piloto

- vertical completa com uma webcam e um ambiente autorizados;
- latência, disponibilidade, erro de contagem, CPU/RAM/rede e custo;
- retenção, exclusão, exportação e restore;
- aviso, enquadramento e áreas autorizadas conferidos;
- critérios de interrupção e rollback exercitados.

### SE-08 a SE-12

- fórmulas e timezone; estimativa versus medição;
- patrimônio/alerta sem acusação e com correção humana;
- deduplicação/canal de notificação;
- falha isolada por câmera e credencial revogada;
- carga/soak, SAST, SCA, segredos, SBOM, backup/restore e fail-safe.

## Invariant de zero persistência de frames

Antes e depois de um teste controlado, verificar explicitamente:

- arquivos nas áreas de dados/log/cache conhecidas;
- linhas/objetos gravados no banco e outbox;
- requisições de rede emitidas pelo processo;
- logs, exceções e artefatos de teste;
- memória/buffer liberado conforme contrato possível de observar.

O teste só sustenta o escopo inspecionado. Não usar frases genéricas como “nenhum
arquivo foi criado” quando a evidência verificou apenas um diretório.

## Dados de teste e piloto

- Preferir imagens/vídeos sintéticos ou datasets cuja licença e finalidade permitam o uso.
- Material de voluntários exige informação, autorização, escopo e descarte definidos.
- Não capturar áudio; não testar em banheiros, vestiários, descanso ou áreas privadas.
- Crianças/adolescentes e escolas ficam fora do primeiro piloto.
- Não commitar frames, exports, credenciais ou dados reais.

## Evidência mínima

Cada `VERIFICATION.md` registra data, ambiente, versão, comando/procedimento, escopo,
resultado, limitações, arquivos alterados e pendências. Hardware e serviço remoto só
contam quando a evidência identifica o ambiente autorizado sem expor segredo ou pessoa.
