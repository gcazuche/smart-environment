# Debug — linha acima do limite no logging seguro

- **Data:** 2026-07-17
- **Ambiente:** Python 3.12.13, Windows, workspace local
- **Comando:** verificação local de linhas Python acima de 100 caracteres
- **Esperado:** nenhuma linha maior que o limite configurado no Ruff
- **Observado:** `app/observability/secure_logging.py:67` possuía 108 caracteres

## Hipóteses e evidência

- O teste funcional não detectaria o problema porque a sintaxe era válida.
- A saída apontou uma única expressão de substituição regex escrita em uma linha.

## Causa raiz

Formatação manual não alinhada ao limite de 100 caracteres de `pyproject.toml`.

## Correção

Quebrar a chamada de `_LABELED_SECRET.sub` em múltiplas linhas sem alterar comportamento.

## Regressão

Verificação de comprimento sem achados, **26/26** testes unitários aprovados e
`compileall` com exit code 0 após o endurecimento final.
