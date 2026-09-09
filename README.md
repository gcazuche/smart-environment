# Smart Environment

Plataforma de ambiente inteligente para ocupação, sustentabilidade, recursos e
patrimônio. O projeto usa uma webcam autorizada, processamento local em Python/OpenCV,
Supabase e um dashboard web em HTML/CSS/JavaScript.

## Estado atual

### Modo servidor Ubuntu (implementado, instalação na VM pendente)

O modo opcional de servidor separa MediaMTX/WebRTC (vídeo contínuo) de um único modelo
OpenVINO CPU (análise configurável, inicialmente 2 FPS por câmera). Até quatro câmeras
são vinculadas por UUID ao catálogo existente do Supabase. O gateway verifica a sessão
e o vínculo de organização; a fila SQLite envia agregados por minuto e alertas sem
gravar imagens. O modo local anterior permanece disponível.

Veja **[como instalar e configurar na VM](docs/server-processing.md)**. O comando é
`python -m app.server --config config/server/server.local.toml --env-file config/server/.env.server.local`.
Use o ambiente Conda `smart-environment`, criado na VM com `environment.server.yml`.
O modelo e os arquivos `.env` não vêm no Git. Nenhum bootstrap precisa ser repetido.
Para conferir a instalação sem câmera/rede, execute `python -m app.server --preflight`.
30 FPS é a meta de transmissão, não uma taxa garantida de inferência; VM e câmeras
físicas ainda precisam de comissionamento. Não exponha os serviços internos à internet.

### Versões do projeto

O primeiro marco proposto é **v0.1.0**, preparado mas ainda não publicado. O histórico
de versões fica em [CHANGELOG.md](CHANGELOG.md), e os comandos para criar commit e
tag sem substituir versões anteriores estão no [guia de versionamento](docs/versioning.md).
Ao fechar um marco testado, informaremos seu conteúdo, limites e comandos; commits,
tags, pushes e Releases não serão executados automaticamente.

### Histórico do piloto local

O protótipo local oferece NanoDet/ONNX e Intel YOLO26/OpenVINO para detectar pessoas
inteiras ou parcialmente visíveis, inclusive múltiplas pessoas. Um agente local pode
processar simultaneamente a webcam do computador e o celular como câmera de rede. O
dashboard local mostra o JPEG anotado mais recente de cada câmera, com os retângulos do
detector e da área de trabalho configurada, sem gravar frames ou enviá-los à internet.
Os gráficos históricos continuam
simulados e a avaliação representativa ainda está pendente.

A fundação técnica anterior foi preservada:

- configuração mínima e comando de diagnóstico;
- logging JSON seguro e tratamento global de exceções;
- ambiente Conda isolado e recriável com `environment.yml`;
- 99 testes e 11 subtestes aprovados no checkpoint atual em Python 3.12;
- smoke autorizado da webcam integrada com um frame somente em memória.

O pacote, a CLI e as variáveis ainda usam o nome técnico legado `multicam` /
`MULTICAM_*`. A mudança de marca no código será planejada separadamente para não
quebrar configuração e compatibilidade durante uma etapa apenas documental.

## MVP planejado

```text
webcam autorizada
  → frame transitório no computador
  → detecção e contagem de pessoas sem identificação
  → evento agregado de ocupação
  → API Python / Supabase
  → dashboard web autenticado
```

O projeto futuramente estimará estados visuais como `trabalho aparente`, `pausa
aparente` ou `inconclusivo`. Isso não mede intenção nem produtividade real: a mesma ação
pode ter significados diferentes conforme o trabalho. Não haverá reconhecimento facial,
áudio, gravação contínua, ranking ou decisão disciplinar automatizada.

Mesmo uma contagem sem nome pode permitir inferências em ambientes pequenos. Por
isso, “sem identificação” não significa automaticamente “anônimo”: granularidade,
retenção e acesso serão avaliados antes de dados reais.

## Uso responsável

- Use somente câmera, local, horário e material de teste autorizados.
- Frames serão mantidos em buffers limitados e descartados; o baseline persiste apenas
  eventos agregados.
- Não instale em banheiro, vestiário, descanso ou local de alta expectativa de privacidade.
- O primeiro piloto não envolverá escolas nem crianças/adolescentes.
- Alertas patrimoniais são indícios para revisão humana e não afirmam furto ou culpa.
- Sustentabilidade começa como recomendação; nenhum equipamento é comandado no MVP.
- Base legal, responsáveis, avisos, retenção e RIPD aplicáveis devem ser definidos pela
  organização antes de dados reais. O projeto não substitui orientação jurídica.

## Próximas etapas

1. **SE-01 — Rebaseline:** concluída, somente documentação.
2. **SE-02 — Câmera e detecção local de pessoas:** em andamento.
3. **SE-03 — Domínio, dados e Supabase seguro.**
4. **SE-04 — Ocupação e atividade observável.**
5. **SE-05 — API, outbox e sincronização.**
6. **SE-06 — Dashboard web MVP.**
7. **SE-07 — Vertical ponta a ponta e piloto controlado.**
8. **SE-08 — Sustentabilidade.**
9. **SE-09 — Recursos e patrimônio.**
10. **SE-10 — Alertas e relatórios.**
11. **SE-11 — Múltiplas câmeras e ESP32.**
12. **SE-12 — Automação controlada, hardening e entrega do TCC.**

