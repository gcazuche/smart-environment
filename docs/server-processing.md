# Processamento na VM Ubuntu — Smart Environment

Esta configuração separa **vídeo ao vivo** de **análise de pessoas**. O destino é a
VM Ubuntu x86-64 no Hyper-V, com 8 vCPU, inicialmente 4 GB de RAM e sem GPU, para
até quatro câmeras. A meta de transmissão é 720p/30 FPS; a análise começa em
2 FPS por câmera e utiliza um único modelo OpenVINO em CPU. Não é uma promessa de
30 quadros novos por segundo: câmera, codec, iluminação, rede, CPU física do host,
concorrência da VM e navegador influenciam o resultado. Se houver pressão de memória,
avalie aumentar a VM para 8 GB; isso ainda precisa ser medido.

```text
Câmeras → MediaMTX na VM → WebRTC → navegador
                   └──→ Python/OpenVINO → fila SQLite → Supabase
```

O navegador usa uma sessão Django; sinalização WHEP e telemetria passam por endpoints
da mesma origem. Django encaminha o JWT do usuário ao gateway Python, que verifica
seu vínculo e a propriedade da sessão de vídeo. Tokens Supabase não ficam no navegador.
A mídia WebRTC vai diretamente ao navegador, sem passar por Django ou pelo banco,
e não espera uma inferência para avançar. Os retângulos são a
detecção recente, não uma análise sincronizada de cada quadro exibido. Imagens ficam
em memória; este fluxo não grava vídeo, áudio, fotos, rostos ou identidade, nem conclui
se alguém está trabalhando, distraído ou sendo produtivo.

## 1. Preparar a VM e os arquivos

Os comandos desta seção são para **Bash no Ubuntu**, não PowerShell. Configure uma
interface de rede da VM acessível aos computadores autorizados e reserve um IP privado
estável; `192.168.1.50` abaixo é apenas exemplo. Para acesso de fora da rede, use uma
VPN administrada pela equipe. Esta entrega não configura VPN, NAT, TURN ou internet pública.

Instale Git, servidor SSH e as bibliotecas de sistema do OpenCV:

```bash
sudo apt update
sudo apt install git openssh-server libgl1 libglib2.0-0
```

Em edições recentes do Ubuntu, o pacote GLib pode aparecer como `libglib2.0-0t64`;
confirme o nome oferecido pelo repositório da sua versão, sem baixar bibliotecas avulsas.
Use uma instalação confiável de Conda. Os serviços fornecidos pressupõem Conda em
`/opt/conda`, com permissão de gestão para o responsável pela instalação. Se ele já
estiver em outro caminho, ajuste os serviços de acordo; um ambiente dentro de `/home`
não fica acessível com o isolamento `ProtectHome=true`. Não execute `pip` como root.

Clone o repositório privado usando sua autenticação Git/SSH, sem inserir tokens na URL:

```bash
sudo install -d -m 755 -o "$USER" -g "$(id -gn)" /opt/smart-environment
git clone URL_DO_REPOSITORIO_PRIVADO /opt/smart-environment
cd /opt/smart-environment
conda env create -f environment.server.yml
conda activate smart-environment
python scripts/streaming.py setup
```

Se o ambiente `smart-environment` já existe, substitua `conda env create` por
`conda env update -n smart-environment -f environment.server.yml`. Não use `base`
ou `.venv`. O perfil de servidor instala os extras `intel` e `stream`, sem os pacotes
de exportação/treinamento. O último comando baixa MediaMTX **1.20.1**, confere o SHA-256
fixado no código e instala somente o executável em `tools/streaming/1.20.1`.

Copie do computador atual, por SCP ou outro canal privado, estes dois arquivos já
usados pelo projeto, preservando os nomes e a estrutura na VM:

```text
/opt/smart-environment/models/intel-person/yolo26n_openvino_model/yolo26n.xml
/opt/smart-environment/models/intel-person/yolo26n_openvino_model/yolo26n.bin
```

