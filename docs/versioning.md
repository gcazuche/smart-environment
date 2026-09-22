# Versões do Smart Environment

## Marco atual — migração Django, 20/09/2026

O candidato desta entrega é **`v0.3.0-alpha.1`**, correspondente à versão Python
**`0.3.0a1`**. É um marco de implementação e validação local: não declara aceite
do Supabase real, implantação na VM, precisão de detecção nem vídeo físico a 30 FPS.

As tags locais **`v0.1.0` e `v0.2.0`** foram verificadas nesta data e continuam
apontando para `f5b1f18`. Não mover, recriar ou trocar o conteúdo dessas tags.
O candidato só deve ser criado depois da revisão do conjunto publicável, dos testes
e da consulta das tags remotas. Nenhum commit, tag ou push foi executado automaticamente.

O novo caminho web usa Django, HTML/CSS e JavaScript puro em `app/web/`. O painel
React/TypeScript em `dashboard/` permanece como legado preservado, fora do runtime
e do caminho de CI principal da nova aplicação.

## Combinado de trabalho

Ao concluir uma funcionalidade coerente, correção importante ou teste de aceite,
registraremos o marco no `CHANGELOG.md`, informaremos a validação e entregaremos
os comandos. Commit, tag, push e GitHub Release dependem de ação sua ou autorização
explícita; não serão executados automaticamente.

Um **commit** acrescenta um ponto ao histórico. Um `git push` normal publica novos
commits sem apagar os anteriores. Uma **tag anotada** identifica permanentemente
o commit escolhido. Uma **GitHub Release** é uma apresentação opcional dessa tag.

## Preparar v0.3.0-alpha.1 sem misturar trabalhos

### 1. Conferir repositório, branch e tags

Na raiz do projeto, execute um comando por vez e pare diante de erro. Confira
também se `origin` é o repositório correto; não compartilhe saídas que contenham
credenciais de um remoto mal configurado.

```text
git status --short
git branch --show-current
git diff --stat
git tag --list v0.3.0-alpha.1
git ls-remote --tags origin "refs/tags/v0.3.0-alpha.1" "refs/tags/v0.3.0-alpha.1^{}"
```

Os comandos de publicação pressupõem a branch `main`. Se estiver em outra branch,
revise o fluxo antes de continuar. Só use este número se a tag não existir localmente
nem no remoto. Falha na consulta remota **não** comprova ausência da tag. Se já
existir, preserve-a e escolha outro número; nunca use `--force` para substituí-la.

### 2. Selecionar explicitamente a entrega Django

O worktree contém alterações anteriores de visão, desempenho e outras etapas.
Não use `git add .` nem `git add -A`. A lista abaixo é um ponto de partida
revisável: confira os arquivos existentes e o índice antes de executar. Nunca
adicione arquivos ignorados usando `-f`.

```text
git add -- app/web manage.py environment.web.yml
git add -- config/web/.env.example config/web/Caddyfile.example config/web/smart-environment-web.service
git add -- tests/test_web_foundation.py tests/test_web_auth.py tests/test_web_dashboard.py tests/test_web_repository.py tests/test_web_video.py
git add -- tests/test_web_backend.py tests/test_web_security.py tests/test_web_forms.py tests/test_web_reports.py tests/conftest.py
git add -- tests/js/web-login.test.mjs tests/js/web-video.test.mjs scripts/preview_django_fixture.py
git add -- docs/django-migration.md .planning/phases/se-13-django-migration
```

Se algum nome não existir nesta cópia, pare e consulte `git status --short`.
Não substitua a lista por um comando que inclua todo o repositório. Acrescente
eventuais testes com outro nome individualmente depois de revisar seu conteúdo.

Manifests, documentação e configurações compartilhadas já contêm trabalho anterior.
Selecione **somente os trechos da migração**, usando revisão interativa:

```text
git add -p -- .gitignore pyproject.toml environment.yml environment.ci.yml app/__init__.py
git add -p -- README.md CHANGELOG.md docs/versioning.md docs/continuous-integration.md docs/server-processing.md
git add -p -- .planning/STATE.md .planning/BACKLOG.md .github/workflows/ci.yml
```

`git add -p` permite aceitar, recusar, dividir ou editar cada trecho. Um arquivo
novo ainda não rastreado não aparece normalmente nesse modo: leia-o primeiro e,
se pertencer integralmente à entrega, adicione o caminho individualmente. O conjunto
selecionado precisa continuar instalável e testável, inclusive versão `0.3.0a1`
e dependências web; não selecione uma dependência pela metade.

Ficam fora desta seleção:

