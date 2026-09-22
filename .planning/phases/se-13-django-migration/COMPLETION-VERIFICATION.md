# SE-13 — conclusão da migração de código Django

Data: 20/09/2026. Pedido: “termine de fazer a transição”.
Ambiente: Windows, Conda `smart-environment`, árvore local com mudanças anteriores.
Este documento complementa o `VERIFICATION.md` histórico de DJ-01; não o substitui
nem apresenta seus limites antigos como se fossem o comportamento atual.

## Resultado

DJ-01 a DJ-06 implementados. `manage.py` / `app.web` são a aplicação web principal,
com templates HTML, CSS e JavaScript puro, sem runtime/build TypeScript/npm. Código
legado e alterações do usuário preservados. Não criados commit, tag, push ou Release.
Não executado login remoto, bootstrap, CRUD remoto, câmera, treino ou implantação.

| Critério | Implementação/evidência |
|---|---|
| Contas existentes | Supabase Auth + membership da organização; chave publicável e JWT só no servidor |
| Sessão | DB Django, cookie com identificador HttpOnly, limite absoluto 8 h, refresh e logout sob lock |
| Permissões | admin/viewer reconsultados, escopo org explícito + RLS; testes de negação/conflito |
| Login seguro | CSRF, rotação, rate limit persistente, mensagens genéricas, DEBUG bloqueia acesso |
| Navegação | URLs reais para visão geral, câmeras, ambientes, perfil, indicadores, histórico, alertas, regras |
| Ambientes | Detalhe mostra todas as câmeras vinculadas, sem somar pessoas observadas por várias câmeras |
| Cadastros | Forms server-side e version original nas alterações; validar endereço sem credenciais |
| Relatórios | Período Brasília/filtro ambiente, agregação por câmera, página 50, CSV UTC protegido contra fórmulas |
| Vídeo | WHEP/telemetria same-origin via Django; mídia separada, conexão manual e cleanup/expiração |
| Dados desconhecidos | Falha/ausência/ambiguidade não vira zero; leituras antigas removem caixas |
| Identidade visual | Logos originais, cores, menu responsivo e relógio atual; UUID visível em detalhe |
| Operação | Configuração privada, ambiente web Conda, Waitress processo único e exemplo Caddy/TLS |
| CI | Django principal, testes Python/JS; antigo npm/audit somente em workflow manual explícito |

## Comandos e resultados executados

Todos via `conda run --no-capture-output -n smart-environment`, sem `.venv` ou base:

- `python -m pip install -e ".[web]"`: instalado pacote **0.3.0a1**, Django 5.2.17 e
  Waitress 3.0.2 no ambiente existente; não instalação limpa.
- `python manage.py prepare_web`: criou arquivo privado ignorado com chave persistente;
  reaproveitou somente allowlist de configuração legada. Nenhum valor impresso.
- `python manage.py migrate --noinput`: aplicou `sessions.0001` e `web.0001` somente
  no `data/web.sqlite3` local; Supabase não é a conexão DATABASES do Django.
- Verificação final sem valores: DEBUG=false, PRODUCTION=false, segredo persistente,
  configuração de acesso válida e SQLite existente; `remote_checked=false`.
- `python manage.py check`: **zero problemas**.
- `python -m pytest -q --basetemp=C:/Users/angel/AppData/Local/Temp/smart-web-final-20260920-r3`:
  **714 passed, 478 subtests passed, 11.57 s**, sem falhas/skips. Basetemp exclusivo
  evita erro de permissões do diretório temporário padrão observado nesta máquina.
- `node --test tests/js/web-login.test.mjs tests/js/web-video.test.mjs`:
  **17/17 aprovados**, sem falhas/skips (2 login, 15 vídeo/polling/cleanup).
- Ruff check e format check: `manage.py`, `app/web`, `tests/test_web_*.py`,
  `tests/conftest.py`, `scripts/preview_django_fixture.py`: aprovados, **35 arquivos**
  já formatados na última verificação.
- Ruff `app/server tests/test_server_*.py`: aprovado; Mypy `app/server`: **10 fontes**
  sem problemas. Não foi feito Mypy estrito do novo Django sem stubs.
- `python -m pip check`: sem dependências quebradas (não é SCA/auditoria CVE).
- `git diff --check`: aprovado; somente avisos LF/CRLF, sem normalizar trabalho alheio.
- YAML dos dois workflows e `environment.web.yml` parseado com sucesso por PyYAML;
  validação sintática somente, não execução nem validação das actions no GitHub.
- Opções do serviço verificadas com `waitress.adjustments.Adjustments`, sem bind:
  loopback8000, 8 threads, connection_limit100, corpo150000 e proxy proto confiável.
  `waitress-serve --help` executado; systemd/Caddy não executados neste Windows.

### Empacotamento

`python -m pip wheel --no-deps --no-build-isolation . --wheel-dir data/builds/django-20260920`:

- `multicam_inteligente-0.3.0a1-py3-none-any.whl` gerado na pasta ignorada.
- SHA256: `28f61c32832beeb416ae52337daad4e93af4885e52a77b70d38a91e1d81fc561`.
- **23 arquivos web estáticos/templates** comparados byte a byte com a árvore, iguais.
- Não há `.ts`, `.tsx` ou `.env.local` dentro do wheel.
- Wheel inclui a árvore Python local, não prova snapshot Git seletivo nem instalação
  independente/Linux. Arquivos runtime privados e imagens de treino não foram empacotados.