O modelo não vem no Git e sua integridade é conferida ao carregá-lo. Não renomeie outro
modelo para esses nomes nem treine/exporte novamente na VM de 4 GB. Preserve os avisos
de licença existentes. Se os arquivos estiverem ausentes ou alterados, a análise não inicia.

## 2. Supabase, UUIDs e segredos

**A organização atual já existe: não execute novamente bootstrap ou migração inicial.**
Mantenha a mesma organização e os vínculos de usuários. Cadastre as câmeras e os
ambientes pelo painel com uma conta administradora. O UUID da câmera aparece no
endereço da página de detalhes (`/cameras/UUID/`) e pode ser conferido no Supabase.
O cadastro sozinho não instala um transmissor nem autoriza um endereço de câmera na VM.

```bash
cp config/server/server.example.toml config/server/server.local.toml
cp config/server/.env.example config/server/.env.server.local
chmod 600 config/server/.env.server.local
nano config/server/.env.server.local
nano config/server/server.local.toml
```

No arquivo de segredos, preencha `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`
(`sb_publishable_...`) e **`SUPABASE_SECRET_KEY` (`sb_secret_...`)** do projeto correto.
Essa última chave tem acesso privilegiado: obtenha-a no painel administrativo, guarde-a
somente no servidor e não a envie pelo chat, Git ou variáveis `VITE_`. Nunca use a chave
secreta como login de usuário. Os arquivos locais acima são ignorados pelo Git; confira
`git status --short` antes de publicar qualquer mudança. Não use `git add -f` neles.

No TOML, substitua os UUIDs fictícios e mantenha a correspondência explícita:

```toml
organization_id = "UUID-REAL-DA-ORGANIZACAO"
allowed_origins = ["http://localhost:8000", "http://127.0.0.1:8000"]
analysis_fps = 2.0
cpu_threads = 4
database = "../../data/server/outbox.sqlite3"

[streams]
"UUID-REAL-DA-CAMERA-DO-PC" = "camera1"
"UUID-REAL-DA-CAMERA-DO-CELULAR" = "camera2"
```

Use de uma a quatro entradas, caminhos diferentes, simples e sem barras. As origens
permitidas são endereços explícitos **do painel**, não da câmera; nunca use curingas.
Na aplicação Django, o navegador não chama diretamente a API do gateway: o proxy
server-side não encaminha o header `Origin` nem cookies recebidos do cliente. A
allowlist do gateway permanece restrita para clientes que usem sua API diretamente.
O serviço só analisa câmeras habilitadas da
organização que também estejam nesse mapa. Endereços salvos pelo navegador não viram
automaticamente fontes de captura: o responsável configura as fontes no MediaMTX.

## 3. MediaMTX e HTTPS privados

```bash
cp config/server/mediamtx.example.yml config/server/mediamtx.local.yml
cp config/server/Caddyfile.example config/server/Caddyfile.local
nano config/server/mediamtx.local.yml
nano config/server/Caddyfile.local
```

Substitua `192.168.1.50` pelo IP privado/VPN da VM em `webrtcLocalUDPAddress`,
`webrtcAdditionalHosts` e no endereço HTTPS do Caddy. Os três devem corresponder à
rede realmente alcançável pelo navegador. Preserve os binds `127.0.0.1:8554`,
`127.0.0.1:8889` e `127.0.0.1:8766`: são acessos internos sem exposição direta.

Instale o Caddy pelo canal oficial apropriado à sua versão do Ubuntu. O exemplo usa
`tls internal`: cada computador cliente precisa confiar **no certificado público da
CA realmente utilizada por esse Caddy**. Solicite sua exportação ao responsável,
confirme sua origem e importe-o no armazenamento de autoridades confiáveis do cliente.
Nunca copie a chave privada da CA e não contorne alertas de certificado no navegador.
Confiar na CA somente dentro da VM não faz os outros computadores confiarem nela.

