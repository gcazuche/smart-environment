# SE-04 — Etapa 3B: smoke offline de objetos de escritório

Data: 2026-08-22  
Estado: implementada; integração com câmera ainda não iniciada

## Objetivo

Verificar se o mesmo YOLO26/OpenVINO já usado para pessoas consegue emitir sinais visuais
de computador e celular nas três referências revisadas, antes de tocar no monitor contínuo.

## Contrato

- classes permitidas: COCO 63 `laptop`, 64 `mouse`, 66 `keyboard`, 67 `cell_phone`;
- limiar oficial deste smoke: `0.25`;
- modelo XML/BIN continua validado pelos hashes já fixados;
- saída contém somente caixa, rótulo visual, score e fonte do detector;
- classe não permitida, frame inválido, modelo alterado ou saída inesperada é rejeitada;
- relatório afirma explicitamente que webcam e classificação de atividade não ocorreram;
- prévias são derivadas das imagens públicas e permanecem fora do Git.

## Critérios de aceite

- comportamento existente do detector de pessoas permanece compatível;
- classes de pessoa e demais classes COCO são filtradas no adaptador de objetos;
- as três referências geram relatório e prévia mesmo com zero detecções;
- caixas encontradas são revisadas visualmente;
- baixar o limiar é apenas diagnóstico separado, nunca ajuste para fabricar sucesso;
- presença/ausência de objeto não cria estado de trabalho, pausa ou distração.

## Fora de escopo

- webcam, celular como câmera ou monitor contínuo;
- relacionar objeto a uma pessoa;
- tracking, pose ou agregação temporal;
- classificador de atividade, persistência ou Supabase;
- alegação de precisão, recall ou prontidão comercial.
