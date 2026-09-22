# Smart Environment — instalar e operar a versão Django

Atualizado em 20/09/2026. Aplicação principal: **Django + HTML/CSS/JavaScript puro**.
Não há compilação TypeScript, npm ou React no novo runtime. A pasta `dashboard/`
foi preservada como legado e não precisa ser iniciada. O detector, os modelos e o
banco Supabase existente não foram substituídos. Não repita o bootstrap.

## O que foi migrado

| Área | Comportamento atual |
|---|---|
| Acesso e perfil | Login Supabase, mesmas contas/organização, sessão no servidor, renovação, sair por POST e permissões admin/viewer |
| Visão geral | Resumo do catálogo e registros consultados, sem números fictícios |
| Câmeras | Listar, filtrar, ver detalhes, criar/editar e ativar/desativar; vídeo por conexão manual |
| Ambientes | Listar, criar/editar e reunir todas as câmeras do ambiente |
| Indicadores | Agregados e barras por câmera, separando ocupado/vazio/desconhecido |
| Histórico e alertas | Período/ambiente, páginas de 50 registros, CSV da página e revisão de alerta por administrador |
| Regras | Cadastro/edição com horários e validações, usando as tabelas existentes |
| Vídeo | WebRTC/WHEP com caixas e telemetria separadas; ponte local JPEG opcional |

Cadastros concorrentes conferem a versão original e não substituem silenciosamente
uma edição mais recente. CSV informa o escopo e datas UTC; a interface usa Brasília.
Não existe medição de produtividade ou economia energética comprovada. Ausência
de leitura continua desconhecida; contagens de câmeras não são somadas como pessoas únicas.

## 1. Baixar em outro computador

Instale Git e Conda, abra o terminal e clone o **seu repositório privado** usando a URL
que aparece no GitHub. Não copie senhas/tokens para o comando ou para o chat. Se o
projeto já estiver nesse PC, revise `git status` antes de atualizar e preserve edições locais.

Na raiz do projeto, para um computador que só exibirá/servirá o site:

```powershell
conda env create -f environment.web.yml
```

Para o ambiente completo de desenvolvimento/detecção, use `environment.yml` em vez
disso; ambos criam **smart-environment**, não execute os dois para criar o mesmo nome.
Se o ambiente já existe, não o recrie:

```powershell
conda run --no-capture-output -n smart-environment python -m pip install -e ".[web]"
```

Não use `.venv` nem instale no `base`. O site não precisa baixar pesos de IA.
O servidor de processamento usa [seu tutorial e modelos próprios](server-processing.md).

## 2. Preparar a configuração privada

```powershell
conda run --no-capture-output -n smart-environment python manage.py prepare_web
```

Isso gera uma chave Django persistente e cria `config/web/.env.web.local`, ignorado
pelo Git. Se o arquivo já existe, o comando recusa sobrescrevê-lo. Nesta máquina ele
já foi preparado; não precisa recriar. A configuração pode reaproveitar **somente**
URL, chave publicável, organização e endereço do processamento do antigo
`dashboard/.env.local`, sem alterá-lo ou imprimir valores. O novo arquivo e as variáveis
de ambiente têm precedência. Nenhuma consulta ou bootstrap remoto é executado.

Em PC novo, preencha no arquivo privado:

```dotenv
DJANGO_SECRET_KEY=CHAVE_LONGA_GERADA_PELO_PREPARE_WEB
DJANGO_DEBUG=false
DJANGO_PRODUCTION=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_SUA_CHAVE
ORGANIZATION_ID=UUID_DA_ORGANIZACAO_JA_EXISTENTE
PROCESSING_SERVER_URL=
LOCAL_MONITOR_ENABLED=false
```

Os textos acima são marcadores, não valores válidos. Use a mesma organização
existente, sem criar outra. Não use service-role/secret key no site. O acesso fica
indisponível se faltar configuração, a chave persistente for curta ou DEBUG estiver
habilitado. Não coloque credenciais em páginas, URLs, commits ou capturas de tela.
Para transferir a configuração, utilize um meio privado autorizado; prefira gerar
uma chave Django própria para a nova instalação. Não copie o banco de sessões.

## 3. Preparar sessões locais e iniciar

```powershell
conda run --no-capture-output -n smart-environment python manage.py migrate --noinput
conda run --no-capture-output -n smart-environment python manage.py check
conda run --no-capture-output -n smart-environment python manage.py runserver 127.0.0.1:8000 --insecure --noreload
```