No firewall, permita **TCP 443 e UDP 8189 somente para clientes da LAN/VPN autorizada**;
SSH/TCP 22 apenas para administração/publicação autorizada. Não publique 8554, 8889,
8766 nem o servidor de desenvolvimento do dashboard. Não habilite API, debug, gravação
ou permissões genéricas no MediaMTX. O Caddy faz proxy do gateway Python, não do WHEP
interno diretamente. Revise regras existentes antes de alterar o firewall remoto para
não perder o acesso administrativo.

## 4. Primeiro teste em primeiro plano, sem pessoas

Na raiz do projeto, com o Conda ativado, valide a configuração:

Você pode conferir a instalação **antes mesmo de preencher os segredos**:

```bash
python -m app.server --preflight
python -m app.server --preflight --json
```

Esse diagnóstico confere o ambiente Conda, Python, importação das dependências, hashes
do modelo e presença dos executáveis. Não abre câmera, porta, banco SQLite nem executa
FFmpeg ou inferência; não consulta o Supabase. Sem `--config`, a configuração aparece
como **não verificada**, e não como aprovada. Para conferir também o formato e as
permissões aparentes do destino da fila, depois de preenchê-los:

```bash
python -m app.server --preflight --config config/server/server.local.toml --env-file config/server/.env.server.local
```

Código de saída `0` significa ausência de falhas nos itens verificados, não aprovação
de rede/VM/produção; `1` indica falhas de diagnóstico. `--json` funciona somente com
`--preflight`. Nenhum diretório ou arquivo de fila é criado por essa verificação.

O modo anterior de validação **apenas do formato** continua disponível:

```bash
python -m app.server --config config/server/server.local.toml --env-file config/server/.env.server.local --check
```

`--check` não acessa rede nem câmeras: confirma o formato da configuração, não a
validade remota das chaves, existência dos UUIDs, disponibilidade do modelo ou desempenho.
Depois, abra terminais separados na raiz do projeto:

```bash
# Terminal 1 — perfil de servidor; NÃO use o comando antigo "streaming.py server".
./tools/streaming/1.20.1/mediamtx config/server/mediamtx.local.yml

# Terminal 2 — gateway e análise, no ambiente smart-environment.
python -m app.server --config config/server/server.local.toml --env-file config/server/.env.server.local

# Terminal 3 — padrão móvel, 720p30, sem câmera física; encerra em 60 segundos.
python scripts/streaming.py test-pattern --path camera1 --seconds 60
```

Com Caddy já instalado, use o gerenciador de serviço dessa instalação para carregar
o conteúdo de `config/server/Caddyfile.local`. Antes de aplicar, revise a configuração
existente: não a sobrescreva se houver outros sites. Na instalação padrão, valide
`sudo caddy validate --config /etc/caddy/Caddyfile` e recarregue com
`sudo systemctl reload caddy`. Não inicie um segundo Caddy disputando a porta 443.

Na máquina que executa **Django**, prepare a configuração privada seguindo
[django-migration.md](django-migration.md). O arquivo atual é
`config/web/.env.web.local`, não `dashboard/.env.local`. As mesmas URL, chave
publicável e organização Supabase continuam válidas; não faça novo bootstrap.
`prepare_web` pode copiar as variáveis do arquivo legado sem sobrescrevê-lo e gera
uma chave Django privada. Preserve essa chave entre reinicializações e não a publique.

Se Django e o processamento estiverem **na mesma VM**, acrescente ao arquivo web:

```dotenv
PROCESSING_SERVER_URL=http://127.0.0.1:8766
```

Se Django estiver **em outro computador**, use o HTTPS privado do gateway:

```dotenv
PROCESSING_SERVER_URL=https://192.168.1.50
```

