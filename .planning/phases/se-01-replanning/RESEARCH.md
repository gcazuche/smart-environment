# SE-01 — Pesquisa e fundamentos

Atualizado em: 2026-08-11

## Evidência local

- O checkpoint anterior estava limpo e a antiga Fase 2 não havia implementado runtime,
  schema ou Supabase; o pivot ocorre antes de dívida funcional relevante.
- Fundação, logs, configuração, lock e testes são independentes do domínio facial.
- O smoke autorizado já comprovou acesso básico à primeira webcam sem salvar o frame.
- Planejamento ativo antigo ainda era dominado por FaceEngine, embeddings, pgvector,
  PySide6 e cadastro de pessoas; precisava ser substituído antes de implementação.

## Síntese técnica

O menor fluxo que comprova valor é:

```text
webcam -> detecção de pessoa -> agregação -> evento -> Supabase -> dashboard
```

Processar o frame na borda reduz transferência e exposição. Um tracking curto pode
ajudar a contar dentro de uma janela, mas não deve persistir nem reidentificar pessoas.
Falha de câmera/modelo deve produzir `unknown`, pois “sem detecção” não prova ambiente
vazio. Supabase é uma preferência de produto que ainda exige PoC de Auth, RLS,
isolamento, região, custo, backup, restauração e exclusão.

## Privacidade e governança

A LGPD define dado pessoal como informação relacionada a pessoa identificada ou
identificável e dado anonimizado como aquele que não permite identificação com meios
técnicos razoáveis disponíveis. Por isso o projeto usa “evento agregado/sem
identificação” e não presume anonimato jurídico.

Os princípios de finalidade, necessidade, transparência, segurança, prevenção, não
discriminação e prestação de contas orientam os gates do projeto. A ANPD recomenda que
um RIPD detalhe dados, operações, finalidades, hipóteses, necessidade,
proporcionalidade, riscos e medidas; também orienta avaliar alto risco conforme o caso.

Fontes oficiais consultadas em 2026-08-11:

- Lei nº 13.709/2018, texto compilado:
  <https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm>
- Orientação da ANPD sobre RIPD:
  <https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd>

Esta pesquisa fundamenta requisitos de engenharia e não define a hipótese legal de
uma organização específica nem substitui aconselhamento jurídico.

## Riscos de interpretação evitados

- contagem agregada não é automaticamente anônima;
- presença de uma pessoa não mede produtividade ou atenção;
- ausência de detecção não prova ausência física;
- alerta patrimonial não prova furto ou autoria;
- oportunidade de energia não é economia medida;
- TCC executável não equivale a produto comercial pronto.

## Escolhas adiadas

Framework web, detector de pessoas, runtime de inferência, granularidade, retenção,
região/plano Supabase, Realtime/polling, metas de capacidade e gateway ESP32 serão
decididos por evidência na fase que os utiliza.