Consulte `.planning/ROADMAP.md` para entregas, critérios de aceite e itens fora de
cada etapa.

## Dashboard visual

O protótipo fica em `dashboard/` e inclui:

- visão geral com ocupação, saúde e atividade recente;
- área **Câmeras** com todos os dispositivos cadastrados;
- detalhes da webcam do computador e da câmera do celular;
- conexão local disponível para webcam e câmera IP; gateway ESP32 permanece futuro;
- ambientes, indicadores, sustentabilidade e alertas;
- navegação responsiva para computador e celular.

As contagens, o estado e a imagem anotada das duas câmeras podem vir do agente local. Os
gráficos históricos ainda são demonstrações. A área de câmera mostra vídeo somente em
`localhost`; mantém um JPEG limitado por câmera em memória e não grava nem publica o
vídeo na internet.

```powershell
cd dashboard
npm install
npm run dev
```

Abra `http://localhost:3000`. Para validar:

```powershell
npm run lint
npm test
```

### Teste com a câmera do computador e a do celular

Conecte os dois aparelhos à mesma rede privada e configure no celular um aplicativo
que disponibilize vídeo por MJPEG ou RTSP. Copie a URL local fornecida pelo aplicativo,
por exemplo `http://192.168.1.50:8080/video`, e execute em um terminal:

```powershell
conda run -n smart-environment multicam monitor --phone-url "http://192.168.1.50:8080/video" --detector intel
```

Por segurança, a área inicial de cada câmera cobre o frame inteiro. Para calibrar uma
região diferente por câmera, use coordenadas proporcionais entre `0` e `1` no formato
`esquerda,topo,direita,base`:

```powershell
conda run -n smart-environment multicam monitor --phone-url "http://192.168.1.50:8080/video" --detector intel --pc-work-zone "0.10,0.20,0.90,1.00" --phone-work-zone "0.05,0.15,0.95,1.00"
```

O retângulo aparece na prévia local. Uma pessoa é contabilizada na região quando ao
menos 20% da caixa detectada se sobrepõe a ela; isso não classifica trabalho ou distração.

Em outro terminal, abra o dashboard:

```powershell
cd dashboard
npm run dev
```

Ao acessar `http://localhost:3000`, o selo muda para **Agente local conectado** e a
área **Câmeras** mostra os dois vídeos com as caixas de detecção. A URL do celular deve
ser um IP privado ou nome `.local`; credenciais embutidas e endereços públicos são
rejeitados. O agente escuta apenas em `127.0.0.1:8765`, valida a origem da página e não
expõe a API na rede.

## Ambiente Conda oficial do projeto

O ambiente oficial chama-se `smart-environment`. Ele é separado do `base` e contém
Python 3.12, aplicação, OpenCV, NumPy, testes, coverage, lint, tipagem e build.

Para criar pela primeira vez no Anaconda Prompt:

```powershell
conda env create --file environment.yml
conda activate smart-environment
```

Para sincronizar depois de uma mudança em `environment.yml`:

```powershell
conda env update --name smart-environment --file environment.yml --prune
```

Não instale dependências deste projeto no `base`. O arquivo `uv.lock` permanece apenas
como evidência do ambiente histórico e não é a fonte ativa de instalação.

Baixe o peso NanoDet oficial do OpenCV/Hugging Face com revisão e SHA-256 fixados:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/download_nanodet.ps1
```

O peso fica em `models/nanodet/`, fora do Git. Origem e licença estão registradas em
`THIRD_PARTY_NOTICES.md`.

Para instalar o detector experimental Intel Person Detection/YOLO26 em OpenVINO:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/download_intel_person_detection.ps1
```

O script usa somente o Conda `smart-environment`, fixa a revisão do Hugging Face e
verifica os hashes dos pesos e dos artefatos OpenVINO. Os arquivos ficam fora do Git.

### Referências de estações de trabalho

O TCC usa três imagens revisadas do dataset
`shangzx/Open-Office-Workstation-Usage-Detection-Dataset` como referência qualitativa
de escritórios ocupados. Para baixá-las e gerar um manifest com licença, origem,
dimensões e SHA-256:

```powershell
conda run -n smart-environment python scripts/prepare_workstation_references.py
```

As imagens ficam em `data/datasets/workstation-references/huggingface/`, fora do Git.
O conjunto tem licença `CC-BY-NC-SA-4.0`, portanto é restrito ao TCC não comercial.
São apenas três cenas ocupadas: servem para revisão visual e smoke de detector, não para
treinar um modelo, medir qualidade representativa ou rotular produtividade/distração.

Para executar somente o smoke offline de `laptop`, `mouse`, `keyboard` e `cell_phone`:

```powershell
conda run -n smart-environment python scripts/smoke_office_objects.py
```