## QA real de interface, com dados exclusivamente sintéticos

`scripts/preview_django_fixture.py --serve-fixture` serviu somente em
`127.0.0.1:8001`, settings herméticos `app.web.testing`, SQLite temporário e serviço
Supabase substituído por memória. `socket.connect/create_connection` bloqueados e
transportes de vídeo sempre indisponíveis. Banner visível “PRÉVIA SINTÉTICA — NÃO
SÃO DADOS REAIS”. Nunca usar esse comando para mostrar dados operacionais.

Conferido no navegador integrado:

1. Login por formulário real/CSRF com credencial fictícia e entrada no painel.
2. Menu, perfil e navegação; ambiente com duas câmeras, sem abertura automática.
3. Edição de nome do ambiente refletida em cartões e filtros.
4. Criação de câmera fictícia, redirecionamento ao detalhe, UUID e versão visíveis.
5. Indicadores por câmera com ocupado/vazio/desconhecido separados.
6. Histórico com três amostras, desconhecido `—` distinto do zero medido e CSV com
   escopo da página visível. Download CSV no navegador não foi exercitado; conteúdo
   e headers são cobertos nos testes Python.
7. Revisão de alerta de Aberto para Revisado, depois botão Resolver disponível.
8. Edição da regra de 60 para 120 segundos refletida na listagem.
9. Perfil em **390×844**, logout retornando à tela de acesso.
10. Painel em **1440×1000**, logo original; em **800×900**, conteúdo785px = viewport785px,
    sem overflow horizontal. Corrigida quebra anterior do wordmark textual.
11. Console final sem avisos/erros capturados. Viewport restaurado e aba fechada.

O processo da prévia foi encerrado; nenhuma porta 8001 escutando ao conferir.
Interrupções forçadas deixaram cinco pastas `smart-environment-browser-fixture-*`
com SQLite de sessões **fictícias** no Temp do usuário. Limpeza dessas pastas foi
bloqueada pela política de execução e não foi contornada. Nada disso está no Git;
não se trata do SQLite real `data/web.sqlite3`, que deve ser preservado.

### Bug encontrado pelo navegador e corrigido

O antigo `Referrer-Policy: no-referrer`, também definido no meta HTML, levava
formulários Chromium a enviar `Origin: null`, recusado pelo Django. Primeiro houve
suspeita de limitação do navegador integrado; investigação confirmou configuração
da aplicação. Header e meta agora são `same-origin`: mantém informações internas
necessárias ao CSRF e não envia referrer a outros sites. **Não** foi liberada origem
null, adicionado bypass de CSRF ou desabilitada validação TLS. O login e os POSTs
de edição passaram após a correção. Testes cobrem token+origem correta e negação de
origem null/externa mesmo com token CSRF válido.

Fonte: [MDN Referrer-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referrer-Policy).

## Revisão de segurança

Revisão independente encontrou e confirmou correções de DEBUG, estrutura de membership,
datas extremas e IP do proxy para rate limit. Após correções, nenhum novo P0/P1/P2
concreto foi identificado por inspeção. Isso não equivale a pentest/DAST/SCA.

- Fronteiras: browser/sessão, Django/Supabase usuário, Django/gateway e WebRTC separado.
- Segredos: configuração server-side; sem service-role, tokens em HTML/JS ou refresh
  token em cookie apenas assinado. SQLite e backups exigem proteção de acesso/disco.
- Caddy sobrescreve proto/IP dedicado; Waitress apenas loopback. Sem múltiplos workers:
  locks são locais a um processo; expansão exige coordenação distribuída.
- A revisão de alerta verifica org/câmera antes da RPC; cadastros usam org/id/version.
- Logout sempre encerra a sessão local; revogação remota é melhor esforço com aviso.
- CSP same-origin, limite de corpo/campos/resposta/tempo; no-store para páginas privadas.
- Auditoria nova de CVEs Python e execução GitHub/Ubuntu **não realizadas**. Achados
  históricos image-size/vinext do legado permanecem documentados; retirar o legado
  do runtime principal não foi apresentado como correção dessas dependências.

## Aceites ainda externos ao código

- Entrar com conta real autorizada e validar admin/viewer/RLS contra Supabase existente.
- Confirmar CRUD/concorrência/relatórios com ingestão real, sem duplicar organização.
- Instalar e validar TLS, Caddy, systemd, permissões e backups na VM Ubuntu/Hyper-V.
- Medir WebRTC real, reconexão, revogação e 3–4 câmeras720p/30FPS separadas da análise CPU.
- Executar o CI no GitHub e revisar/auditar dependências do candidato de publicação.
- Fotos/anotações humanas, detector, celular e treino permanecem conforme SE-04;
  não interpretar presença ou proximidade como intenção/produtividade.

Guia operacional: `docs/django-migration.md`; publicação seletiva: `docs/versioning.md`.
Tags locais v0.1.0/v0.2.0 verificadas em 20/09 e preservadas. Candidato Git
v0.3.0-alpha.1 não criado; conferir remoto antes de usar. Contagens são da **árvore
inteira**, não da seleção publicável. `h origin main` e trabalho anterior intocados.
