# Verificação — SE-04 Etapa 1

Data: 2026-08-22  
Ambiente: Conda `smart-environment`, Python 3.12, Windows

## Escopo verificado

- contrato dos cinco estados observáveis;
- política `office-computer` e seus limiares iniciais;
- imutabilidade, validação de configuração e salvaguardas de linguagem;
- regressão do conjunto Python existente.

Nenhum teste abriu webcam, acessou o celular, classificou frames, persistiu evento ou
conectou Supabase.

## Evidências

| Comando | Resultado |
|---|---|
| `conda run -n smart-environment python -m pytest -q` | 77 testes e 5 subtestes aprovados |
| `conda run -n smart-environment ruff check app main.py tests` | aprovado |
| `conda run -n smart-environment ruff format --check app main.py tests` | 30 arquivos formatados |
| `conda run -n smart-environment mypy app main.py tests` | 30 arquivos sem erro |
| `conda run -n smart-environment python -m compileall -q app main.py tests` | aprovado |
| `conda run -n smart-environment python -m build --no-isolation` | sdist e wheel gerados |
| `conda run -n smart-environment python -m pip check` | nenhuma dependência quebrada |

O build isolado padrão tentou baixar `setuptools` e foi impedido pela política de rede
do ambiente. Como nenhuma dependência mudou, o build foi repetido sem isolamento usando
exclusivamente as versões já instaladas no Conda e terminou com sucesso.

## Resultado

Os critérios da Etapa 1 foram atendidos. A implementação deliberadamente não decide o
estado de nenhum frame: isso depende das próximas etapas de área, sinais e agregação.

## Próximo checkpoint autorizado

Etapa 2: configurar a área da estação de trabalho. Pose, objetos, tracking, classificador,
dashboard e persistência permanecem fora desse próximo recorte.
