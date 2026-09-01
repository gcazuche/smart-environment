# SE-04 — Etapa 3A: referências de estações de trabalho

Data: 2026-08-22  
Estado: implementada; detecção de objetos ainda não integrada

## Objetivo

Preparar um conjunto mínimo e reproduzível de cenas reais de escritório para revisar o
próximo detector de computador/celular antes de conectá-lo à câmera. Este recorte é um
gate de dados da Etapa 3, não a implementação completa dos sinais de objetos.

## Fonte selecionada

- repositório: `shangzx/Open-Office-Workstation-Usage-Detection-Dataset`;
- conteúdo: três cenas reais de escritório aberto, todas ocupadas;
- licença declarada: `CC-BY-NC-SA-4.0`;
- finalidade aceita: TCC não comercial, referência qualitativa e smoke;
- pixels e manifest: `data/datasets/workstation-references/huggingface/`, fora do Git.

O recorte automático inicial do Open Images foi descartado após revisão visual: a
coocorrência de rótulos selecionou produtos e telas sem uma estação de trabalho real.

## Contrato do preparador

- lista de arquivos e SHA-256 fixados no código;
- URL HTTPS inicial e hosts de redirecionamento explicitamente permitidos;
- limite de tamanho e timeout;
- validação de hash e decodificação JPEG antes da escrita;
- arquivo existente adulterado falha fechado e não é sobrescrito;
- manifest registra licença, origem, dimensões e metadados do dataset;
- nenhum rótulo de produtividade, distração, postura ou intenção é criado.

## Critérios de aceite

- as três imagens são revisadas visualmente como cenas de escritório;
- hashes locais coincidem com os objetos LFS publicados;
- pixels e manifest permanecem ignorados pelo Git;
- download pode ser reexecutado no Conda `smart-environment`;
- limitações de volume e licença aparecem no README, avisos e checkpoint;
- testes de sucesso, adulteração e falha fechada passam sem rede.

## Fora de escopo

- treinar ou ajustar um modelo;
- alegar métrica representativa;
- classificar trabalho, pausa ou uso indevido de celular;
- abrir webcam/celular ou executar inferência de objetos;
- pose, tracking temporal, persistência ou Supabase.