Abra [Smart Environment local](http://127.0.0.1:8000/) e entre com sua conta já
vinculada ao Supabase. Não existe senha padrão ou cadastro automático. `createsuperuser`
não cria acesso ao painel. O banco `data/web.sqlite3` contém **sessões e limite de
tentativas**, não outro catálogo: câmeras, ambientes, regras e relatórios continuam
no Supabase. `migrate` aqui só altera esse SQLite local, não o Supabase.

Neste comando, `--insecure` serve somente arquivos estáticos no servidor de
desenvolvimento com DEBUG desligado; não desliga CSRF nem muda a validação HTTPS
dos serviços externos. Use somente em loopback, nunca na VM/internet. Encerre com
Ctrl+C. Se 8000 estiver ocupada, escolha outra porta local, sem parar processos alheios.

O cookie contém só o identificador da sessão; os tokens ficam no banco do servidor,
não no localStorage ou HTML. O SQLite não é criptografado automaticamente: proteja
arquivos e backups por permissões e criptografia do disco. Limpe sessões expiradas
periodicamente com `python manage.py clearsessions`, no ambiente Conda.

## 4. Ligar o site ao processamento existente

Na mesma VM, a configuração recomendada é:

```dotenv
PROCESSING_SERVER_URL=http://127.0.0.1:8766
```

Para outro servidor, use sua origem HTTPS, com certificado confiável pelo sistema
operacional. Não use `verify=False` nem libere CORS geral. HTTP de processamento só
é aceito em loopback na porta 8766. Não inclua caminho, senha ou parâmetros na URL.

O navegador fala com o Django na mesma origem para sinalização e telemetria. Django
encaminha o token de usuário ao gateway, que continua verificando organização e
propriedade das sessões. **O vídeo WebRTC não passa pelo Django**: vai do serviço de
mídia ao navegador. Inferência CPU tem sua própria frequência. Isso evita transformar
o servidor web num decodificador de vídeo, mas não garante 30 FPS; rede/codec/VM ainda
precisam ser medidos. ICE/UDP e eventual necessidade de TURN seguem o guia do servidor.

Cadastre a câmera no site e associe seu UUID à configuração do processamento como
descrito no [guia da VM](server-processing.md). Adicionar um registro não instala ou
ativa fisicamente uma câmera. No site, clique **Conectar**; sair da página, ocultar
a aba ou encerrar o acesso limpa a transmissão. Telemetria vencida remove caixas e
contagem, sem inventar zero ou reiniciar desnecessariamente o vídeo.

Para o piloto antigo, `LOCAL_MONITOR_ENABLED=true` habilita uma ponte exclusivamente
para o monitor em `127.0.0.1:8765`, no **mesmo computador do Django**. Use só com câmera
autorizada, monitor iniciado e `monitor_id` do catálogo correspondente. O browser não
abre sua webcam automaticamente. Com a opção desligada, não há acesso ao monitor.

## 5. Implantar na VM Ubuntu quando houver acesso

Isto é um roteiro preparado, **não uma implantação realizada**. A senha/usuário SSH
da VM são distintos da conta do painel. Conecte-se com o usuário/IP informados pelo
administrador (`ssh USUARIO@IP_DA_VM`) e confirme a identidade do servidor antes de
aceitar uma chave desconhecida. Não coloque a senha em scripts ou arquivos Git.

1. Clone o repositório privado em `/opt/smart-environment`, instale Conda em local
   acessível ao usuário de serviço e prepare `smart-environment`. Se processamento
   já usa esse ambiente, apenas instale o extra `web` nele, sem recriar o ambiente.
2. Ajuste `config/web/smart-environment-web.service` aos caminhos reais de Conda,
   projeto e usuário de serviço sem privilégios. O exemplo usa `/opt/conda` e
   usuário `smart-environment`. Não execute o serviço como root.
3. Crie `/var/lib/smart-environment` de propriedade desse usuário e permissões
   restritas. Guarde a configuração privada em `/etc/smart-environment/web.env`,
   legível somente pelo administrador e serviço, nunca numa pasta pública.
4. Configure os campos abaixo além do Supabase e segredo persistente. Substitua o
   domínio de exemplo por um domínio realmente seu, com DNS/TLS preparados.

```dotenv
DJANGO_PRODUCTION=true
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=smart.seudominio.com.br
DJANGO_CSRF_TRUSTED_ORIGINS=https://smart.seudominio.com.br
DJANGO_DATABASE_PATH=/var/lib/smart-environment/web.sqlite3
DJANGO_STATIC_ROOT=/var/lib/smart-environment/static
PROCESSING_SERVER_URL=http://127.0.0.1:8766
LOCAL_MONITOR_ENABLED=false
```

5. No terminal do **usuário de serviço**, com as mesmas variáveis exportadas do
   arquivo privado, execute no Conda:

```bash
conda run --no-capture-output -n smart-environment python manage.py migrate --noinput
conda run --no-capture-output -n smart-environment python manage.py collectstatic --noinput
conda run --no-capture-output -n smart-environment python manage.py check --deploy
```

   Não execute esses comandos com configuração diferente da usada no serviço.
   `EnvironmentFile` do systemd não é carregado automaticamente num terminal comum.
   Uma forma é manter temporariamente os mesmos valores em `config/web/.env.web.local`
   com permissões 600 e propriedade do serviço, ou exportá-los no shell privado
   sem imprimir valores. A chave deve continuar estável entre reinícios.
6. Instale a unidade revisada em `/etc/systemd/system/`, execute `systemctl daemon-reload`
   e habilite/inicie `smart-environment-web` com a autorização do administrador.
7. Integre `config/web/Caddyfile.example` à configuração Caddy existente. **Não
   sobrescreva** o proxy do gateway já instalado. O exemplo serve `/static/` e
   encaminha o site ao Waitress em `127.0.0.1:8000`; não exponha essa porta diretamente.
   O Caddy precisa ler os assets publicados, mas nunca a configuração ou SQLite;
   ajuste apenas a leitura/travessia da pasta `static`, não a pasta inteira de dados.
8. Configure HTTPS real e firewall: site em 443; portas internas restritas; mídia
   conforme guia do servidor. Teste login/logout, admin/viewer, CRUD, ingestão e
   vídeo reais antes de anunciar pronto. Faça backup privado do SQLite de sessões
   e do segredo; reiniciar sessões é preferível a compartilhar esse banco entre PCs.

**Um processo Waitress, com oito threads**, é a configuração suportada neste
incremento. O lock de renovação de token é local ao processo; não adicione múltiplos
workers/réplicas sem implementar coordenação distribuída. O proxy deve sobrescrever
`X-Forwarded-Proto` e `X-Smart-Client-IP`; a aplicação só confia no IP dedicado quando
a conexão vem do proxy loopback em produção. Não abra 8000 a clientes externos.

## 6. Verificação e limites

```powershell
conda run --no-capture-output -n smart-environment python -m pytest -q --basetemp=C:/Users/angel/AppData/Local/Temp/smart-django-tests
conda run --no-capture-output -n smart-environment node --test tests/js/web-login.test.mjs tests/js/web-video.test.mjs
```

Adapte o caminho temporário ao usuário do novo PC e reserve uma pasta **só para
pytest**: ele apaga seu próprio basetemp. Node só é necessário para esses testes,
não para operar o site. Instale extras de desenvolvimento para pytest/Ruff.

Para QA visual sem dados reais, há um comando isolado e opt-in:

```powershell
conda run --no-capture-output -n smart-environment python scripts/preview_django_fixture.py --serve-fixture
```

Ele só aceita `127.0.0.1:8001`, mostra aviso sintético, não lê configuração privada,
bloqueia conexões externas e descarta o banco temporário ao terminar. Suas credenciais
fictícias não funcionam no site real. Não use esse comando para implantação.
Uma interrupção forçada do processo pode deixar o SQLite sintético na pasta Temp;
isso não é o banco real da aplicação nem contém credenciais reais. No teste desta
entrega, a limpeza automática desses resíduos foi bloqueada pela política de execução.

`/health/` prova apenas que o processo web responde, não autenticação, RLS, modelos
ou transmissão. As evidências do incremento estão em
`../.planning/phases/se-13-django-migration/COMPLETION-VERIFICATION.md`.
Aceite remoto e teste de 3–4 câmeras 720p/30 FPS na VM permanecem pendentes.
Preservamos os arquivos antigos para recuperação; não houve commit/tag/push.

Referências: [sessões Django](https://docs.djangoproject.com/en/5.2/topics/http/sessions/),
[checklist de implantação](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/),
[Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/runner.html),
[sessões Supabase](https://supabase.com/docs/guides/auth/sessions).
