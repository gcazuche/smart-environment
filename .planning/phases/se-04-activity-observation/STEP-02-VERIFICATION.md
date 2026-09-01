# Verificação — SE-04 Etapa 2

Data: 2026-08-22  
Ambiente: Conda `smart-environment`, Python 3.12, Windows

## Escopo verificado

- parsing e validação de áreas normalizadas;
- conversão segura para frames com resoluções diferentes;
- sobreposição geométrica e contagem agregada por câmera;
- desenho da área em cópia do frame e JPEG volátil;
- parâmetros independentes para webcam e celular;
- regressão do conjunto Python existente.

Nenhum teste abriu webcam, acessou o celular, identificou pessoas, classificou atividade,
persistiu pixels/eventos ou conectou Supabase.

## Evidências

| Comando | Resultado |
|---|---|
| `conda run -n smart-environment python -m pytest -q` | 87 testes e 11 subtestes aprovados |
| `conda run -n smart-environment ruff check app main.py tests` | aprovado |
| `conda run -n smart-environment ruff format --check app main.py tests` | 32 arquivos formatados |
| `conda run -n smart-environment mypy app main.py tests` | 32 arquivos sem erro |
| `conda run -n smart-environment python -m compileall -q app main.py tests` | aprovado |
| `conda run -n smart-environment python -m build --no-isolation` | sdist e wheel gerados |
| `conda run -n smart-environment python -m pip check` | nenhuma dependência quebrada |
| `conda run -n smart-environment npm run lint` em `dashboard/` | aprovado |
| `conda run -n smart-environment npm test` em `dashboard/` | build Vinext e 2 testes aprovados |

## Resultado e limite

Os critérios automatizáveis da Etapa 2 foram atendidos. O padrão cobre o frame inteiro,
portanto a calibração de coordenadas reais para cada enquadramento continua pendente e
deve ser feita visualmente com o próprio usuário. Nenhum estado de atividade é emitido.

## Próximo checkpoint autorizado

Etapa 3: detectar objetos relevantes ao contexto de escritório. Pose, tracking temporal,
classificação, persistência e Supabase continuam fora desse próximo recorte.
