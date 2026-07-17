# Fase 1 — Plano atômico

## Estado de execução

| Tarefa | Estado | Evidência/lacuna |
|---|---|---|
| FND-01-01 | concluída | documentos e pesquisas persistidos e revisados |
| FND-01-02 | concluída com ressalva | configuração testada em 3.12; 3.11 não executado |
| FND-01-03 | concluída | diagnóstico, testes de CLI e smoke doctor aprovados |
| FND-01-04 | pendente | logging/redaction e fronteira global de exceções |
| FND-01-05 | pendente | pytest/Ruff/mypy, instalação limpa e lockfile |

## FND-01-01 — Inicializar contexto GSD

- **Tipo:** documentação/especificação
- **Prioridade:** P0
- **Risco:** médio
- **Objetivo:** persistir escopo, requisitos, decisões, riscos, roadmap e lacunas.
- **Arquivos:** `.planning/*.md`, `.planning/research/*.md`.
- **Dependências:** pedido original e inventário do repositório.
- **Passos:** normalizar entradas; pesquisar fontes oficiais; criar documentos;
  revisar consistência e links.
- **Aceite:** documentos obrigatórios existem; fatos/premissas estão separados;
  nenhum requisito futuro está marcado como implementado.
- **Validação:** leitura cruzada, `git diff --check` e inventário de arquivos.
- **Resultado esperado:** contexto retomável.
- **Reversão:** remover apenas arquivos da inicialização ainda não commitidos.
- **Impacto de segurança:** ameaça/privacidade deixam de ser implícitas.

## FND-01-02 — Criar pacote e configuração mínima

- **Tipo:** implementação
- **Prioridade:** P0
- **Risco:** baixo
- **Objetivo:** disponibilizar pacote Python e configuração validada por ambiente.
- **Arquivos:** `pyproject.toml`, `.env.example`, `.gitignore`, `app/__init__.py`,
  `app/configuration/settings.py`, `main.py`.
- **Dependências:** FND-01-01.
- **Passos:** declarar metadata; implementar parsing sem segredos; validar enums,
  booleanos e limites; documentar execução.
- **Aceite:** import funciona em Python 3.11+; valores inválidos falham claramente;
  nenhum segredo possui default real.
- **Validação:** unit tests e `compileall`.
- **Resultado esperado:** base configurável e instalável.
- **Reversão:** reverter os arquivos listados.
- **Impacto de segurança:** evita configuração silenciosa/insegura.

## FND-01-03 — Diagnóstico executável

- **Tipo:** implementação/teste
- **Prioridade:** P0
- **Risco:** baixo
- **Objetivo:** verificar runtime e estrutura sem mutar o sistema.
- **Arquivos:** `app/diagnostics.py`, `app/__main__.py`, `tests/`.
- **Dependências:** FND-01-02.
- **Passos:** modelar checks; saída humana/JSON; exit code por falha; testes.
- **Aceite:** `doctor --json` é parseável; checks não revelam segredos; teste cobre
  sucesso e configuração inválida.
- **Validação:** `unittest`, `compileall`, smoke test.
- **Resultado esperado:** primeira etapa funcional observável.
- **Reversão:** remover comando/diagnóstico e testes relacionados.
- **Impacto de segurança:** diagnóstico somente leitura e saída sanitizada.

## FND-01-04 — Adicionar logging e tratamento global seguros

- **Tipo:** implementação/segurança
- **Prioridade:** P0
- **Risco:** médio
- **Objetivo:** atender o baseline de SEC-007 sem vazar dados em erros.
- **Arquivos:** `app/logging.py` (nome final a confirmar), entrypoints e testes.
- **Dependências:** FND-01-02..03.
- **Passos:** definir eventos/redaction/correlation ID; capturar apenas na fronteira;
  preservar causa no log protegido; testar destino indisponível e saída pública.
- **Aceite:** nenhum `except` vazio; mensagem pública sanitizada; correlação e nível;
  encerramento coerente; rotação/destino definidos.
- **Validação:** testes de exceção, redaction, correlação e falha do logger.
- **Resultado esperado:** limite de erro seguro e observável.
- **Reversão:** voltar ao entrypoint anterior e manter incidente registrado.
- **Impacto de segurança:** reduz exposição de paths, tokens e dados biométricos.

## FND-01-05 — Validar e fechar a fase

- **Tipo:** verificação/documentação
- **Prioridade:** P0
- **Risco:** baixo
- **Objetivo:** executar gates disponíveis e registrar gaps honestamente.
- **Arquivos:** `VERIFICATION.md`, `SUMMARY.md`, `.planning/STATE.md`,
  `.planning/CHANGELOG.md`.
- **Dependências:** FND-01-01..04.
- **Passos:** testar; revisar diff/segredos; registrar comandos/resultados; atualizar
  próximo passo.
- **Aceite:** nenhuma falha crítica; testes disponíveis passam; gaps têm responsável.
- **Validação:** `git diff --check`, `git status --short` e evidências registradas.
- **Resultado esperado:** fase aprovada ou aprovada com ressalvas.
- **Reversão:** corrigir estado para refletir a tarefa realmente concluída.
- **Impacto de segurança:** impede alegação de validação não executada.