Nesse segundo caso, a CA do certificado precisa ser confiável também para o **Python
na máquina Django**, não apenas para o navegador. Configure o armazenamento de
certificados/CA do ambiente com o responsável pela rede; não desative a validação
TLS. O navegador ainda precisa alcançar a mídia WebRTC na VM pela LAN/VPN. A URL
acima é somente uma origem, sem caminho, parâmetros ou credenciais embutidas.

Depois da preparação inicial da configuração e das migrações **locais de sessão**,
reinicie Django. Para ver o painel local no Windows, na raiz do projeto:

```powershell
conda run --no-capture-output -n smart-environment python manage.py runserver 127.0.0.1:8000 --insecure --noreload
```

Abra `http://127.0.0.1:8000`. `DJANGO_DEBUG=false` permanece ativo; `--insecure` apenas
permite que o servidor de desenvolvimento entregue os arquivos estáticos nesse
endereço loopback. Não é opção de implantação, não ignora certificados TLS e não
autoriza expor `runserver` à rede. Não é necessário npm nem build TypeScript.

Entre com uma conta real vinculada à organização. Abra **Câmeras** e clique
**Conectar** na transmissão desejada; nenhuma câmera é aberta automaticamente.
Confirme imagem móvel e FPS medidos. Vídeo FPS é separado de Análise FPS; uma falha
temporária de análise expira contagens/retângulos, mas não reinicia a mídia. Falha de
acesso encerra a transmissão. Ocultar a aba também a encerra; conecte para retomar.
O padrão é um teste de transporte, não de acurácia da detecção.

Para hospedar o painel na VM, use o roteiro de implantação Django e os exemplos
`config/web/smart-environment-web.service` (Waitress, um processo com threads) e
`config/web/Caddyfile.example` (HTTPS e arquivos estáticos). Eles são separados dos
serviços MediaMTX/processamento desta página. Integre o site web ao Caddy existente
sem sobrescrever o gateway nem iniciar outro processo na mesma porta. Hostnames,
certificados, permissões, caminho do SQLite de sessões e coleta de estáticos exigem
revisão antes de ativar o serviço; os exemplos não representam uma implantação validada.

## 5. Conectar fontes reais, uma de cada vez

**Webcam no PC Windows:** ela continua fisicamente no PC; a VM não ganha acesso ao
USB automaticamente. Pare o padrão e qualquer monitor anterior que esteja usando a
webcam. Em um terminal do PC, mantenha este túnel aberto:

```powershell
ssh -N -L 8554:127.0.0.1:8554 usuario@192.168.1.50
```

Se a porta 8554 já estiver ocupada, identifique e encerre apenas o MediaMTX local
anterior que você iniciou; não altere o servidor para aceitar publicação anônima na rede.
Em outro terminal do PC, na raiz do projeto e no Conda `smart-environment`:

```powershell
python scripts/streaming.py devices
python scripts/streaming.py modes --device "NOME EXATO DA CAMERA"
python scripts/streaming.py webcam --device "NOME EXATO DA CAMERA" --path camera1
```

A webcam precisa oferecer 1280×720/30 FPS para esse comando. Ela pode anunciar o modo
e entregar menos quadros reais; o transmissor não duplica frames para aparentar 30 FPS.
O PC codifica H264, mas a detecção é feita na VM. O túnel é para publicação RTSP;
ele não substitui a conectividade UDP entre navegador e VM.

**Câmera IP com RTSP/H264:** no YAML local, habilite `camera2` com `source:` apontando
para o endpoint RTSP real do dispositivo e `rtspTransport: tcp`, conforme o exemplo
comentado. Preserve a permissão `read` de `camera2`. Nesse caso o MediaMTX busca a
fonte, sem o publicador FFmpeg. Proteja o YAML se ele contiver credenciais; não coloque
senhas no cadastro público. Prefira H264 compatível com WebRTC, sem B-frames. H265 e
outros formatos não têm reprodução universal: transcodificação pode ser necessária,
consome CPU e deve ser planejada/testada, não está automaticamente resolvida.

