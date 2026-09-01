# SE-04 — Etapa 2: área configurável da estação de trabalho

Data: 2026-08-22  
Estado: implementada; calibração física ainda não executada

## Objetivo

Permitir uma região retangular independente para cada câmera e observar geometricamente
quais caixas de pessoa se sobrepõem a essa região. Isso ainda não é uma classificação de
trabalho, pausa ou distração.

## Contrato

- formato: `esquerda,topo,direita,base`;
- cada coordenada é uma fração de `0` a `1` da largura ou altura do frame;
- os limites devem formar um retângulo com área positiva;
- uma caixa pertence à área quando ao menos 20% dela se sobrepõe ao retângulo;
- o padrão neutro do monitor cobre o frame inteiro até ocorrer calibração manual;
- a API local expõe apenas geometria normalizada e contagem agregada na área;
- a prévia JPEG volátil desenha a área, mas nenhum pixel adicional é persistido.

Exemplo para usar a parte central e inferior de uma câmera:

```powershell
--pc-work-zone "0.10,0.20,0.90,1.00"
```

## Critérios de aceite

- coordenadas inválidas, invertidas, vazias, infinitas ou fora de `0..1` são rejeitadas;
- a mesma configuração funciona em resoluções diferentes;
- câmera do computador e celular aceitam áreas independentes;
- original do frame permanece inalterado durante anotação;
- falha de câmera limpa a contagem espacial anterior;
- nenhuma identidade ou estado de atividade é criado.

## Fora de escopo

- selecionar a área com o mouse ou pelo dashboard;
- detectar mesa, teclado, celular, mãos ou postura;
- tracking, agregação temporal e classificação de atividade;
- salvar configurações no banco ou conectar Supabase.
