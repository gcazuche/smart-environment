# SE-02 — Pesquisa técnica

Atualizado em: 2026-08-14

## Escolha do primeiro detector

O PoC começará com `HOGDescriptor` e o classificador de pessoas padrão do OpenCV. A
documentação oficial descreve um classificador treinado para janela 64×128 e a função
`detectMultiScale` para devolver retângulos em diferentes escalas:

- <https://docs.opencv.org/4.12.0/d5/d33/structcv_1_1HOGDescriptor.html>
- <https://docs.opencv.org/4.13.0/d8/d61/samples_2tapi_2hog_8cpp-example.html>

OpenCV `4.13.0.92` possui wheel Windows para Python 3.11/3.12 e metadata Apache 2.0:

- <https://pypi.org/project/opencv-python/4.13.0.92/>
- <https://github.com/opencv/opencv>

## Trade-off

HOG evita peso externo, conta múltiplas detecções, funciona offline/CPU e mantém o
primeiro patch pequeno. Porém, favorece pessoas com corpo inteiro e postura vertical.
Pessoa sentada perto da webcam, oclusão e enquadramento parcial podem gerar falso
negativo. Por isso a interface do detector será substituível e o PoC não alegará
acurácia ou prontidão comercial.

Uma evolução possível é o MP-PersonDet do OpenCV Zoo, que detecta partes superior e
completa do corpo e declara Apache 2.0 para os arquivos do modelo. Ele exige modelo
ONNX e decoder adicional, então não entra antes de medir o baseline:

- <https://github.com/opencv/opencv_zoo/tree/main/models/person_detection_mediapipe>

## Incremento híbrido executado

O wheel instalado também distribui `haarcascade_upperbody.xml`, classificador 22×18
para parte superior. O cabeçalho do próprio arquivo concede redistribuição e uso em
fonte/binário com ou sem modificação, sob condições de atribuição e não endosso
(licença BSD-like). O protótipo combina esse cascade com o HOG, equaliza o frame em
cinza e deduplica caixas sobrepostas. Isso evita dependência/download novo, mas não
substitui avaliação de falso positivo, falso negativo, latência e CPU.

## NanoDet selecionado no Hugging Face

O baseline ativo passou para `opencv/object_detection_nanodet`, mantido pela Open
Source Vision Foundation no Hugging Face. A model card identifica NanoDet-m-plus-1.5x
com entrada 416 × 416, AP50 de 67,5 e mAP de 41,8 para `person` no COCO 2017 val. Esses
números são apenas referência do modelo, não resultado deste projeto.

- revisão: `5bfd47077350a726ad440dd7bd1e1e35e8ebcfb2`;
- peso FP32: 3.800.954 bytes;
- SHA-256: `4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186`;
- licença declarada para todos os arquivos do diretório: Apache-2.0;
- runtime: OpenCV DNN/CPU já instalado, sem PyTorch ou serviço de inferência.

O MP-PersonDet também foi analisado: é menor e mais rápido, mas o exemplo oficial avisa
que normalmente apenas uma pessoa oferece bom desempenho. Como o produto precisa
contar várias pessoas, NanoDet foi preferido. YOLOX é maior e mais lento nos benchmarks
oficiais do mesmo Zoo. Imagens aleatórias da internet não foram incorporadas: o próximo
gate usará amostras autorizadas/sintéticas com origem e licença registradas.

## Threat model resumido

- **Ativo:** frames da webcam e privacidade da pessoa observada.
- **Entrada não confiável:** dispositivo, frame nativo e teclas da janela.
- **Fronteiras:** câmera→processo OpenCV e processo→janela local.
- **Ameaças:** persistência acidental, handle órfão, frame em log, loop invisível,
  detecção falsa apresentada como fato e crash em biblioteca nativa.
- **Controles:** nenhum writer/rede, cópia só para anotação, `finally/release`, limite de
  frames no modo headless, linguagem de estimativa e testes com fakes.
