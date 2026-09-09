# SEC-01 — preparação de segurança antes da rede

## Correção complementar em 08/09/2026 — 2 entradas altas residuais

**Resultado: dependência sharp corrigida e compatibilidade local verificada; gate
global de segurança ainda não aprovado.** O audit completo passou de 6 para 2 entradas
altas (`image-size` e `vinext`), sem críticas. Não houve deploy, exploração, acesso a
câmeras, banco remoto ou VM. Todas as execuções usaram Conda `smart-environment`.

### Fronteira e alteração mínima

No Miniflare instalado, `imagesLocalFetcher` e `cfImageLocalFetcher` importam `sharp`
dinamicamente e decodificam o conteúdo de uma imagem recebida. A configuração atual
do dashboard não declara binding Images; não foi demonstrada uma entrada remota
explorável no produto. Ainda assim, o parser vulnerável estava instalado e poderia ser
usado pelas ferramentas. O invariante adotado é não resolver cópias de sharp anteriores
à correção e carregar libheif corrigida, mantendo decodificação e transformações válidas.

A consulta ao registro npm confirmou que mesmo `@cloudflare/vite-plugin@1.54.6`,
`wrangler@4.130.0` e `miniflare@5.20260908.0-alpha` ainda fixam sharp 0.35.2.
Atualizar apenas os pais não corrigiria este aviso. Foram preservadas as versões dos
pais e adicionado um override **limitado a `miniflare@5.20260903.0-alpha` → sharp 0.35.4**,
com regeneração do lock pelo npm. Isto é uma exceção explícita ao pin do fornecedor,
não uma correção já adotada pelo Miniflare nem uma supressão do audit. A API testada
permaneceu compatível. Não houve `--force`, downgrade ou edição de `node_modules`.

