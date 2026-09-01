# SE-04 — Etapa 3D: verificação do dataset piloto autorizado

Data: 2026-08-27  
Resultado: pipeline aprovado; anotações ainda não aprovadas para treino

## Resultado produzido

- original preservado: `C:\Users\angel\Downloads\fotos.zip`;
- derivada usada: `data/datasets/workstation-references/user-anonymized-training-20260827-v2/`;
- saída: `data/datasets/workstation-prelabels-v1/`, ignorada pelo Git;
- 62 imagens de origem e 33 quadros representativos selecionados;
- split por oito cenas: 22 `train`, 5 `val` e 6 `test`;
- classes: `person`, `laptop`, `mouse` e `keyboard`;
- `cell_phone` ausente do mapa, do YAML e dos IDs YOLO;
- 29 frames redundantes permaneceram preservados na derivada, mas não entraram no piloto.

## Integridade e privacidade

- fingerprint das 62 imagens: `b2c242109e18987bbfb619c7d0562b251397fd3f2105bf837e5c83c1ef7ad804`;
- SHA-256 do manifest de anonimização: `c06328463e27804cd79dcae36c01e5c8129a17fb186b841693d0590b9ecdfae2`;
- 62/62 hashes de origem e 33/33 hashes de saída conferidos;
- nenhum JPEG selecionado contém APP1, APP2, APP13 ou comentário, e todos têm SOI/EOI válidos;
- a passagem de perfil facial nos dois sentidos elevou as regiões de face de 42 para 66;
- conteúdo de telas e zonas de cabeça continuam redigidos; `phones_redacted=0`;
- amostras representativas foram inspecionadas, mas não houve revisão humana de privacidade
  de 100% das imagens; por isso o manifest mantém `human_privacy_reviewed=false`;
- o caminho contém `OneDrive`; o pipeline não enviou arquivos, mas o cliente do Windows
  pode sincronizá-los conforme a configuração da máquina.

## Pré-rótulos encontrados

| Split | Pessoa | Laptop | Mouse | Teclado |
|---|---:|---:|---:|---:|
| Treino | 21 | 2 | 6 | 8 |
| Validação | 5 | 0 | 1 | 6 |
| Teste | 1 | 0 | 5 | 7 |
| **Total** | **27** | **2** | **12** | **21** |

Essas contagens são sugestões do modelo, não ground truth. A inspeção de prévias encontrou:

- caixas úteis em pessoas, mouses e teclados;
- uma pessoa não marcada em `frame_015`;
- falso positivo de pessoa em parte de uma cadeira em `frame_001`;
- falso positivo de pessoa em conteúdo/reflexo de tela em `frame_033`;
- somente dois laptops sugeridos e nenhum em validação/teste, apesar de haver objetos que
  precisam ser revistos manualmente.

## Gate

O dataset permanece `ready_for_training=false`. Antes de fine-tuning:

1. revisar as 33 imagens e corrigir todas as caixas;
2. garantir ground truth de cada classe em treino e avaliação, especialmente `laptop`;
3. fazer uma segunda revisão de pelo menos 20% das anotações;
4. concluir a revisão de privacidade antes de compartilhar qualquer derivado;
5. confirmar a política de sincronização do OneDrive;
6. só então alterar o status para pronto e executar um dry-run de treinamento.

## Verificações executadas

- testes focados do pipeline e anonimização: 16 aprovados;
- hashes, JPEGs, cobertura das cenas, ausência de sobreposição e IDs YOLO verificados;
- suíte completa: 115 testes e 11 subtestes aprovados;
- Ruff, 53 arquivos formatados, mypy em 46 fontes, mypy dos scripts, compileall e
  `git diff --check` aprovados.