**Android com MJPEG:** configure `camera2` como `source: publisher` e acrescente também
uma permissão `publish` para `camera2` no usuário local do MediaMTX. Reinicie somente
seu MediaMTX para aplicar. Com o aplicativo do celular ativo, execute na VM que alcança
o celular, ou no PC com o túnel SSH aberto:

```bash
python scripts/streaming.py mjpeg --url http://192.168.1.36:8080/video --path camera2
```

Confirme o IP atual e o endpoint multipart MJPEG do aplicativo. O helper aceita HTTP
em IPv4 privado, sem usuário/senha, query ou fragmento na URL. Não serve para uma foto
JPEG estática nem para qualquer URL de vídeo. MJPEG é convertido para H264 onde esse
comando roda, consumindo CPU adicional; baixa cadência do celular não é corrigida pela
VM. Não encaminhe esse HTTP sem proteção pela internet. Câmeras 3 e 4 repetem o mapa
UUID/caminho, as permissões e a configuração de fonte; uma fonte por caminho.

## 6. Deixar os serviços automáticos após o teste

Os exemplos usam `/opt/smart-environment`, ambiente em
`/opt/conda/envs/smart-environment`, configurações em `/etc/smart-environment` e usuário
de serviço `smart-environment`. Confirme esses caminhos antes de instalar os units.
Crie o usuário somente se `id smart-environment` indicar que ele ainda não existe:

```bash
sudo useradd --system --home /var/lib/smart-environment --shell /usr/sbin/nologin smart-environment
sudo install -d -m 750 -o root -g smart-environment /etc/smart-environment
sudo install -d -m 700 -o smart-environment -g smart-environment /var/lib/smart-environment
sudo install -m 600 config/server/.env.server.local /etc/smart-environment/server.env
sudo install -m 640 -o root -g smart-environment config/server/server.local.toml /etc/smart-environment/server.toml
sudo install -m 640 -o root -g smart-environment config/server/mediamtx.local.yml /etc/smart-environment/mediamtx.yml
sudo nano /etc/smart-environment/server.toml
```

No TOML instalado, altere **`database = "/var/lib/smart-environment/outbox.sqlite3"`**.
Um caminho relativo passa a ser relativo a `/etc/smart-environment`, não ao repositório.
O `EnvironmentFile` é lido pelo systemd e permanece root/600. O usuário de serviço
precisa ler código, modelo e dependências em `/opt`, mas não precisa editá-los.

```bash
sudo install -m 644 config/server/smart-environment-media.service /etc/systemd/system/smart-environment-media.service
sudo install -m 644 config/server/smart-environment.service /etc/systemd/system/smart-environment.service
sudo systemctl daemon-reload
sudo systemctl enable --now smart-environment-media.service smart-environment.service
sudo systemctl status smart-environment-media.service smart-environment.service
sudo journalctl -u smart-environment.service -n 50 --no-pager
```

Encerre os processos de teste em primeiro plano com Ctrl+C **antes** de iniciar os
units, evitando disputa de portas. Se o teste anterior gerou uma fila SQLite pendente,
pare o processamento e preserve/migre a base com segurança antes de trocar seu caminho;
não abandone a fila nem copie só o arquivo principal enquanto houver escrita/WAL ativo.
Os units não automatizam a webcam do PC, o túnel SSH nem o relay MJPEG: esses publicadores
continuam explícitos nesta etapa. Não execute dois servidores para a mesma câmera/minuto.

## Operação, diagnóstico e limites

O incremento v0.2.0 acrescenta [backup/verify/restore da outbox](server-backup.md)
com destino novo, preservando a base original. Consulte também as
[melhorias locais e o roteiro de medição](performance-and-readiness.md).
O fechamento periódico dos minutos consulta o SQLite uma vez por segundo, em vez de
acompanhar o loop de vídeo; observações e alertas continuam sendo persistidos quando
recebidos. Um minuto encerrado pode levar até cerca de um segundo adicional para
ser fechado, além do tempo de inferência/entrega. Isso não altera a análise configurada.

