# SE-04 — Etapa 3C: referências sintéticas provisórias

Data: 2026-08-23  
Estado: implementada; substituição futura por material real autorizado

## Objetivo

Criar um conjunto pequeno, controlado e sem pessoas reais identificáveis para testar
qualitativamente os sinais de `laptop` e `cell_phone`. As imagens não são ground truth de
atividade, não servem para treinar o modelo e não substituem avaliação em câmera real.

## Contrato de privacidade e proveniência

- seis imagens geradas pela ferramenta integrada de imagens do OpenAI/Codex;
- personagens fictícios vistos de costas, sem rosto visível, ou mesa sem pessoa;
- nenhuma fotografia de colaborador, voluntário ou terceiro;
- pixels e manifest em `data/datasets/workstation-references/synthetic/`, fora do Git;
- nomes, hashes, dimensões, cenário e objetos visualmente esperados fixados no manifest;
- nenhum rótulo de produtividade, distração, intenção, emoção ou identidade;
- uso limitado ao protótipo acadêmico; uso comercial não foi analisado.

## Cenas fixadas

| Arquivo | Pessoa | Objetos visualmente esperados | SHA-256 |
|---|---:|---|---|
| `synth-01-laptop-typing.png` | sim | laptop | `cd7eb67474a64690a9d944859f1e47e84a85adf2e5018611d5e5980477b10045` |
| `synth-02-phone-handheld.png` | sim | celular | `ccda59d25bf383ab3d8a254a1032427cf26714e815d84d2ad5fa118827d6ab02` |
| `synth-03-laptop-phone-on-desk.png` | sim | laptop, celular | `3c586d91de9b9a9ee97bbf77782a82e9e0ddcd10526b2748f5d89b9839a37386` |
| `synth-04-empty-desk-devices.png` | não | laptop, celular | `beb493d2a683261cfd0252533bd79d7379be03f7150f2503ffe38d180e0a5d21` |
| `synth-05-pause-clear-desk.png` | sim | nenhum objeto-alvo | `f5c09d6a33e60943aff74118303ad1e8d7ba6ba88c0a34a9ed96320c6c460d44` |
| `synth-06-phone-use-laptop-open.png` | sim | laptop, celular | `2009e9a7c6d6e41f77d76b33e8b90f3fec1a95ebbd005260976ba927ba19ffc6` |

Todas têm 1536×1024 pixels. Os objetos esperados são observações por cena, sem caixas
manuais; por isso não constituem anotação suficiente para métricas de detecção.

## Prompt final comum

As seis gerações usaram `Use case: photorealistic-natural` e `Asset type: synthetic
computer-vision reference image for an academic office-object detector`, com estas
invariantes: uma única fotografia horizontal, pessoa fictícia somente, rosto totalmente
invisível, objetos sem marca e grandes o suficiente para detecção, sem texto legível,
logotipo, marca ou watermark, e aparência natural de escritório.

Variações aplicadas, uma geração independente por imagem:

1. Pessoa vista de costas digitando em um laptop aberto; nenhum celular.
2. Pessoa vista de costas segurando um celular totalmente visível; nenhum computador.
3. Pessoa digitando em laptop, com um celular separado e visível sobre a mesa.
4. Mesa desocupada com laptop aberto e celular separado; nenhuma pessoa ou parte corporal.
5. Pessoa em pausa neutra diante de mesa vazia; nenhum dispositivo eletrônico.
6. Cena deliberadamente ambígua: pessoa segurando celular com laptop aberto à frente.

## Critérios de aceite

- as seis imagens são inspecionadas visualmente e não mostram rosto;
- o preparador falha fechado para arquivo ausente ou hash alterado;
- manifest deixa explícitas origem sintética, limitações e ausência de classificação;
- smoke usa o mesmo modelo fixado e gera saída separada das referências reais;
- resultado zero significa apenas falta de evidência do modelo;
- a cena ambígua não recebe automaticamente rótulo de distração.

## Fora de escopo

- treinamento, fine-tuning ou métrica representativa;
- câmera, monitor contínuo, tracking, pose ou classificador de atividade;
- persistência de pessoas, eventos ou pixels no Supabase;
- afirmar que imagens geradas representam a distribuição de uma câmera real.
