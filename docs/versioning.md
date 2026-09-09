# Versões do Smart Environment

## Combinado de trabalho

Ao concluir uma funcionalidade coerente, uma correção importante ou um teste de aceite,
registraremos o marco no `CHANGELOG.md`, informaremos o que foi validado e entregaremos
os comandos para salvar a versão. Commit, tag, push e GitHub Release dependem de uma
ação sua ou de autorização explícita; não serão executados automaticamente.

Um **commit** adiciona um ponto ao histórico. Um `git push` normal publica os novos
commits: ele não apaga as versões anteriores. Uma **tag anotada**, como `v0.1.0`, dá um
nome permanente ao commit escolhido. Uma **GitHub Release** é uma apresentação opcional
dessa tag, com notas e anexos; não é necessária para preservar o código.

## Primeiro marco proposto: v0.1.0

**Estado: preparado, não publicado.** Em 08/09/2026, a branch local era `main`, o HEAD
era `332af86` e não havia tags locais. As tags remotas não foram consultadas. Os
manifests Python e dashboard já declaram `0.1.0`; não houve mudança de versão neles.

Esta primeira tag deve apontar para o **novo commit revisado** que inclui o servidor,
e não para o HEAD antigo. Ela será um marco de código, não uma afirmação de que a VM,
as câmeras físicas ou os 30 FPS já passaram pelo teste de aceite.
O audit atual tem 2 entradas altas ainda abertas; esta tag é um marco interno de
desenvolvimento, não uma liberação para exposição pública.

### 1. Conferir antes de salvar

No terminal aberto na raiz do projeto, os comandos abaixo funcionam em PowerShell
e no Prompt de Comando. Execute um por vez e pare se algum falhar:

```text
git status --short
git branch --show-current
git diff --stat
git tag --list v0.1.0
git ls-remote --tags origin "refs/tags/v0.1.0" "refs/tags/v0.1.0^{}"
```

Continue somente se a branch for `main`, o remoto for o repositório esperado e a tag
não existir localmente nem no remoto. Se já existir, preserve-a e escolha o próximo
número adequado; nunca use `--force` para trocar seu conteúdo. Falha de rede na
consulta remota não significa ausência da tag.

### 2. Selecionar e revisar o incremento

Após os testes e a revisão, selecione explicitamente estes arquivos do incremento.
Confira o `status`: inclua separadamente outros arquivos legítimos da entrega e não
use `git add .` sem revisar. Arquivos ignorados não devem ser adicionados com `-f`.

```text
git add -- .gitignore .planning/STATE.md .planning/BACKLOG.md README.md CHANGELOG.md environment.server.yml
git add -- "app/server/*.py" "tests/test_server_*.py" tests/test_streaming_tools.py scripts/streaming.py
git add -- config/server/.env.example config/server/server.example.toml config/server/mediamtx.example.yml config/server/Caddyfile.example config/server/smart-environment-media.service config/server/smart-environment.service
git add -- dashboard/.env.example dashboard/app/globals.css dashboard/app/page.tsx dashboard/app/stream-client.ts dashboard/app/stream-preview.tsx dashboard/app/processing-server.tsx dashboard/tests/processing-server.test.mjs
git add -- dashboard/package.json dashboard/package-lock.json dashboard/tests/image-runtime.test.mjs
git add -- docs/server-processing.md docs/versioning.md docs/dependency-hardening.md
git diff --cached --stat
git diff --cached --check
git diff --cached
```

A última revisão deve conter somente mudanças desta entrega, sem chaves, senhas,
imagens reais, arquivos de banco ou configurações privadas. O índice pode já conter
arquivos de um trabalho anterior: eles também aparecerão nesta revisão.

### 3. Criar e publicar a versão

```text
git commit -m "feat: prepara processamento em servidor e marco v0.1.0"
git tag -a v0.1.0 -m "Smart Environment v0.1.0: processamento em servidor preparado"
git show --no-patch v0.1.0
git push origin main
git push origin v0.1.0
```

Só crie a tag se o commit anterior tiver terminado com sucesso. Só envie a tag se o
push da branch tiver sucesso. Se o remoto recusar um push, pare e confira o histórico;
não substitua o comando por `push --force`. Após conferir os dois envios, registre a
data e o commit publicados no changelog em um commit documental posterior, sem mover
a tag já criada. No GitHub, uma Release pode usar essa mesma tag e as notas do changelog.

## Próximas versões

- `v0.1.1`: correções compatíveis do marco `v0.1.0`.
- `v0.2.0`: um novo conjunto de funcionalidades, documentando eventuais incompatibilidades.
- `v1.0.0`: marco estável somente após critérios de aceite e operação definidos e aprovados.

Esses números são exemplos de planejamento, não versões existentes. Cada entrega usa
um novo commit e uma nova tag; versões de manifests e locks devem acompanhar a versão
real quando fizermos a próxima atualização. Não é necessário criar uma tag para todo
pequeno commit. Nunca reutilize ou apague tags publicadas para esconder uma correção.

## Consultar uma versão antiga sem desfazer a atual

```text
git log --oneline --decorate -12
git show --stat v0.1.0
git worktree add --detach ../Multicam-v0.1.0 v0.1.0
```

O último comando cria outra pasta, que ainda não deve existir, com o código daquela
tag; ele não reverte a pasta atual. Não use `reset --hard` nem restaure arquivos sobre
mudanças em andamento. Antes de executar o código antigo, confira suas dependências
e a compatibilidade com o banco atual. Não reaplique migrações ou bootstrap antigos
contra o mesmo Supabase apenas para testar uma versão anterior.

**Git não é backup do ambiente inteiro.** `.env.local`, segredos do servidor, mapas
locais das câmeras, pesos dos modelos, fotos, Supabase e a fila SQLite ficam fora da
tag. Transfira configurações autorizadas por meio privado e mantenha backups separados
dos dados. A outra máquina continua precisando do Conda `smart-environment`, das
dependências, do modelo e de seus próprios arquivos de configuração.

Referências: [tags no Git](https://git-scm.com/book/en/v2/Git-Basics-Tagging) e
[pastas de trabalho separadas](https://git-scm.com/docs/git-worktree).