- O endpoint autenticado `GET /v1/health` informa disponibilidade do catálogo e estado
  da entrega. Ele exige `Authorization: Bearer` com sessão real de usuário; nunca use
  a chave secreta no navegador, numa URL ou em capturas de tela. `GET /v1/cameras`
  também é autenticado. Abrir esses endereços sem sessão não é um teste de login.
- Cadastro habilitado + UUID no TOML + caminho publicado são três requisitos distintos.
  Confira os três quando a câmera estiver aguardando. Sem catálogo recente por cerca
  de 30 segundos, o serviço deixa de autorizar fontes/sessões; não continua monitorando
  indefinidamente sem conferir o vínculo atual. Sem análise fresca, contagem é desconhecida,
  não zero, e retângulos antigos deixam de ser apresentados.
- O Supabase recebe agregados de minutos encerrados, não cada frame: presença observada
  torna o minuto ocupado; vazio exige cobertura válida; lacunas/parciais ficam desconhecidos.
  Câmeras sobrepostas não são somadas como se fossem pessoas únicas. Alertas seguem as
  regras habilitadas de ausência de câmera/ocupação fora do horário, no fuso de Brasília.
- A fila SQLite persiste envios pendentes e tenta novamente falhas transitórias. Examine
  contadores de pendências e erros permanentes (`dead letter`). Não apague a base para
  esconder um erro: uma câmera movida de ambiente pode ter registros antigos recusados
  pela integridade do banco. Não reatribua silenciosamente esse histórico nem reenvie
  sobrescrevendo decisões humanas sobre alertas. Proteja e inclua a fila no plano de backup.
- A sessão de vídeo exige renovação periódica autenticada. Revogação não é instantânea:
  há caches/janelas de renovação e o encerramento depende do gateway/MediaMTX disponíveis.
  Sair de um navegador não equivale a invalidar imediatamente todo token de outro dispositivo.
- Meça primeiro uma câmera, depois duas e quatro: FPS decodificados/apresentados, atraso,
  CPU, memória, perdas de rede e frequência real de análise. Mantenha `analysis_fps = 2`
  inicialmente; reduza se necessário. Aumentar para 30 não é permitido nem necessário
  para o vídeo de 30 FPS; o limite de análise configurável é de 0,2 a 5 FPS por câmera.
  Mantenha data/hora da VM e dos computadores sincronizadas: o painel compara os
  horários das leituras para não manter contagens ou retângulos desatualizados.

**Validação pendente no ambiente de destino:** instalação Ubuntu/Hyper-V, firewall/TLS,
login e ingestão reais, reprodução WebRTC com tráfego UDP e desempenho simultâneo das
câmeras físicas. Testes locais de código não comprovam esses resultados. Esta entrega
não é aprovação para exposição pública: revise também as dependências residuais do
dashboard, hospedagem de produção, retenção, permissões, backup e operação do servidor.

Validação de código em 08/09/2026, no Conda `smart-environment`: 322 testes Python
e 11 subtestes, 55 testes do dashboard e build, TypeScript, ESLint, Ruff e Mypy.
O modelo OpenVINO também carregou com o perfil CPU de 4 threads e concluiu uma
inferência sobre uma matriz sintética em memória. Isso não acessou câmera física
e não é medição de FPS ou validação na VM.

Referências do projeto: [configuração do Supabase](supabase-setup.md),
[piloto local e medições anteriores](streaming-local.md),
[hardening de dependências](dependency-hardening.md).
Referências técnicas: [MediaMTX 1.20.1](https://github.com/bluenviron/mediamtx/releases/tag/v1.20.1),
[reprodução no navegador](https://mediamtx.org/docs/read/web-browsers),
[compatibilidade WebRTC](https://mediamtx.org/docs/features/webrtc-specific-features),
[chaves Supabase](https://supabase.com/docs/guides/getting-started/api-keys).
