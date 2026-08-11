# Smart Environment

Plataforma de ambiente inteligente para ocupação, sustentabilidade, recursos e
patrimônio. O projeto usa uma webcam autorizada, processamento local em Python/OpenCV,
Supabase e um dashboard web em HTML/CSS/JavaScript.

## Estado atual

A **Etapa SE-01 — Rebaseline** está concluída. Nesta etapa foram atualizados somente
escopo, arquitetura, requisitos, riscos e roadmap. Ainda não existe captura contínua,
detector de pessoas, Supabase, API ou interface web.

A fundação técnica anterior foi preservada:

- configuração mínima e comando de diagnóstico;
- logging JSON seguro e tratamento global de exceções;
- ambiente recriável com `uv.lock` e gates de qualidade;
- 28 testes aprovados no checkpoint anterior em Python 3.11 e 3.12;
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

O MVP mede desempenho **do ambiente**. Não mede desempenho de funcionários e não
infere atenção, distração, emoção, produtividade ou jornada. Também não usa
reconhecimento facial, embeddings, áudio, gravação contínua ou decisão disciplinar
automatizada.

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
2. **SE-02 — Domínio, dados e Supabase seguro:** próxima, ainda não autorizada.
3. **SE-03 — Captura confiável de uma webcam.**
4. **SE-04 — Detecção e ocupação sem identificação.**
5. **SE-05 — API, outbox e sincronização.**
6. **SE-06 — Dashboard web MVP.**
7. **SE-07 — Vertical ponta a ponta e piloto controlado.**
8. **SE-08 — Sustentabilidade.**
9. **SE-09 — Recursos e patrimônio.**
10. **SE-10 — Alertas e relatórios.**
11. **SE-11 — Múltiplas câmeras e ESP32.**
12. **SE-12 — Automação controlada, hardening e entrega do TCC.**

Nada após SE-01 foi iniciado automaticamente. Consulte `.planning/ROADMAP.md` para
entregas, critérios de aceite e itens fora de cada etapa.

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

Um smoke autorizado em 2026-07-17 tentou MSMF e abriu a webcam `USB2.0 HD UVC
WebCam` por DirectShow. Foi lido um frame 640×480 somente em memória, o array recebido
foi sobrescrito best-effort e o dispositivo foi liberado. Nenhuma imagem ou arquivo
novo apareceu em `data/` durante esse teste.

Essa evidência confirma acesso básico naquele computador. Não confirma captura
contínua, backend portátil, índice fixo, detector ou ausência de escrita fora do escopo
observado. OpenCV foi usado em ambiente efêmero e ainda não está no lock principal.

## Estrutura

```text
.
├── app/                         # fundação Python; módulos funcionais são futuros
├── data/                        # runtime ignorado; pastas antigas não são baseline
├── tests/                       # 28 testes da fundação
└── .planning/
    ├── phases/01-foundation/    # evidência histórica preservada
    ├── phases/02-database/      # plano antigo explicitamente superado
    ├── phases/se-01-replanning/ # checkpoint atual
    ├── research/
    └── debugging/
```

## Como continuar

Leia `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`,
`.planning/DECISIONS.md` e `.planning/STATE.md`. A próxima etapa só começa após
autorização explícita; sua primeira tarefa é definir finalidades, dados e responsáveis,
antes de criar schema ou conectar o Supabase.
