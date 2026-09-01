# SE-04 — Etapa 3D: dataset piloto autorizado sem celular

Data: 2026-08-27  
Estado: pré-rótulos gerados; revisão humana pendente

## Objetivo

Preparar as fotos locais autorizadas como um dataset piloto de detecção de objetos,
preservando a anonimização e separando rajadas por cena antes de qualquer fine-tuning.
Esta etapa valida o formato, os pré-rótulos e o fluxo de revisão; ela não produz um
modelo aprovado nem mede produtividade.

## Classes desta versão

| ID local | Classe | Regra |
|---:|---|---|
| 0 | `person` | trecho visível de cada pessoa autorizada |
| 1 | `laptop` | notebook inequívoco, aberto ou fechado |
| 2 | `mouse` | mouse físico; não inclui mão ou touchpad |
| 3 | `keyboard` | teclado físico externo; não inclui teclado integrado |

`cell_phone` não pertence ao mapa de classes porque não há exemplo positivo nas fotos.
Ele será tratado em outra versão, depois de uma coleta específica e autorizada.

## Entradas e saídas

- entrada original: ZIP local fornecido pelo usuário, somente leitura;
- entrada de treino: `user-anonymized-training-20260827-v2`, sem EXIF/XMP/ICC,
  nomes ou horários de origem;
- saída: `data/datasets/workstation-prelabels-v1/`, fora do Git;
- formato: imagens e rótulos YOLO separados em `train`, `val` e `test` por cena;
- evidência: `manifest.json`, `dataset.yaml` e prévias com caixas;
- anotações iniciais: pré-rótulos do Intel YOLO26, sempre marcados como pendentes de
  revisão humana.

## Regras de divisão

- frames da mesma rajada nunca atravessam `train`, `val` e `test`;
- duplicatas exatas são rejeitadas e quase duplicatas são agrupadas por cena;
- nenhuma ampliação é aplicada antes da divisão;
- fotos sintéticas não entram no teste real;
- o conjunto não é considerado representativo de outros ambientes ou câmeras.

## Privacidade e semântica

- processamento executado localmente no Conda `smart-environment`, sem envio feito pelo
  pipeline; como o repositório está sob uma pasta `OneDrive`, a sincronização do Windows
  precisa ser confirmada ou desativada antes de afirmar que os derivados não saíram do PC;
- rosto e região superior de pessoas são redigidos; conteúdo de telas é ocultado sem
  apagar deliberadamente o contorno dos objetos do escopo;
- originais, nomes e horários não são copiados para o dataset;
- não há identificação, reconhecimento facial ou ligação entre pessoas;
- não existem rótulos de `atividade_compativel`, `pausa_aparente`, `ausente`, emoção,
  intenção ou produtividade nesta etapa.

## Critérios de aceite

- classes de saída são exatamente `person`, `laptop`, `mouse` e `keyboard`;
- `cell_phone` não aparece no YAML nem nos arquivos de rótulo;
- todas as imagens de saída decodificam e não carregam metadados sensíveis;
- cada cena pertence a um único split e toda imagem selecionada possui rótulo, mesmo
  que vazio;
- caixas duplicadas por classe passam por NMS e caixas minúsculas são descartadas;
- manifest registra contagens, grupos, limitações e `ready_for_training=false`;
- prévias representativas são revisadas antes do próximo passo;
- testes, Ruff e mypy passam no ambiente Conda.

## Fora do escopo

- fine-tuning, escolha de hiperparâmetros ou publicação de pesos;
- inferência de atividade, postura, atenção ou uso de celular;
- integração ao monitor contínuo, dashboard ou Supabase;
- alegação de precisão, recall ou generalização antes da revisão humana.

## Próximo gate

Revisar todas as caixas e corrigir omissões/falsos positivos. Somente depois disso executar
um fine-tuning de caráter `dry-run`, comparar com o modelo pré-treinado e registrar
precisão, recall, mAP50-95 e falsos positivos por imagem.

Evidência atual: `STEP-03-AUTHORIZED-DATASET-VERIFICATION.md`.
