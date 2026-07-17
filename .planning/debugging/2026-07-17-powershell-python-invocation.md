# Debug — invocação do Python empacotado no PowerShell

- **Data:** 2026-07-17
- **Ambiente:** Windows, PowerShell, runtime Python fora do `PATH`
- **Comando:** `"C:\\...\\python.exe" -m unittest ...`
- **Esperado:** iniciar o interpretador e executar o módulo.
- **Observado:** parser do PowerShell retornou `Token '-m' inesperado` antes de criar o
  processo Python. Os quatro comandos Python tiveram o mesmo erro; `git diff --check`
  passou.

## Hipóteses e evidências

1. **Erro no código Python:** rejeitada, pois nenhum processo Python iniciou.
2. **Caminho inexistente:** rejeitada; o mesmo executável informou a versão em chamada
   anterior.
3. **Sintaxe PowerShell:** confirmada. Um caminho executável entre aspas exige o
   operador de invocação `&` quando recebe argumentos.

## Causa raiz

Ausência do operador `&` antes do caminho entre aspas.

## Correção

Repetir cada comando no formato:

```powershell
& 'C:\...\python.exe' -m unittest discover -s tests -v
```

## Testes e regressões

Reexecutar unittest, compileall, parser TOML e smoke test; manter `git diff --check`.
Este registro não implica que os testes da aplicação passaram.
