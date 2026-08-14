# Dashboard visual antecipado — Contexto

Data: 2026-08-14

## Decisão do usuário

Pausar temporariamente a melhoria da detecção de pessoas, montar primeiro o dashboard
na ordem combinada e depois retornar ao detector. O dashboard deve possuir um lugar
central que reúna todas as câmeras.

## Objetivo desta fatia

Criar uma interface reconhecível, navegável e responsiva usando dados simulados, para
validar organização, linguagem visual e fluxo antes de existirem API/Supabase.

## Dentro do escopo

- visão geral, todas as câmeras e detalhe de câmera;
- ambientes, indicadores e alertas;
- busca/filtro e modal visual de adição de dispositivos;
- uma webcam cadastrada; câmera IP e ESP32 apenas como opções futuras;
- desktop/mobile, labels acessíveis e build para Sites;
- marcação explícita de conteúdo simulado e ausência de frame real.

## Fora do escopo

- câmera ao vivo, captura no navegador ou stream;
- Supabase, Auth, API, banco, persistência e dados reais;
- classificar trabalho/relaxamento;
- declarar economia, produtividade ou qualidade de detecção;
- encerrar os requisitos completos da SE-06.

## Gate de segurança e privacidade

A UI não recebe pixels, URLs de stream ou credenciais. A prévia de pessoa é construída
com CSS. Alertas são indícios simulados para revisão humana e não decisões automáticas.
