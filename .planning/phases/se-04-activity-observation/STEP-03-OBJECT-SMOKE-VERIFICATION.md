# Verificação — SE-04 Etapa 3B

Data: 2026-08-22  
Ambiente: Conda `smart-environment`, Python 3.12, CPU, Windows

## Resultado funcional

Com limiar `0.25`, o modelo encontrou um laptop na primeira imagem (`0.310`) e um na
segunda (`0.815`). As duas caixas foram aprovadas visualmente. A terceira imagem, que
contém celulares pequenos/ocluídos, retornou zero objetos. A média observada foi `43,2 ms`
por imagem. O diagnóstico separado em `0.10` repetiu exatamente duas detecções de laptop
e zero de celular, teclado ou mouse.

Esse resultado demonstra o caminho técnico de objetos, mas reprova o sinal de celular
para o enquadramento atual. Zero detecções significa somente ausência de evidência do
modelo, não ausência real do objeto e muito menos evidência de trabalho.

## Evidências

| Comando ou procedimento | Resultado |
|---|---|
| `conda run -n smart-environment python scripts/smoke_office_objects.py` | 3 imagens; 2 laptops; 0 celulares; média 43,2 ms |
| mesmo script com `--confidence-threshold 0.10` e saída separada | resultado inalterado |
| inspeção visual das três prévias | 2 caixas de laptop corretas; terceira sem caixa |
| `conda run -n smart-environment python -m pytest -q` | 97 testes e 11 subtestes aprovados |
| `conda run -n smart-environment python -m ruff check app main.py scripts tests` | aprovado |
| `conda run -n smart-environment python -m ruff format --check app main.py scripts tests` | 43 arquivos formatados |
| `conda run -n smart-environment python -m mypy app main.py tests` | 40 arquivos sem erro |
| `conda run -n smart-environment python -m compileall -q app main.py scripts tests` | aprovado |
| `conda run -n smart-environment python -m build --no-isolation` | sdist e wheel gerados |
| `conda run -n smart-environment python -m pip check` | nenhuma dependência quebrada |

## Privacidade e dados

- `activity_classification_performed=false` e `webcam_opened=false` no relatório;
- relatório e prévias ficam em `data/evaluations/office-object-smoke/`, fora do Git;
- nenhuma imagem da webcam/celular, identidade, evento ou estado de atividade foi criado;
- o material de entrada continua restrito ao TCC não comercial.

## Próximo checkpoint

Montar, com autorização, um teste curto e aproximado na câmera contendo laptop visível,
celular visível e ausência de objeto. Esse teste deve encerrar e liberar a câmera; ainda
não deve integrar objetos ao monitor contínuo ou classificar atividade.
