# SE-04 — Etapa 1: contrato de atividade observável

Data: 2026-08-22  
Estado: implementada; inferência visual ainda não iniciada

## Contexto inicial

O primeiro cenário controlado é uma pessoa em uma estação fixa de escritório usando um
computador. A câmera pode observar sinais visuais, mas não conhece intenção, qualidade,
conteúdo da tarefa ou produtividade real.

## Estados aprovados

| Estado de máquina | Rótulo da interface | Critério observável inicial | Tempo padrão |
|---|---|---|---|
| `atividade_compativel` | Atividade compatível | pessoa na área e sinais de interação com computador, teclado, mouse, documento ou ferramenta | evidência em ao menos 60% da janela de 10 s |
| `uso_celular_aparente` | Uso aparente de celular | celular próximo às mãos de forma sustentada | evidência em ao menos 80% da janela de 10 s |
| `pausa_aparente` | Pausa aparente | pessoa presente sem sinais configurados suficientes | 60 s contínuos antes de confirmar |
| `ausente` | Ausente | câmera/modelo saudáveis e nenhuma pessoa na área | 3 s contínuos antes de confirmar |
| `inconclusivo` | Inconclusivo | baixa confiança, oclusão, conflito, falha ou ausência de regra suficiente | imediato e seguro por padrão |

Uma observação só pode sustentar outro estado quando pelo menos 70% da janela for
considerada confiável. Os tempos são valores iniciais do experimento e deverão ser
calibrados com vídeos autorizados; não são métricas de verdade ou desempenho humano.

## Ordem futura de decisão

1. Fonte, detector ou observação não confiável: `inconclusivo`.
2. Fonte saudável e ausência confirmada: `ausente`.
3. Uso de celular confirmado: `uso_celular_aparente`.
4. Evidência de tarefa configurada confirmada: `atividade_compativel`.
5. Presença sem evidência suficiente por 60 segundos: `pausa_aparente`.
6. Qualquer ambiguidade restante: `inconclusivo`.

O estado de celular descreve apenas o objeto observado. Ele não significa distração,
pois uma ligação, autenticação ou consulta pode fazer parte do trabalho.

## Critérios de aceite desta etapa

- exatamente cinco estados estáveis e documentados;
- política versionada e imutável para `office-computer`;
- tempos e proporções validados no carregamento;
- falha nunca convertida em ausência ou avaliação negativa;
- nenhuma identidade, face, emoção, ranking ou produtividade real no contrato;
- testes unitários independentes de câmera, modelo e internet.

## Fora de escopo

- desenhar a área da mesa;
- tracking, pose, mãos ou detecção de objetos;
- classificar frames ou emitir eventos reais;
- alterar o dashboard ou persistir resultados;
- reconhecimento facial, áudio e decisão disciplinar.
