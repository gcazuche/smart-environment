# Verificação — SE-04 Etapa 3A

Data: 2026-08-22  
Ambiente: Conda `smart-environment`, Python 3.12, Windows

## Resultado

As três imagens publicadas foram baixadas e decodificadas nas dimensões declaradas:
`640×757`, `640×819` e `1080×1440`. A inspeção visual confirmou escritórios reais
ocupados; a terceira cena inclui uso visível de celulares, mas nenhum rótulo de intenção
foi atribuído. O conjunto automático anterior foi rejeitado e removido.

## Evidências

| Comando ou procedimento | Resultado |
|---|---|
| `conda run -n smart-environment python scripts/prepare_workstation_references.py` | 3 imagens validadas e manifest gerado |
| mesmo comando com `--output-directory data/datasets/workstation-references-download-smoke` vazio | download real do zero aprovado; cópia temporária removida |
| inspeção visual de uma a uma | 3 cenas de escritório aprovadas |
| `git check-ignore` nos JPEGs e manifest | conteúdo local ignorado pelo Git |
| `conda run -n smart-environment python -m pytest -q` | 92 testes e 11 subtestes aprovados |
| `conda run -n smart-environment python -m ruff check app main.py scripts tests` | aprovado |
| `conda run -n smart-environment python -m ruff format --check app main.py scripts tests` | 37 arquivos formatados |
| `conda run -n smart-environment python -m mypy app main.py tests` | 35 arquivos sem erro |
| `conda run -n smart-environment python -m compileall -q app main.py scripts tests` | aprovado |
| `conda run -n smart-environment python -m build --no-isolation` | sdist e wheel gerados |
| `conda run -n smart-environment python -m pip check` | nenhuma dependência quebrada |

## Limites

- todas as três cenas estão ocupadas e têm múltiplas pessoas;
- o conjunto não oferece negativos, variedade suficiente ou ground truth de atividade;
- a licença é não comercial;
- nenhum detector de objetos foi executado nesta subetapa;
- webcam, celular, dashboard, persistência e Supabase não foram alterados.

## Próximo checkpoint

Executar somente o primeiro smoke de sinais de computador/celular nessas referências e
na câmera autorizada. Permanecem fora do recorte: pose, tracking temporal, classificador
de atividade, persistência e Supabase.
