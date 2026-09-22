# Validação contínua

O workflow `.github/workflows/ci.yml` prepara um ambiente Conda **smart-environment**
isolado em runner Ubuntu 24.04 para pull requests, pushes na main/codex e execução
manual. Não usa `.venv`, não instala o projeto no base, não faz deploy, não cria tags
e não recebe segredos do servidor, fotos, modelos ou credenciais Supabase.

O fluxo principal agora valida **Django + HTML/CSS/JavaScript puro**. Executa toda a
suíte Python com `python -m pytest -q`, `manage.py check`, Ruff e conferência de formato
de `manage.py`, `app/web/` e todos os testes `tests/test_web_*.py`, além de
`node --test tests/js/*.test.mjs`. Mantém Ruff/Mypy do processamento em `app/server/`
e Ruff dos testes do servidor. Node serve apenas para testar JavaScript: executar a
aplicação Django não depende de Node, npm, React ou TypeScript.

O job define `DJANGO_SETTINGS_MODULE=app.web.testing`, uma configuração hermética:
não lê arquivos privados `.env`, usa serviços remotos simulados e SQLite de teste,
sem consultar ou modificar o Supabase da organização. Os testes do player usam mocks,
sem conexão a câmeras ou à VM. Instalar dependências requer rede; o perfil CI omite
treino/exportação e pesos de modelos. O extra `web` instala as dependências Django.
A versão major de Node 22 e o instalador Miniforge são resolvidos no runner; isso não
é um lock completo da imagem de sistema.

## Legado preservado, execução manual separada

`dashboard/` permanece como referência/rollback do painel React/TypeScript anterior,
fora do runtime principal. Seus gates foram transferidos integralmente para
`.github/workflows/legacy-dashboard.yml`, acionável somente por **workflow_dispatch**:
instalação pelo lock com `npm ci --ignore-scripts`, build/testes offline, ESLint,
TypeScript e `npm audit --audit-level=high`. Nesse fluxo, os testes SQL com PGlite
continuam locais; não usam o banco da organização. Nenhum desses comandos é necessário
para iniciar o Django.

A separação marca a troca de aplicação ativa, **não a correção das dependências do
legado**. O último audit documentado em [dependency-hardening.md](dependency-hardening.md)
registrou duas entradas altas residuais em image-size/vinext. É um registro histórico,
não um audit novo. O gate manual continua falhando se detectar vulnerabilidades no
limiar configurado; não há `continue-on-error`, `--omit=dev` ou downgrade forçado para
aparentar aprovação. Não usar o legado exposto como aplicação de produção.

## Evidência e acompanhamento

As actions estão fixadas por SHA verificado nos repositórios oficiais, com token apenas
de leitura e sem credencial Git persistida. Não utiliza `pull_request_target`, scripts
de implantação, artefatos de dados ou permissões de escrita. Uma execução nova cancela
a anterior da mesma referência; prazo total de 20 minutos.

**Estado: workflows preparados, não executados no GitHub nesta entrega.** Os SHAs
das actions foram preservados da configuração anterior; não houve atualização nem
nova verificação remota desses pins. Conferência de arquivos e testes locais não
validam a resolução das dependências pelo runner. Só a execução remota poderá
comprovar a instalação limpa Linux e o ambiente do runner. Se uma etapa anterior
falhar, as posteriores não são executadas e não devem ser consideradas aprovadas.

Após publicar os commits, conferir a aba **Actions** e o log de cada etapa. Proteção
de branch com check obrigatório depende de configuração do repositório e não foi
habilitada automaticamente. Execuções em repositório privado podem consumir a cota
GitHub Actions da conta; nenhum runner foi contratado ou workflow disparado aqui.

Referências: [checkout](https://github.com/actions/checkout),
[setup-miniconda](https://github.com/conda-incubator/setup-miniconda).
