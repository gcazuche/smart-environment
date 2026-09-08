# Dashboard Smart Environment

Interface web responsiva para visualizar câmeras, ambientes, ocupação, indicadores e
alertas do Smart Environment.

## Transmissão independente da IA (ST-01)

Na aba **Câmeras**, **Transmissão** abre o novo player WebRTC/WHEP de uma fonte
local com métricas reais. **Detecção local** preserva os JPEGs anotados anteriores.
O novo fluxo não depende do agente Python de detecção. Configuração, comandos de
webcam/padrão de teste e limites estão em [streaming local](../docs/streaming-local.md).
Ainda não é acesso pela VM/rede. O cadastro persistente está preparado separadamente
para ativação com o Supabase e não configura o gateway automaticamente.

A interface recebe do agente local contagem, estado, backend, latência e o JPEG anotado
mais recente da webcam do computador e da câmera do celular. As imagens ficam em
memória, são aceitas somente em localhost e não são gravadas nem enviadas à internet.
Histórico, indicadores e alertas já usam o adaptador Supabase quando configurado. Não
há projeto remoto conectado nesta instalação; leituras ao vivo não alimentam o banco
automaticamente. A ingestão no servidor Ubuntu é um próximo incremento.

## Controles, data/hora e banco (UI-02 / DB-01)

O cabeçalho mostra data/hora atuais em Brasília, atualizadas automaticamente. Histórico
e seleção de períodos fazem consultas reais quando o banco está configurado. Os
formulários de câmera, ambiente e regras salvam com permissão de administrador;
sem configuração ou permissão, informam o motivo e não fingem persistência.
Há histórico paginado, exportação CSV por página, relatório por câmera e revisão de
alertas. Não há cadastro local oculto nem gravação de vídeo.
Ativação e limites: [guia do Supabase](../docs/supabase-setup.md).

## Acesso atual

Ao abrir o dashboard, a tela de login aparece antes do painel. O acesso nesta instalação
sem variáveis configuradas é apenas local em localhost/127.0.0.1: aceita e-mail válido
e senha com pelo menos seis caracteres, guarda um marcador temporário em `sessionStorage`
e não armazena a senha nem autentica uma conta real. Com o Supabase configurado, o login
valida a conta no Auth, carrega permissões por organização e permite sair pelo SDK.
Configuração parcial bloqueia o acesso; não usa o acesso local como fallback.

## Executar localmente

```powershell
conda activate smart-environment
npm.cmd ci
npm.cmd run dev -- --hostname localhost
```

Acesse `http://localhost:3000`.

Para alimentar as duas câmeras, inicie antes o agente na raiz do projeto:

```powershell
conda run -n smart-environment multicam monitor --phone-url "http://IP-PRIVADO:PORTA/video" --detector intel
```

Áreas independentes podem ser desenhadas nas prévias com `--pc-work-zone` e
`--phone-work-zone`, usando `esquerda,topo,direita,base` entre `0` e `1`. Sem esses
argumentos, a região neutra cobre o frame inteiro.

O celular e o computador devem estar na mesma rede privada. O dashboard local mostra
as imagens reais com as caixas do detector. Em ambientes hospedados, a exibição de
vídeo depende de um backend remoto autenticado.

## Validar

```powershell
conda activate smart-environment
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd test
```

O build de produção é executado pelo próprio `npm test`.

## Áreas disponíveis

- visão geral com indicadores e atividade recente;
- lista e detalhes da webcam do computador e da câmera do celular;
- cadastro de webcam, MJPEG e câmera IP/RTSP (gateway ESP32 pendente);
- ambientes independentes, inclusive sem câmeras;
- ocupação por câmera e exportação de relatórios;
- alertas com linguagem de revisão humana.

Em 07/09/2026, a atualização de segurança reduziu o audit completo de 19 para **2 avisos
altos residuais** ligados a image-size/Vinext. Não estão suprimidos e não há aprovação
de deploy. O risco identificado é processamento de assets locais de dev/build; imagens
não confiáveis exigem revisão. O zero em `--omit=dev` não aprova o artefato servidor.
Versões, evidências e limites: [hardening de dependências](../docs/dependency-hardening.md).
