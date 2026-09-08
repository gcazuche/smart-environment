# ST-01 — uma transmissão sem depender da IA

## Escopo e estado

O dashboard agora oferece **Câmeras → Transmissão** com player WebRTC/WHEP,
conectar/desconectar, tratamento de indisponibilidade e métricas do navegador.
**Detecção local** preserva o fluxo anterior de JPEGs anotados. O player novo não
abre webcam pelo navegador, não executa IA, não grava vídeo e não inventa contagens.

Este incremento é **somente local**: navegador, MediaMTX e transmissor no mesmo PC.
Não é ainda a implantação no Ubuntu/Hyper-V e não implementa cadastro persistente.
O perfil bloqueia conexões externas. Não altere os binds para `0.0.0.0` para
experimentar na rede: autenticação, autorização e transporte seguro são a próxima etapa.

Destino planejado, informado pelo usuário: VM Ubuntu no Hyper-V, 8 vCPU, 4 GB RAM
(ampliáveis), sem GPU, 3–4 câmeras 720p e meta de 30 FPS por câmera. A versão exata do
Ubuntu, CPU física, carga compartilhada e capacidade real ainda serão verificadas.
8 GB RAM é uma recomendação provisória para os testes com IA, não requisito medido.

## Preparar (uma vez)

Na raiz do projeto, dentro do Anaconda Prompt:

```bat
conda activate smart-environment
python -m pip install -e ".[stream]"
python scripts/streaming.py setup
```

`setup` baixa MediaMTX **1.20.1** para `tools/streaming/1.20.1` (fora do Git),
confere SHA-256 fixado e extrai apenas o executável. O extra `stream` instala
`imageio-ffmpeg==0.6.0` no Conda com FFmpeg incluído; não altera o `base`.
O helper também suporta Ubuntu x86-64 para o mesmo teste inteiramente local.

## Rodar o primeiro teste sem imagens de pessoas

Terminal 1, raiz do projeto:

```bat
conda activate smart-environment
python scripts/streaming.py server
```

Terminal 2, raiz do projeto:

```bat
conda activate smart-environment
python scripts/streaming.py test-pattern
```

Esse segundo comando gera um padrão móvel 1280×720/30 FPS em memória. Não acessa
câmera. Para um teste com encerramento automático, acrescente `--seconds 45`.
Não roda modelo de pessoas e não grava imagens.

Terminal 3, raiz do projeto:

```bat
conda activate smart-environment
cd dashboard
npm.cmd ci
npm.cmd run dev -- --hostname localhost
```

Abra `http://localhost:3000`, entre no painel e selecione **Câmeras → Transmissão**.
O login continua local demonstrativo: e-mail válido e senha de seis ou mais
caracteres. Não é autenticação de rede. Mantenha o endereço
`http://127.0.0.1:8889/camera1/whep` e clique **Conectar transmissão**.

`npm.cmd ci` só é necessário na instalação ou após mudanças de dependências.
No Ubuntu use `npm` no lugar de `npm.cmd`.

## Usar a webcam Windows

Primeiro encerre o padrão de teste com Ctrl+C; somente um transmissor pode ocupar
`camera1`. Encerre também o monitor antigo se ele estiver usando a mesma webcam.

```bat
python scripts/streaming.py devices
python scripts/streaming.py modes --device "NOME EXATO DA CAMERA"
python scripts/streaming.py webcam --device "NOME EXATO DA CAMERA"
```

As listagens DirectShow podem terminar com código 1 mesmo após mostrar os dados;
isso é comportamento da ferramenta de listagem, não falha de transmissão.
O comando de webcam solicita 1280×720/30 FPS na entrada e falha se não houver esse
modo. A saída usa `-fps_mode passthrough`, sem duplicar frames para aparentar 30 FPS.
Uma câmera anunciar esse modo não comprova a entrega de 30 quadros novos por segundo.
O desempenho real ainda
depende da câmera, exposição/iluminação, USB, codificação e computador receptor.
No Ubuntu, uma webcam fisicamente acessível à VM usa, por exemplo,
`python scripts/streaming.py webcam --device /dev/video0` (V4L2).
USB do computador cliente não aparece automaticamente dentro da VM remota.

**Não cole URL MJPEG/RTSP do celular no campo WHEP.** Adaptação de outras fontes e
publicação na VM serão implementadas em outro incremento; este emissor é webcam
local ou padrão de teste. Para parar, desconecte o player e use Ctrl+C nos terminais.

## O que os números significam

- **FPS decodificados:** variação de `framesDecoded` no intervalo do relatório WebRTC.
- **FPS apresentados:** variação de `presentedFrames` informada por
  `requestVideoFrameCallback`; mede submissões ao compositor, não fotografa a tela.
  Pode ser limitada pela atualização do display e pela carga do cliente.
