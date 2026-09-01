# Dashboard Smart Environment

Interface web responsiva para visualizar câmeras, ambientes, ocupação, indicadores e
alertas do Smart Environment.

A interface recebe do agente local contagem, estado, backend, latência e o JPEG anotado
mais recente da webcam do computador e da câmera do celular. As imagens ficam em
memória, são aceitas somente em localhost e não são gravadas nem enviadas à internet.
Os gráficos históricos usam a base disponível e podem ser conectados ao Supabase.

## Acesso atual

Ao abrir o dashboard, a tela de login aparece antes do painel. O acesso nesta instalação
é local: aceita um e-mail válido e senha com pelo menos seis caracteres, guarda somente
um marcador temporário em `sessionStorage` e não armazena a senha. O perfil do
administrador abre um resumo da sessão e permite sair do painel. Para contas, sessões e
permissões compartilhadas, conecte o Supabase Auth e o backend da aplicação.

## Executar localmente

```powershell
npm install
npm run dev
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
npm run lint
npm test
```

O build de produção é executado pelo próprio `npm test`.

## Áreas disponíveis

- visão geral com indicadores e atividade recente;
- lista e detalhes da webcam do computador e da câmera do celular;
- cadastro visual de webcam, câmera IP e gateway ESP32;
- ambientes monitorados;
- ocupação e sustentabilidade;
- alertas com linguagem de revisão humana.
