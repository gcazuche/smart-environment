# Smart Environment

Plataforma de ambiente inteligente para ocupação, sustentabilidade, recursos e
patrimônio. O projeto usa uma webcam autorizada, processamento local em Python/OpenCV,
Supabase e um dashboard web em HTML/CSS/JavaScript.

## Estado atual

A **Etapa SE-02 — Câmera e detecção local** possui um primeiro protótipo executável.
Ele abre a webcam, procura pessoas, desenha caixas e mostra a contagem, sem gravar
frames. Supabase, API, dashboard e classificação de atividade ainda não entram.

A fundação técnica anterior foi preservada:

- configuração mínima e comando de diagnóstico;
- logging JSON seguro e tratamento global de exceções;
- ambiente recriável com `uv.lock` e gates de qualidade;
- 44 testes aprovados no checkpoint atual em Python 3.12;
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

## Pré-requisitos da fundação existente

- Python 3.11 ou 3.12;
- `uv` 0.11.17 instalado como pré-requisito;
- Git;
- internet no primeiro sync apenas se os pacotes não estiverem em cache.

## Diagnóstico e testes no Windows

```powershell
uv sync --locked --extra dev --cache-dir .uv-cache
.\.venv\Scripts\python.exe -m app doctor --json
.\.venv\Scripts\python.exe -m pytest -q
```

Para abrir a câmera e ver as caixas localmente, use `Q` ou `Esc` para encerrar:

```powershell
.\.venv\Scripts\multicam.exe camera
```

Para um teste invisível e obrigatoriamente limitado a 30 frames:

```powershell
.\.venv\Scripts\multicam.exe camera --no-display --max-frames 30
```

É possível selecionar outra câmera com `--index 1` e escolher explicitamente
`--backend dshow`, `msmf` ou `any`. O modo automático tenta os backends adequados ao
sistema e sempre libera o dispositivo ao sair.

Gates completos:

```powershell
.\.venv\Scripts\ruff.exe check app main.py tests
.\.venv\Scripts\ruff.exe format --check app main.py tests
.\.venv\Scripts\mypy.exe app main.py tests
.\.venv\Scripts\python.exe -m compileall -q app main.py tests
uv build --offline --cache-dir .uv-cache
uv --cache-dir .uv-cache pip check --python .\.venv\Scripts\python.exe
```

## Diagnóstico e testes no Linux

```bash
uv sync --locked --extra dev --cache-dir .uv-cache
.venv/bin/python -m app doctor --json
.venv/bin/python -m pytest -q
```

## Webcam atual

Em 2026-08-14, o protótipo abriu a webcam por DirectShow e processou 30 frames em
memória antes de liberar o dispositivo. O resultado foi zero detecções nessa amostra;
portanto, o acesso à câmera está validado, mas a qualidade para uma pessoa sentada e
parcialmente enquadrada ainda não está. A contagem de arquivos em `data/` permaneceu
5 antes e depois das tentativas inspecionadas.

O baseline HOG incluído no OpenCV é simples e mais adequado a corpo inteiro. Ele foi
mantido atrás de um contrato substituível para que o próximo incremento possa avaliar
um detector de corpo parcial sem reescrever a captura. A evidência não confirma
qualidade de produção nem ausência de escrita fora dos caminhos e APIs inspecionados.
OpenCV 4.13.0 e NumPy 2.3.5 estão fixados no lock principal.

## Estrutura

```text
.
├── app/                         # fundação, câmera e detecção local
├── data/                        # runtime ignorado; pastas antigas não são baseline
├── tests/                       # 44 testes automatizados
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
`.planning/DECISIONS.md` e `.planning/STATE.md`. O próximo incremento da SE-02 é
avaliar a qualidade do detector para uma pessoa sentada, ainda sem Supabase ou
classificação de trabalho/relaxamento.
