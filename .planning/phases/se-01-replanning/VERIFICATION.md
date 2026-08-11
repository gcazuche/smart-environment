# SE-01 — Verificação

Data: 2026-08-11
Escopo: rebaseline documental
Resultado: aprovado com ressalvas explícitas abaixo

## Critérios

| Verificação | Resultado |
|---|---|
| documentos ativos usam Smart Environment e o mesmo MVP | aprovado |
| reconhecimento facial/distração não são funcionalidade ativa | aprovado |
| antiga Fase 2 está marcada como superada | aprovado |
| cada requisito tem fase, prioridade, dependência, aceite e status | aprovado — 61/61 |
| referências explícitas de requisitos resolvem | aprovado — 59 IDs distintos |
| incertezas permanecem `unspecified` | aprovado |
| referências internas `.planning/*` existem | aprovado |
| somente documentação mudou | aprovado — 18 arquivos modificados + 6 novos, todos Markdown |
| código/dependências/dados/câmera/serviço externo não mudaram | aprovado |
| revisão independente dos P1/P2 | aprovado após correções |

## Evidência documental

```powershell
git diff --check
rg -n "[ \t]+$" README.md .planning
git diff --name-only
git ls-files --others --exclude-standard
```

Resultados: diff sem erro; zero trailing whitespace; 24 arquivos documentais; nenhum
arquivo fora de `README.md`/`.planning/`; 382 headings revisados sem salto/estrutura
inválida; 24/24 arquivos UTF-8 válidos, sem BOM, NUL, caractere de substituição ou
assinatura de mojibake. Os avisos LF→CRLF decorrem de `core.autocrlf=true` e não
representam erro no diff atual.

Validações estruturais em PowerShell confirmaram:

- 61 IDs de requisito únicos;
- 61/61 requisitos com descrição, fase, prioridade, dependências, aceite e status;
- 59 referências explícitas distintas em ROADMAP/BACKLOG/STATE resolvidas;
- 38 tarefas únicas e sequenciais de `SEB-001` a `SEB-038`;
- 12 etapas `SE-*` no roadmap;
- todos os caminhos `.planning/*` citados existem;
- nenhum documento ativo aponta `DB-02-02` como próxima tarefa;
- SE-02 está não iniciada e não autorizada.

As duas fontes oficiais citadas em `RESEARCH.md` foram abertas com sucesso em
2026-08-11: texto compilado da LGPD no Planalto e orientação de RIPD da ANPD.

## Gates preservados da fundação

| Comando | Resultado real |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | aprovado — 28 testes em 1,25 s |
| `.\.venv\Scripts\ruff.exe check app main.py tests` | aprovado |
| `.\.venv\Scripts\ruff.exe format --check app main.py tests` | aprovado — 13 arquivos |
| `.\.venv\Scripts\mypy.exe app main.py tests` | aprovado — 13 arquivos |
| `.\.venv\Scripts\python.exe -m compileall -q app main.py tests` | aprovado |
| `.\.venv\Scripts\python.exe -m app doctor --json` | aprovado, sem falhas |
| `uv build --offline --cache-dir .uv-cache` | aprovado — sdist e wheel 0.1.0 |
| `uv --cache-dir .uv-cache pip check --python .\.venv\Scripts\python.exe` | aprovado — 15 pacotes compatíveis |

## Correções originadas pela revisão independente

- antecipado o gate de câmera real: SE-03 só permite cenário controlado vazio ou o
  próprio responsável informado; terceiros aguardam transparência completa de SE-07;
- corrigido diagrama para `dashboard → API → Supabase`;
- movido `AST-003` para SE-10 e alinhadas as dependências do backlog;
- corrigidas fases de `SEC-003` e `OPS-002` e a rastreabilidade transversal;
- diferenciados operador do sistema e operador de tratamento;
- substituída a verificação provisória por estes resultados reais.

## Ressalvas e pendências

- Termos faciais continuam apenas em histórico, pesquisa marcada como legado, ADR
  supersedida ou declaração explícita de fora do escopo.
- O smoke da webcam é evidência histórica e não foi repetido em SE-01.
- O comando `doctor` e o pacote ainda exibem nomes/campos legados; sua migração não foi
  autorizada nesta etapa documental e está registrada como decisão futura.
- Nenhum teste valida requisitos funcionais `SE-*` além da consistência do planejamento.
- Supabase, OpenCV da aplicação, detector e frontend continuam não implementados.
- Nenhum secret scan, SAST, SCA ou DAST novo foi executado; o checkpoint não alega esses
  resultados. Os gates serão introduzidos nas fases que alterarem dependências/superfície.
