# Verificação — SE-04 Etapa 3C

Data: 2026-08-23  
Ambiente: Conda `smart-environment`, Python 3.12, CPU, Windows

## Resultado funcional

As seis imagens sintéticas foram validadas em 1536×1024, com hashes fixos, e revisadas
visualmente. Nenhuma exibe rosto. No limiar oficial `0.25`, o detector encontrou laptop
nas quatro cenas que o continham e celular em três das quatro cenas que o continham. A
cena negativa não gerou objeto-alvo.

O relatório bruto contém cinco caixas de laptop porque a sexta cena produziu duas caixas
sobrepostas para o mesmo notebook; uma delas invade a região do celular e é falsa/duplicada.
Nessa mesma cena, o celular não foi reconhecido em `0.25`. A média foi `41,4 ms` por imagem.

No diagnóstico `0.10`, o quarto celular apareceu com score `0.232`, mas também surgiram
um mouse falso sobre o celular, um teclado e um laptop extra. O limiar oficial permanece
`0.25`; baixar o limiar não resolve a ambiguidade com qualidade suficiente.

## Evidências

| Comando ou procedimento | Resultado |
|---|---|
| `conda run -n smart-environment python scripts/prepare_synthetic_workstations.py` | 6 PNGs válidos; hashes e dimensões aprovados |
| `conda run -n smart-environment python scripts/smoke_synthetic_office_objects.py` | laptops em 4/4 cenas; celulares em 3/4; negativo limpo; média 41,4 ms |
| mesmo script com `--confidence-threshold 0.10` e saída separada | celular 4/4, acompanhado de novos falsos sinais |
| inspeção visual das seis entradas e seis prévias | rostos ocultos; caixas corretas em 1–5; duplicação/falso de laptop em 6 |
| `conda run -n smart-environment python -m pytest -q` | 99 testes e 11 subtestes aprovados |
| `conda run -n smart-environment python -m ruff check app main.py scripts tests` | aprovado |
| `conda run -n smart-environment python -m ruff format --check app main.py scripts tests` | 48 arquivos formatados |
| `conda run -n smart-environment python -m mypy app main.py tests` | 43 arquivos sem erro |
| `conda run -n smart-environment python -m compileall -q app main.py scripts tests` | aprovado |
| `conda run -n smart-environment python -m build --no-isolation` | sdist e wheel gerados |
| `conda run -n smart-environment python -m pip check` | nenhuma dependência quebrada |

## Privacidade e limites

- `contains_real_people=false`, `faces_visible=false` e
  `activity_classification_performed=false` no manifest;
- webcam e celular não foram abertos;
- imagens, manifest, relatórios e prévias permanecem fora do Git;
- referências sintéticas avaliam somente o caminho técnico e têm forte diferença de
  domínio em relação às câmeras reais;
- objeto detectado não prova trabalho, distração, pausa ou intenção.

## Próximo checkpoint

Executar um teste curto e aproximado na câmera autorizada mostrando laptop, celular e
ausência de objeto. Encerrar e liberar a câmera; não integrar ao monitor contínuo nem
classificar atividade neste próximo incremento.
