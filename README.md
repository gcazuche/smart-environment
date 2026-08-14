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
- ambiente Conda isolado e recriável com `environment.yml`;
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

É possível selecionar outra câmera com `--index 1` e escolher explicitamente
`--backend dshow`, `msmf` ou `any`. O modo automático tenta os backends adequados ao
sistema e sempre libera o dispositivo ao sair.

Gates completos:

```powershell
ruff check app main.py tests
ruff format --check app main.py tests
mypy app main.py tests
python -m compileall -q app main.py tests
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