O [advisory do mantenedor](https://github.com/lovell/sharp/security/advisories/GHSA-rgj7-g3m4-5g8c)
indica sharp 0.35.4 / libheif 1.23.2 como corrigidos. O npm documenta
[overrides transitivos e delimitados por versão](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/#overrides).
Quando o pai passar a exigir uma versão corrigida, remover este override em um novo
incremento, após conferir toda a árvore e reexecutar os testes; não ampliar o override
silenciosamente para novas versões. Os changelogs
[0.35.3](https://sharp.pixelplumbing.com/changelog/v0.35.3/) e
[0.35.4](https://sharp.pixelplumbing.com/changelog/v0.35.4/) foram consultados.

### Evidência ordenada

- Antes da atualização, os controles de versão no novo `tests/image-runtime.test.mjs`
  falharam para o lock e a biblioteca carregada; PNG/JPEG/WebP/AVIF legítimos passaram.
  Isso reproduz a instalação afetada, **não uma exploração do heap**.
- `npm install --ignore-scripts`: resolveu sharp 0.35.4 e seus binários oficiais;
  o lock conserva as variantes Windows, Linux glibc e musl. Nenhum pacote alheio à
  cadeia sharp foi atualizado. `npm ci --ignore-scripts --dry-run` passou, verificando
  consistência do manifesto/lock, não uma instalação limpa completa.
- `node --test tests/image-runtime.test.mjs`: **5/5**. Verifica todas as cópias sharp
  do lock, a versão resolvida a partir do Miniflare, libheif efetivamente carregada,
  decodificação/redimensionamento dos quatro formatos, rejeição de bytes inválidos e
  AVIF truncado, além de AVIF → PNG pelo binding Images de um Miniflare temporário em
  loopback, sem telemetria ou requisição de dados externos. O runtime é encerrado ao final.
- Revisão local em passe separado conferiu os dois consumidores e cópias transitivas;
  delegação de revisão ficou indisponível. Não foram encontrados pins antigos adicionais.
- `npm test`: build + **60/60 testes**. `npm run lint` e `npm exec -- tsc --noEmit`: aprovados.
- `npm ls sharp miniflare @cloudflare/vite-plugin wrangler --all`: árvore válida,
  única resolução sharp 0.35.4. `npm audit --json`: saída 1 esperada pelas **2 altas**
  residuais, sem sharp/miniflare/wrangler/plugin entre os alertas.

A evidência da correção é a versão corrigida no lock **e no código/binário carregado**,
conforme o advisory; não foi executado exploit nem comprovada segurança geral do parser.
Execução nativa Ubuntu/Linux e instalação limpa em outra máquina continuam pendentes.
Não processar arquivos não confiáveis nem expor o servidor publicamente como se todos
os gates estivessem aprovados. O `image-size/latest` ainda era 2.0.2 no registro em 08/09;
seus avisos e a análise histórica abaixo continuam abertos.

Arquivos desta correção: `dashboard/package.json`, `dashboard/package-lock.json`,
`dashboard/tests/image-runtime.test.mjs` e documentos de evidência/continuidade.

## Baseline em 08/09/2026 — 6 entradas altas antes da correção

O `npm audit --json` completo foi reexecutado ao preparar o marco de desenvolvimento
v0.1.0 e retornou **6 entradas altas, 0 críticas**, sem alteração do manifesto/lock.
As entradas são `image-size`, `vinext`, `sharp`, `miniflare`, `wrangler` e
`@cloudflare/vite-plugin`; dependentes propagam um aviso, não representam seis falhas
independentes comprovadas no produto. O novo aviso é
[GHSA-rgj7-g3m4-5g8c](https://github.com/advisories/GHSA-rgj7-g3m4-5g8c), incluído na
base em 08/09. O advisory aponta sharp <0.35.4 e correção em 0.35.4; o lock atual usa
0.35.2. Atingibilidade/exploração no sistema atual não foi testada nesta rodada.

Naquele baseline ainda não havia atualização. A correção complementar acima substitui
esse estado; os números deste trecho são históricos. Não aplicar o downgrade automático
sugerido para Wrangler/plugin nem `audit fix --force`.

É possível guardar este snapshot como marco **interno de código** com limitações
expressas; isso não aprova deploy, servidor público ou processamento de arquivos não
confiáveis. Testes funcionais aprovados não anulam o gate de segurança não-zero.

O relatório abaixo preserva a evidência de 07/09 e seus números são históricos.

Data: 07/09/2026. Estado: **correções aplicadas; risco residual não suprimido**.

## Escopo e sequência

Fechar os avisos de dependências do dashboard antes de qualquer publicação/exposição.
Não muda a interface, banco, login, autorização, fontes de câmera nem os modelos.
Não cria Supabase, acessa VM, faz deploy, commit/push ou executa exploração de falhas.
A ativação remota DB-01 continua pendente para quando o usuário criar o projeto.

Baseline confirmado por `npm audit --json`: 19 entradas, sendo 16 altas, uma moderada
e duas baixas. Pacotes marcados como desenvolvimento também participam do servidor;
o audit completo é o gate relevante, não apenas `--omit=dev`.

## Plano mínimo e critérios de aceite

1. Conferir advisories primários, versões corrigidas e peer dependencies.
2. Atualizar versões explícitas necessárias e resolver transitivas dentro dos intervalos
   suportados. Não usar `--force`, suprimir avisos ou remover pacotes apenas para esconder
   findings. Conferir bibliotecas incorporadas pelo framework, não somente o npm audit.
3. Validar instalação, árvore de peers, build, testes, TypeScript e lint; manter dev
   server somente em loopback. Preservar marcas, streaming e estrutura Supabase.
4. Reexecutar audit completo e registrar qualquer risco residual ou teste não realizado.

Ativos/superfícies: credenciais futuras em arquivos ignorados, sessões do navegador,
servidor dev Windows, protocolo RSC, parsers de imagens de metadata e ferramentas de
build. Entradas remotas não recebem autorização automática para acessar arquivos locais.
Reversibilidade: mudanças ficam no manifesto/lock/configuração e testes do dashboard;
preservar todas as alterações existentes de DB-01 e ST-01 ao reverter um pacote.

## Evidência inicial

- Vite 8.0.13 é afetado no Windows; primeira correção da linha 8.0 é 8.0.16:
  [advisory oficial](https://github.com/vitejs/vite/security/advisories/GHSA-fx2h-pf6j-xcff).
- RSC exige a atualização coordenada de React/React DOM/RSC para 19.2.8:
  [advisory oficial](https://github.com/react/react/security/advisories/GHSA-wx67-qw84-cm4g).
- Peers e dependências serão conferidos no registro npm e no artefato instalado.
  Desaparecer do lockfile por ser incorporado em outro pacote não prova correção.

## Alterações aplicadas

| Componente | Antes | Depois |
| --- | --- | --- |
| React / React DOM / React Server DOM Webpack | 19.2.6 | 19.2.8 |
| Vite | 8.0.13 | 8.0.16 |
| Cloudflare Vite Plugin | 1.37.1 | 1.54.4 |
| Wrangler | 4.92.0 | 4.129.0 |
| Vinext / plugin-rsc | beta.2 / 0.5.26 | preservados |

Transitivas atualizadas pelo resolvedor, respeitando os intervalos dos pais, com
`npm install --ignore-scripts` e `npm audit fix --ignore-scripts`. Não foi usado
`--force`, `--legacy-peer-deps`, override de segurança ou patch em node_modules.
Supabase/PGlite e todo o trabalho DB-01/ST-01 foram preservados.

O plugin Cloudflare selecionado publica Miniflare `5.20260903.0-alpha`, Undici 7.29.0,
ws 8.21.0, sharp 0.35.2 e esbuild 0.28.1. O Miniflare é dependência do plugin estável,
não uma substituição manual. Build e inicialização local devem ser verificados;
isso não equivale a validar um deploy na Cloudflare ou uma execução na VM Ubuntu.

O servidor Vite passa a declarar `host: "localhost"` por padrão. Os metadados sociais
aceitam somente hosts conhecidos, sem refletir Host/X-Forwarded-Host arbitrário na URL
da imagem. Hosts novos exigem atualização explícita de `app/metadata-origin.ts`; em
host desconhecido, a página continua funcional, mas omite a imagem social absoluta.
Não houve troca das imagens, cores, páginas ou funcionalidades do painel.

## Risco residual: image-size 2.0.2

O audit após resolução retornou **2 entradas altas**, `image-size` e seu dependente
`vinext`, contra 19 iniciais. Os 17 outros avisos deixaram de ser reportados após as
correções. O gate de audit permanece não-zero; não há aceite automático para produção.

Não existe correção publicada de image-size posterior a 2.0.2 na consulta realizada.
O npm sugere Vinext beta.9, mas beta.6 incorporou a mesma biblioteca ao pacote e o
catálogo de beta.9 ainda fixa 2.0.2. Migrar para esconder o aviso não corrigiria os parsers.
Referências: [PR do empacotamento](https://github.com/cloudflare/vinext/pull/2913) e
[catálogo beta.9](https://raw.githubusercontent.com/cloudflare/vinext/vinext@1.0.0-beta.9/pnpm-workspace.yaml).

Revisão estática do Vinext beta.2 instalado identificou chamadas durante transformação
de imports de imagens locais e geração de metadados estáticos locais. O dashboard atual
não importa imagens como módulos e não tem arquivos de metadados de imagem em `app/`.
Seus três PNGs versionados em `public/` são referenciados por URLs textuais. Não foi
identificada entrada remota atual que alcance esse parser; isso **não prova ausência
geral de exploração** nem corrige a biblioteca. O otimizador do Worker usa ASSETS/IMAGES,
não essa biblioteca, nos caminhos inspecionados.

Controles enquanto a correção definitiva não existe: não executar build de mudanças
não revisadas com acesso a segredos, não converter uploads/URLs não confiáveis em imports,
e exigir nova revisão antes de adicionar imagens por import ou metadados por arquivo.
Não houve exploração de ICNS/JXL/HEIF, DAST ou fuzzing. A aceitação de risco para qualquer
publicação permanece pendente, juntamente com validação da autenticação remota.

## Validação

- Build e 51 testes JS/TS aprovados, incluindo banco offline, contrato SDK, transporte
  de stream, login SSR, hosts de metadados e alinhamento de versões React/RSC.
- ESLint, TypeScript global e `npm ls --depth=0` aprovados, sem erro de peers.
- Servidor de desenvolvimento atualizado iniciou em `http://localhost:3000/` e
  respondeu HTTP 200 à raiz. A prévia foi encaminhada ao painel do aplicativo, sem
  inspeção de DOM, captura de tela ou testes de interação.
- Lockfile preserva pacotes nativos Windows/Linux AMD64 de workerd 1.20260903.1 e
  sharp 0.35.2 com integridade registrada; isso não valida instalação em outra máquina.
- Testes de navegador, múltiplas câmeras, VM, JWT/PostgREST hospedados e deploy não
  executados. A suíte Python passou no incremento anterior (127 + 11 subtestes);
  nenhum código Python foi alterado neste incremento.
- A auditoria é datada; novas vulnerabilidades podem aparecer após esta consulta.

Comandos no Conda `smart-environment`, a partir de `dashboard/`:

```powershell
conda run -n smart-environment npm.cmd test
conda run -n smart-environment npm.cmd run lint
conda run -n smart-environment npx.cmd tsc --noEmit
conda run -n smart-environment npm.cmd ls --depth=0
conda run -n smart-environment npm.cmd audit --json
```

`npm audit` retorna código diferente de zero pelos dois avisos residuais, e não por
erro de instalação. Durante as consultas houve colisão de temporários de `conda run`
paralelos; as chamadas posteriores foram serializadas, sem alterar base/.venv.
