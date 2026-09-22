# Smart Environment

Plataforma de ambiente inteligente para ocupação, sustentabilidade, recursos e
patrimônio. O projeto usa câmeras autorizadas, processamento separado em Python/OpenCV,
Supabase e um dashboard Django com HTML/CSS/JavaScript puro.

## Estado atual

### Django é a aplicação web principal

A transição para **Django + HTML/CSS/JavaScript puro** está implementada em `app/web/`:

- Login Supabase, sessões mantidas no servidor, perfil e logout.
- URLs reais para visão geral, câmeras, ambientes, indicadores, alertas e histórico.
- Cadastros de ambientes, câmeras e regras com permissões e controle de versão.
- Ambientes com todas as suas câmeras, consulta de registros, gráficos por câmera e CSV.
- Transmissão WebRTC e análise independentes, com controles em JavaScript puro.
- Prévia JPEG do monitor local por configuração explícita, desabilitada por padrão.

O runtime web não depende de Node, React, TypeScript ou dos pesos de detecção.
`dashboard/` foi preservado como legado para consulta e reversibilidade, mas não é a
aplicação nem o caminho de CI principal. Sua existência no repositório não significa
que TypeScript seja usado para executar o Django.

**Implementação não equivale a aceite operacional:** autenticação e dados no Supabase
real, instalação na VM e transmissão com câmeras físicas ainda precisam de validação
no ambiente autorizado. Os testes locais não comprovam 720p/30 FPS no Hyper-V.
Nenhum bootstrap deve ser repetido; usuários, organização e dados existentes são reutilizados.

Consulte o [guia completo de configuração Django](docs/django-migration.md). O início
rápido local está na seção **Executar o dashboard Django**, abaixo.

### Avaliação de interação na estação (offline, experimental)

O projeto agora compara o detector atual com uma entrada que preserva as proporções
da imagem (`letterbox`), usando seis fotos públicas com origem/licença/hash registrados.
A avaliação detecta pessoa/laptop/mouse/teclado e relata proximidade, não produtividade
ou intenção. Não houve fine-tuning nem mudança automática no detector das câmeras.
Veja [como reproduzir a avaliação e seus limites](docs/workstation-evaluation.md).
Há também um modo de recortes `--include-detail` e duas cenas abertas adicionais:
ele recuperou propostas de teclados pequenos, mas acrescentou falsos positivos e
custou cerca de 5,1 vezes mais CPU nos ensaios locais. Continua somente offline,
sem promoção às câmeras e sem treino ou classificação de trabalho/distração.
O [editor local de revisão de caixas](docs/workstation-review.md) permite corrigir
anotações e salvar rascunhos; a comparação de precisão/recall só aceita revisões
explicitamente concluídas. Os oito exemplos reais continuam pendentes de revisão.
QA visual no navegador do usuário também está pendente; testes de lógica passaram.
Para continuar em outro PC, leia também `AGENTS.md` e `.planning/STATE.md`.

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

Em 20/09/2026, as tags locais **v0.1.0 e v0.2.0** foram novamente verificadas e
apontam para `f5b1f18`. O novo candidato da migração é **v0.3.0-alpha.1**
(versão Python `0.3.0a1`), ainda não publicado.
As mudanças posteriores ainda estão locais; não mova ou recrie essas tags para
incluí-las. Não houve commit/tag/push automático; publicação remota não foi verificada. O histórico
de versões fica em [CHANGELOG.md](CHANGELOG.md), e os comandos para criar commit e
tag sem substituir versões anteriores estão no [guia de versionamento](docs/versioning.md).
Ao fechar um marco testado, informaremos seu conteúdo, limites e comandos; commits,
tags, pushes e Releases não serão executados automaticamente.

### Preparação local sem acesso à VM

O painel evita consultas simultâneas e interrompe transmissão e consultas ao ocultar
a aba; a retomada exige nova ação explícita. Falhas temporárias de telemetria expiram
contagens/retângulos sem reiniciar o
vídeo remoto; acesso negado continua removendo a transmissão. A captura do servidor
reduz cópias de memória e a consulta periódica de fechamento de minutos roda a 1 Hz.

- [Desempenho, evidências e critérios de aceite](docs/performance-and-readiness.md).
- [Backup, verificação e restore da fila local](docs/server-backup.md).
- [Validação automática preparada para o GitHub](docs/continuous-integration.md).

O workflow ainda precisa executar no GitHub; não é evidência de instalação Linux.

### Histórico do piloto local

