# Multicam Inteligente

Fundação de uma plataforma autorizada de câmeras com reconhecimento facial local,
servidor central, operação offline e controles de privacidade. O projeto está na
**Fase 1 (fundação)**: ainda não captura câmeras nem processa biometria.

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
- testes unitários sem dependências externas;
- arquitetura e roadmap para banco, câmeras, visão, GUI, API e sincronização.

A primeira fonte real será uma webcam integrada. A arquitetura prepara expansão para
múltiplas webcams e ESP32, com inferência local, Supabase como serviço central
preferencial e frames completos somente por evento/opt-in. Nada disso, além da
fundação, foi conectado a hardware ou serviço real nesta fase.

## Pré-requisitos

- Python 3.11 ou 3.12 (3.12 é o baseline inicialmente validado);
- Git;
- dependências de desenvolvimento opcionais para pytest, Ruff e mypy.

## Inicialização no Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m app doctor --json
python -m pytest -q
```

Se a política do PowerShell bloquear ativação, execute diretamente
`.venv\Scripts\python.exe` nos comandos; não é necessário afrouxar a política global.

## Inicialização no Linux

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
python -m app doctor --json
python -m pytest -q
```

Não há dependência de câmera/modelo nesta fase. Dependências nativas serão adicionadas
por extras e lockfile depois da validação de SO, hardware e licença.

## Testes sem instalar extras

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app main.py
python -m app doctor --json
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
    └── debugging/
```

## Limitações atuais

- nenhum teste de câmera, GPU, PostgreSQL ou GUI foi executado;
- o motor/modelo facial depende de decisão técnica e de licença dos pesos;
- uma câmera inicial está confirmada; escala futura, modelos ESP32, retenção, base
  legal, hardware e região/plano do Supabase aguardam definição/validação;
- arquivo de log persistente não está ativo; ACL do Windows ainda precisa de gate;
- `.env` não é carregado automaticamente nesta fase; exporte as variáveis ou use os
  defaults seguros do diagnóstico.

Consulte `.planning/STATE.md` para o checkpoint e o próximo passo exato.