- `dashboard/` e mudanças do painel legado não necessárias à entrega Django;
- experimentos de visão, dataset, revisão e mudanças de servidor alheias à migração;
- o arquivo particular `h origin main`;
- `.env.local`, `.env.web.local`, senhas, tokens e configurações locais de câmeras;
- fotos, pesos, dados de sessão, SQLite, filas e relatórios privados.

Não reverta, apague ou descarte esses arquivos para preparar a versão: apenas
deixe o trabalho não relacionado fora do índice.

### 3. Revisar o que será publicado e validar

```text
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
git diff --cached
```

Revise também arquivos que já estavam no índice. O diff final não pode conter
segredos, endereços com credenciais, fotos ou banco de sessões. Exemplos de
configuração devem conter somente valores de exemplo. Não cole o diff em chat
antes de conferir segredos.

Execute a validação do [guia Django](django-migration.md) usando Conda
`smart-environment`. Testes do worktree inteiro não comprovam que a seleção parcial
funciona: o **snapshot publicável precisa ser validado também**, preferencialmente
em cópia isolada do candidato, sem configurações privadas ou arquivos não
selecionados. Se não puder validar esse conjunto, mantenha a publicação pendente.

### 4. Criar commit novo e depois tag nova

Somente após a revisão e os testes aprovados:

```text
git commit -m "feat(web): migra Smart Environment para Django"
git log -1 --oneline
git show --stat HEAD
```

Confira se o commit contém exatamente a entrega validada. Consulte novamente as
tags locais e remotas para evitar um nome que passou a existir:

```text
git tag --list v0.3.0-alpha.1
git ls-remote --tags origin "refs/tags/v0.3.0-alpha.1" "refs/tags/v0.3.0-alpha.1^{}"
```

Se ambas as consultas concluírem com sucesso e não retornarem essa tag:

```text
git tag -a v0.3.0-alpha.1 -m "Smart Environment v0.3.0-alpha.1: aplicacao Django"
git show --no-patch v0.3.0-alpha.1
git push origin main
git push origin v0.3.0-alpha.1
```

Só crie a tag após o commit validado; só envie a tag se o envio da branch tiver
sucesso. Se o remoto recusar o push, pare e confira o histórico; não use
`push --force`. Após confirmar a publicação, registre data e commit no changelog
em outro commit documental, sem mover a tag. A Release opcional deve ser marcada
como **pré-lançamento** e citar as pendências de aceite real.

## Histórico preservado — não é o roteiro atual

- **09/09/2026, v0.1.0:** marco salvo pelo usuário em `f5b1f18`. Não comprovava
  VM, câmeras físicas ou 30 FPS. Achados de dependências daquela rodada são
  históricos, não uma auditoria atual.
- **Plano de 09/09, v0.2.0:** desempenho local, backup/restore da outbox e CI.
  Esse nome posteriormente passou a existir como tag local no mesmo `f5b1f18`.
  Os antigos comandos para criar v0.2.0 não devem ser repetidos. Alterações que
  ficaram apenas no worktree não foram incorporadas automaticamente à tag.
- **19/09/2026, fundação Django:** estrutura e login apenas visual. Essa limitação
  foi superada pela implementação atual; não descreve o funcionamento de hoje.

## Próximas versões

- `v0.3.0-alpha.2`: eventual próxima revisão do candidato, se o nome estiver livre.
- `v0.3.0`: após os critérios acordados para fechar a migração e o aceite.
- `v1.0.0`: marco estável após critérios funcionais, de segurança e operação aprovados.

Esses números são exemplos, não versões existentes. Cada entrega usa novo commit
e nova tag. Não é necessário criar tag para cada pequeno commit. Nunca reutilize
ou apague tags publicadas para esconder uma correção.

## Consultar versão antiga sem desfazer a atual

```text
git log --oneline --decorate -12
git show --stat v0.1.0
git worktree add --detach ../Multicam-v0.1.0 v0.1.0
```

O último comando cria outra pasta, que ainda não deve existir, com o código daquela
tag; não reverte a pasta atual. Não use `reset --hard` nem restaure arquivos sobre
mudanças em andamento. Antes de executar código antigo, confira dependências e
compatibilidade com o banco. Não reaplique migrações ou bootstrap antigos no mesmo
Supabase para testar uma versão anterior.

**Git não é backup do ambiente inteiro.** Configurações privadas, segredos, mapas
de câmera, pesos, fotos, Supabase, sessões e fila SQLite ficam fora da tag.
Transfira configurações autorizadas por meio privado e mantenha backups separados.
Outra máquina precisa do Conda `smart-environment` e configuração própria; modelos
de detecção são necessários na máquina que processa imagens, não para abrir o site.

Referências: [tags no Git](https://git-scm.com/book/en/v2/Git-Basics-Tagging) e
[pastas de trabalho separadas](https://git-scm.com/docs/git-worktree).