O protótipo local oferece NanoDet/ONNX e Intel YOLO26/OpenVINO para detectar pessoas
inteiras ou parcialmente visíveis, inclusive múltiplas pessoas. Um agente local pode
processar simultaneamente a webcam do computador e o celular como câmera de rede. O
dashboard local mostra o JPEG anotado mais recente de cada câmera, com os retângulos do
detector e da área de trabalho configurada, sem gravar frames ou enviá-los à internet.
Nesse piloto anterior, gráficos históricos eram simulados. O painel Django atual
consulta registros persistidos; não usa esses gráficos de demonstração. A avaliação
representativa do detector continua pendente.

A fundação técnica anterior foi preservada:

- configuração mínima e comando de diagnóstico;
- logging JSON seguro e tratamento global de exceções;
- ambiente Conda isolado e recriável com `environment.yml`;
- 99 testes e 11 subtestes aprovados no checkpoint histórico da fundação;
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

## Executar o dashboard Django

Abra um terminal na raiz do projeto. Se este PC ainda não possui o ambiente
`smart-environment`, crie o perfil leve da aplicação web uma única vez:

```powershell
conda env create --file environment.web.yml
```

Se o ambiente já existe, preserve-o e atualize somente o extra web. Os comandos
seguintes usam o Conda correto sem instalar no `base`:

```powershell
conda run --no-capture-output -n smart-environment python -m pip install -e ".[web]"
conda run --no-capture-output -n smart-environment python manage.py prepare_web
```

`prepare_web` cria `config/web/.env.web.local` somente se o arquivo não existir,
gera o segredo Django e aproveita a configuração local anterior quando disponível.
Não sobrescreve configurações existentes, não acessa o Supabase e não mostra chaves.
Em outro PC, preencha o arquivo privado conforme o
[guia Django](docs/django-migration.md), com o UUID da organização que já existe.
Não coloque configurações privadas no Git, em capturas de tela ou nos logs.

Depois de conferir a configuração, execute cada comando separadamente:

```powershell
conda run --no-capture-output -n smart-environment python manage.py migrate
conda run --no-capture-output -n smart-environment python manage.py check
conda run --no-capture-output -n smart-environment python manage.py runserver 127.0.0.1:8000 --insecure --noreload
```

`migrate` prepara **apenas o banco local de sessões e controle de tentativas de login**.
Não executa bootstrap nem migração no Supabase. Abra <http://127.0.0.1:8000/> e use
sua conta Supabase existente. Para encerrar, pressione `Ctrl+C` no terminal.

Mantenha `DJANGO_DEBUG=false`. Neste comando, `--insecure` habilita os arquivos
estáticos no servidor de desenvolvimento com DEBUG desligado; **não é uma opção
de implantação**. Não exponha `runserver` na LAN ou internet. A VM deve usar o serviço
WSGI e o proxy HTTPS descritos no guia, com hosts e origens configurados corretamente.

### Vídeo no servidor ou monitor local

O caminho principal usa `PROCESSING_SERVER_URL` apontando para o gateway configurado.
Cadastre ambientes e câmeras e associe seus UUIDs ao mapa do servidor. Na área
**Câmeras**, clique em **Conectar** para iniciar um stream. Cadastrar não abre uma
câmera automaticamente. Vídeo FPS e análise FPS são informados separadamente; dados
indisponíveis ficam desconhecidos, nunca uma contagem fictícia de zero.

Para o piloto local autorizado, existe a opção `LOCAL_MONITOR_ENABLED=true` no
arquivo privado. Ela é **opt-in**, destinada a quem autorizou o uso das câmeras e
já mantém o monitor local funcionando. Sem gateway configurado, o Django consulta
somente o monitor em `127.0.0.1:8765` e associa leituras pelo `monitor_id` cadastrado.
A prévia é JPEG limitado, sem promessa de 30 FPS. Ativar a opção não inicia o monitor
nem autoriza capturas; consulte o [guia Django](docs/django-migration.md) antes de usar.

O retângulo de pessoa/região, quando disponível, indica uma detecção espacial.
Presença ou proximidade de computador não classifica trabalho, distração ou produtividade.

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
│   └── web/                     # aplicação Django principal, templates e JS puro
├── config/web/                  # exemplos públicos e configuração privada ignorada
├── dashboard/                   # painel TypeScript legado, fora do runtime principal
├── manage.py                    # entrada dos comandos Django
├── data/                        # runtime ignorado; pastas antigas não são baseline
├── tests/                       # testes locais e integrações sintéticas
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
`.planning/DECISIONS.md` e `.planning/STATE.md`. O foco atual é fechar a preparação
local, validar a aplicação Django com a conta existente, preservar a nova versão e,
quando houver acesso, comissionar a VM por etapas.
As fotos e o treinamento permanecem pausados; celular não faz parte do dataset atual.
