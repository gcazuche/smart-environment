# DJ-01 — evidências e continuidade

Data: 2026-09-19. Windows, ambiente Conda `smart-environment`, Python 3.12.13,
Django 5.2.17. Branch `main`, HEAD `f5b1f18`; tags locais `v0.1.0` e `v0.2.0`
preservadas. Árvore já continha muitos incrementos locais antes deste trabalho.

## Entrega

- Fundação Django e login visual, não autenticação operacional.
- HTML/CSS/JavaScript puro, logos copiadas sem alteração e sem runtime Node.
- Rotas públicas restritas a GET/HEAD; painel/admin/cadastro não implementados.
- Sem import/inicialização de câmera/modelo, `.env`, Supabase, sessão ou banco.
- Settings apenas locais; segredo efêmero em memória e DEBUG não servem para deploy.
- Guia em `docs/django-migration.md`; plano/contratos em `SPEC.md`.

## Validação executada

| Verificação | Evidência |
|---|---|
| Instalação `python -m pip install -e ".[web]"` no Conda | Django 5.2.17 instalado, sem `.venv`/base |
| `python manage.py check` | zero problemas, nada silenciado |
| `python -m pytest tests/test_web_foundation.py -q` | 13 testes e 11 subtestes aprovados |
| Suíte Python completa após ajuste final do favicon | **560 testes e 263 subtestes aprovados**, sem skips/falhas; 9,66 s |
| `node --check app/web/static/web/login.js` | sintaxe aprovada |
| `node --test tests/js/web-login.test.mjs` | 2 testes aprovados; também incluídos na chamada com glob `*.test.mjs` |
| Ruff check/formato em manage.py, app/web e teste web | check aprovado; 7 fontes já formatadas |
| `python -m pip check` | nenhuma dependência incompatível; não é auditoria de vulnerabilidades |
| `python -m build --wheel --no-isolation --outdir data/builds/django-foundation-20260919` | wheel gerado; 6 assets/templates presentes e SHA-256 idênticos aos fontes |
| Revisão estática independente | sem bloqueante DJ-01; ressalvas de bind/ALLOWED_HOSTS e deploy registradas |

Pytest completo usou a pasta temporária explícita
`C:/Users/angel/AppData/Local/Temp/smart-environment-django-pytest-final-20260919`.
Comandos executados com `conda run --no-capture-output -n smart-environment`.
Contagens incluem toda a árvore de trabalho, não representam uma versão publicada.
Wheel permanece em `data/` ignorado; não foi instalado/testado em ambiente limpo.

## QA no navegador

Servidor temporário em `127.0.0.1:8000`, somente loopback, encerrado após inspeção.
No navegador integrado, tela renderizou com CSS e as duas logos carregadas (dimensões
naturais 363×154 e 167×137). Campos e Entrar estavam desabilitados com aviso visível.
Botão de detalhes fechou e reabriu conteúdo com estado acessível correspondente.
Inspeção desktop e viewport solicitado de 390×844; largura útil observada de 375 px,
sem transbordamento horizontal (scrollWidth=clientWidth=375). Override restaurado,
aba temporária fechada. Não é auditoria completa WCAG nem teste de todos os dispositivos.

Houve uma busca automática inicial por favicon inexistente. Depois foi adicionado
`rel=icon` apontando para o símbolo existente e a suíte completa foi repetida; não
foi aberta nova rodada visual apenas para o ícone. Assets e render final cobertos por teste.

## Arquivos do incremento

Criados: `manage.py`, `app/web/` (Python/templates/static), `tests/test_web_foundation.py`,
`tests/js/web-login.test.mjs`, guia Django, SPEC e este relatório.
Alterados pontualmente: `pyproject.toml`, `environment.yml`, `environment.ci.yml`,
`.github/workflows/ci.yml`, `docs/continuous-integration.md`, README, CHANGELOG,
`.planning/BACKLOG.md` e `.planning/STATE.md`. Dois arquivos de CI já eram não rastreados
antes do incremento; alterações anteriores neles foram preservadas.

Sem alteração neste incremento em `dashboard/`, detector/modelos, dados, configuração
Supabase ou processamento do servidor. O arquivo `h origin main` foi preservado.
Nenhum commit/tag/push, migração de banco, bootstrap, câmera, treino, VM ou dado remoto.

## Limites / próximo passo

- Autenticação, papéis, consultas/CRUD, WHEP/telemetria, relatórios/CSV e corte do
  TypeScript ainda pendentes. Nenhuma promessa de paridade ou ganho de FPS.
- DEBUG/chave efêmera são impeditivos para login real/deploy: corrigir em DJ-02.
- ALLOWED_HOSTS não é firewall; o bind explícito de loopback é essencial.
- Sem auditoria SCA nova, Mypy Django/stubs, QA completo de acessibilidade, instalação
  Linux limpa ou execução do workflow GitHub. Dashboard legado não foi reconstruído.
- Pendências antigas de dependências frontend, VM e revisão humana de imagens continuam.

Retomada: ler STATE/README e SPEC SE-13, conferir git status; executar DJ-02 (projetar
sessão server-side, integrar Supabase Auth e vínculo existente, CSRF, logout/refresh,
admin/viewer e testes negativos). Não repetir bootstrap, expor segredos, copiar o login
local simulado do legado ou retirar TypeScript antes de migrar suas funcionalidades.