- **Resolução recebida:** reportada pelo navegador, não copiada da meta.
- **Recepção:** variação de bytes recebidos por tempo; não é o consumo total da rede.
- **Buffer médio:** variação do atraso acumulado no jitter buffer dividida pelos
  quadros emitidos. **Não é latência ponta a ponta.**

Sem suporte/counter inicial, mostramos `—`. Em aba oculta não afirmamos FPS de
apresentação. Ausência de quadros fica sinalizada e uma interrupção prolongada
encerra a sessão. Reconexão é explícita, sem loop agressivo de tentativas.

## Validação realizada e limites

- Build, lint e **24 testes** do dashboard aprovados, incluindo cliente WHEP,
  métricas e regressões da UI.
- **127 testes Python e 11 subtestes** aprovados; testes automatizados do novo
  instalador/configuração/emissor não acessam câmeras. Ruff e mypy do helper passaram.
- MediaMTX real carregou o YAML e escutou somente TCP 127.0.0.1:8554/8889 e UDP
  127.0.0.1:8189; outros protocolos, API, debug e gravação desabilitados.
- FFmpeg publicou **1.350 frames em 45 segundos de mídia**, 720p30, fonte sintética;
  uma segunda conexão RTSP recebeu e decodificou vídeo para uma saída descartada.
  Esse teste não mede desempenho do navegador ou da VM.
- Negociação real com SDP completo: OPTIONS/CORS, POST WHEP 201, Location de mesma
  origem e DELETE 200. O teste de sinalização não completa ICE/DTLS nem toca vídeo.
- Teste separado com a webcam **USB2.0 HD UVC WebCam**, sem IA: ela anuncia 720p30,
  mas entregou **113 frames em 14,96 segundos de mídia**, cerca de **7,5 FPS reais**,
  com `-fps_mode passthrough`. Na primeira execução, a sincronização padrão do FFmpeg
  repetiu quadros; isso foi identificado e corrigido antes deste resultado final.
  Não foi determinada a causa da baixa cadência da câmera. Iluminação/exposição,
  driver, USB e carga precisam de investigação; mudar para a VM não garante corrigi-la.
  O teste foi encerrado automaticamente, sem microfone nem gravação.

Não houve teste automatizado de interação/reprodução em navegador. Precisamos ainda
medir FPS apresentados, perdas e atraso ponta a ponta com webcam e depois com quatro
câmeras na VM. Não há garantia universal de 30 FPS.

Comandos de validação, raiz do projeto:

```bat
conda run -n smart-environment python -m pytest -q --basetemp "%LOCALAPPDATA%\Temp\smart-environment-stream-tests"
conda run -n smart-environment ruff check scripts/streaming.py tests/test_streaming_tools.py
cd dashboard
conda run -n smart-environment npm.cmd test
conda run -n smart-environment npm.cmd run lint
```

Com o MediaMTX e um transmissor ativos, também na pasta dashboard:

```bat
conda run -n smart-environment npm.cmd run test:stream-transport
```

Type-check dos dois módulos novos passou. O `tsc --noEmit` global ainda aponta
declarações `Fetcher` e `D1Database` ausentes no Worker preexistente; isso não foi
mascarado com `any` nem removido do escopo do compilador. Build e lint são separados.

## Segurança e próxima etapa

O perfil MediaMTX permite leitura/publicação anônimas **somente de processos locais**,
apenas em `camera1`. CORS não é autenticação; outros programas do mesmo computador
podem acessar esse vídeo. WHEP/WHIP compartilham o serviço WebRTC. Não há gravação,
STUN/TURN externo, credenciais no navegador, armazenamento de URL ou frames em disco.
O cliente não segue redirects HTTP e só apaga sessões da mesma origem/caminho.

Próximos passos: validar player com webcam e investigar a cadência real da captura;
testar carga gradativa; preparar acesso
autenticado à VM; depois cadastrar fontes persistentes e ligar IA por metadados
temporais separados. A análise não deve bloquear nem recodificar o vídeo exibido.

Referências: [MediaMTX 1.20.1](https://github.com/bluenviron/mediamtx/releases/tag/v1.20.1),
[WHEP no navegador](https://mediamtx.org/docs/read/web-browsers),
[codecs WebRTC](https://mediamtx.org/docs/features/webrtc-specific-features),
[framesDecoded](https://developer.mozilla.org/en-US/docs/Web/API/RTCInboundRtpStreamStats/framesDecoded),
[requestVideoFrameCallback](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback).
