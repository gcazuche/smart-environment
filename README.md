# Multicam Inteligente

Fundação de uma plataforma autorizada de câmeras com reconhecimento facial local,
servidor central, operação offline e controles de privacidade. A **Fase 1** foi
concluída e a **Fase 2 (persistência)** foi aberta. A aplicação ainda não captura
câmeras continuamente nem processa biometria.

## Uso responsável

Biometria é dado pessoal sensível. Use somente em câmeras e ambientes autorizados,
com finalidade legítima, transparência, acesso mínimo, retenção definida e avaliação
jurídica aplicável (incluindo LGPD no Brasil). Não use para identificação secreta,
busca em redes sociais ou vigilância fora do escopo declarado.

## O que existe agora

- planejamento GSD persistente em `.planning/`;
- configuração mínima por variáveis de ambiente, com validação;
- comando de diagnóstico somente leitura;
- logging JSON seguro com correlação e tratamento global de exceções;
- ambiente recriável com `uv.lock`, build fixado e gates de qualidade;
- 28 testes aprovados em Python 3.11 e 3.12;
- arquitetura e roadmap para banco, câmeras, visão, GUI, API e sincronização.

A primeira fonte real é a webcam integrada. Um smoke test autorizado abriu o índice 0
por DirectShow, leu um frame 640×480 apenas em memória, sobrescreveu best-effort o
array recebido e liberou o dispositivo sem criar imagem/arquivo em `data/`. Isso valida
disponibilidade básica do hardware, não a
captura da Fase 4. A arquitetura prepara expansão para múltiplas webcams e ESP32, com
inferência local, Supabase como serviço central preferencial e frames completos somente
por evento/opt-in. Nenhum serviço externo, modelo facial ou dado biométrico foi conectado.

## Pré-requisitos

- Python 3.11 ou 3.12;
- `uv` 0.11.17 (a versão é verificada pelo `pyproject.toml`);
- Git;
- acesso à internet somente no primeiro `sync`, se o cache ainda não tiver os pacotes.

## Inicialização no Windows (PowerShell)

```powershell
uv sync --locked --extra dev --cache-dir .uv-cache
.\.venv\Scripts\python.exe -m app doctor --json
.\.venv\Scripts\python.exe -m pytest -q
```

Não é necessário ativar a venv nem afrouxar a política global do PowerShell.

## Inicialização no Linux

```bash
uv sync --locked --extra dev --cache-dir .uv-cache
.venv/bin/python -m app doctor --json
.venv/bin/python -m pytest -q
```

O projeto não instala OpenCV ou modelo facial nesta etapa. O smoke da webcam usou
`opencv-python-headless==4.13.0.92` em ambiente efêmero; a dependência só entrará no
lock principal quando a captura simulada e o contrato da Fase 4 forem implementados.

## Gates de desenvolvimento

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app main.py tests
.\.venv\Scripts\ruff.exe format --check app main.py tests
.\.venv\Scripts\mypy.exe app main.py tests
.\.venv\Scripts\python.exe -m compileall -q app main.py tests
uv build --offline --cache-dir .uv-cache
uv --cache-dir .uv-cache pip check --python .\.venv\Scripts\python.exe
```

## GSD

O fluxo manual adotado é:

1. ler `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`,
   `.planning/ROADMAP.md`, `.planning/STATE.md` e `.planning/DECISIONS.md`;
2. abrir o contexto/plano da fase atual;
3. executar uma tarefa atômica;
4. testar e registrar evidência;
5. atualizar verificação, resumo, estado e changelog.

A ferramenta pública GSD com suporte ao Codex pode ser instalada localmente, após
revisão de supply chain, com:

```powershell
npx get-shit-done-cc@latest --codex --local
```

Ela não foi instalada automaticamente. Detalhes: `.planning/research/GSD_TOOLING.md`.

## Estrutura atual e planejada

```text
.
├── app/                    # pacote; módulos entram na fase que os usa
│   └── configuration/
├── data/                   # runtime, ignorado pelo Git
├── scripts/                # scripts operacionais futuros
├── tests/
└── .planning/
    ├── research/
    ├── phases/01-foundation/
    ├── phases/02-database/
    └── debugging/
```

## Limitações atuais

- a webcam foi exercitada somente por um smoke de um frame; captura contínua,
  simulação, reconexão, FPS e integração da aplicação ainda não existem;
- nenhum teste de GPU, PostgreSQL/Supabase ou GUI foi executado;
- o motor/modelo facial depende de decisão técnica e de licença dos pesos;
- uma câmera inicial está confirmada; escala futura, modelos ESP32, retenção, base
  legal, hardware e região/plano do Supabase aguardam definição/validação;
- arquivo de log persistente não está ativo; no Windows, a configuração falha fechada
  para stderr até existir um adaptador DACL validado;
- `.env` é apenas um exemplo e não é carregado automaticamente; exporte as variáveis
  necessárias no processo ou use os defaults seguros do diagnóstico.

Consulte `.planning/STATE.md` para o checkpoint e o próximo passo exato.