O relatório e as prévias anotadas ficam em `data/evaluations/office-object-smoke/`, fora
do Git. No checkpoint atual, o YOLO26/OpenVINO encontrou corretamente dois laptops nas
três imagens, com média de 43,2 ms por imagem, mas não encontrou o celular visível nem
com limiar diagnóstico de 0,10. Portanto, o sinal de computador está apenas demonstrado
e o de celular ainda não está aprovado.

Como alternativa provisória sem fotografias de pessoas reais, o projeto possui seis
cenas geradas por IA, todas com rosto oculto, incluindo laptop, celular, ambos, mesa vazia
e uma cena ambígua. Para validar o manifest e executar o smoke separado:

```powershell
conda run -n smart-environment python scripts/prepare_synthetic_workstations.py
conda run -n smart-environment python scripts/smoke_synthetic_office_objects.py
```

As imagens ficam em `data/datasets/workstation-references/synthetic/` e as saídas em
`data/evaluations/office-object-smoke-synthetic/`, ambas fora do Git. No limiar 0,25,
o modelo reconheceu laptop nas 4 cenas esperadas e celular em 3 de 4; a cena ambígua
perdeu o celular e gerou uma caixa duplicada/falsa de laptop. Em 0,10, o quarto celular
apareceu, mas vieram novos falsos sinais. O conjunto serve somente para smoke acadêmico:
não treina o modelo, não mede qualidade real e não classifica comportamento.

## Diagnóstico e testes no Windows

```powershell
conda activate smart-environment
python -m app doctor --json
python -m pytest -q
```

Para abrir a câmera e ver as caixas localmente, use `Q` ou `Esc` para encerrar:

```powershell
multicam camera
```

Para um teste invisível e obrigatoriamente limitado a 30 frames:

```powershell
multicam camera --no-display --max-frames 30
```

Para testar o detector Intel sem substituir o NanoDet padrão:

```powershell
multicam camera --detector intel
```

É possível selecionar outra câmera com `--index 1` e escolher explicitamente
`--backend dshow`, `msmf` ou `any`. O modo automático tenta os backends adequados ao
sistema e sempre libera o dispositivo ao sair.

Gates completos:

```powershell
ruff check app tests scripts
ruff format --check app tests scripts
mypy app tests
python -m compileall -q app tests scripts
python -m build
python -m pip check
```

Para automação sem ativar o shell, inclusive nas próximas execuções do Codex:

```powershell
conda run -n smart-environment python -m pytest -q
conda run -n smart-environment multicam camera --no-display --max-frames 30
```

## Webcam atual

Em 2026-08-14, o protótipo abriu a webcam por DirectShow e processou 30 frames em
memória antes de liberar o dispositivo. A primeira amostra teve zero detecções; a
revalidação no ambiente Conda detectou no máximo uma pessoa. Isso comprova o fluxo
básico, mas ainda não mede qualidade para diferentes posições, oclusões e iluminações.
A contagem de arquivos em `data/` permaneceu 5 antes e depois.

O baseline ativo é NanoDet-m-plus-1.5x/ONNX do OpenCV Zoo, filtrado somente para a classe
`person`. O peso FP32 de 3,8 MB veio do Hugging Face oficial, está fixado por revisão e
SHA-256 e roda localmente em OpenCV DNN/CPU. No smoke de 30 frames com limiar oficial
0,35, detectou no máximo uma pessoa; limiares 0,30 e 0,25 aumentaram falsos sinais e
foram rejeitados. Isso ainda não prova precisão nem prontidão comercial.

Em 2026-08-18, `Intel/person-detection` foi integrado como alternativa experimental
`--detector intel`. O YOLO26n FP16/OpenVINO detectou as duas pessoas da imagem pública
indicada pela Intel, com média de 32,1 ms em 20 inferências; o NanoDet retornou três
caixas e média de 90,1 ms na mesma amostra. Uma imagem não comprova superioridade. A
webcam estava indisponível nessa primeira tentativa. Depois, o monitor simultâneo abriu
a webcam por DirectShow e o celular por MJPEG privado; ambas ficaram online e uma
pessoa foi observada em cada fonte, sem persistência de frames. A comparação
representativa de qualidade ainda continua pendente.

## Estrutura

```text
.
├── app/                         # fundação, câmera e detecção local
├── data/                        # runtime ignorado; pastas antigas não são baseline
├── tests/                       # 99 testes e 11 subtestes automatizados
└── .planning/
    ├── phases/01-foundation/    # evidência histórica preservada
    ├── phases/02-database/      # plano antigo explicitamente superado
    ├── phases/se-01-replanning/ # rebaseline concluído
    ├── phases/se-02-person-detection/ # implementação e evidências atuais
    ├── research/
    └── debugging/
```

## Como continuar

Leia `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`,
`.planning/DECISIONS.md` e `.planning/STATE.md`. O próximo incremento deve criar um
pequeno teste controlado e aproximado de laptop/celular com a câmera autorizada antes de
qualquer integração em tempo real, ainda sem Supabase ou classificação de atividade.
