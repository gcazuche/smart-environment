# Roadmap GSD — Smart Environment

Versão: 1.0
Atualizado em: 2026-08-11
Status global: detector híbrido da SE-02 implementado; avaliação representativa pendente

## Como ler este roadmap

A fundação técnica histórica `FND-01` permanece válida. As etapas `SE-*` representam o
novo produto e são executadas em ordem, uma tarefa atômica por vez. A mudança de escopo
não transforma planejamento em implementação nem valida serviços ainda não testados.

## Regras de execução

1. Executar somente a etapa explicitamente autorizada pelo usuário.
2. Antes de cada etapa, confirmar contexto, escopo, risco, dependências e aceite.
3. Não avançar com erro crítico, requisito crítico sem gate ou evidência obrigatória ausente.
4. Dados reais, câmera, Supabase e testes ativos exigem ambiente e autorização adequados.
5. Item não decidido permanece `unspecified`; não inventar retenção, base legal, volume,
   precisão, custo ou licença para liberar uma etapa.
6. Segurança, privacidade, acessibilidade e observabilidade são transversais.
7. Cada encerramento atualiza contexto, plano, resumo, verificação, estado e changelog.

## Gates transversais

- **Especificação:** objetivo, entradas, saídas e não objetivos estão claros.
- **Funcional:** critérios de aceite são demonstrados, não apenas descritos.
- **Qualidade:** lint, format-check, type-check, testes e build aplicáveis passam.
- **Segurança:** segredos, autorização, entradas e dependências têm controles/evidência.
- **Privacidade:** finalidade, minimização, retenção e acesso são proporcionais.
- **Evidência:** resultados reais e pendências são separados.
- **Reversão:** migração ou mudança operacional possui rollback/recuperação testável.

## FND-01 — Fundação técnica histórica

**Status:** concluída em 2026-07-17; preservada

Entregou ambiente Python reproduzível, configuração mínima, comando `doctor`, logging
seguro, tratamento de erros e gates. O smoke autorizado da webcam leu um frame em
memória por DirectShow e liberou o dispositivo. Isso não implementa captura contínua.

---

## SE-01 — Rebaseline Smart Environment

**Status:** concluída em 2026-08-11
**Objetivo:** substituir o planejamento biométrico pelo produto de ocupação sem identificação,
sustentabilidade, recursos e patrimônio, sem alterar código funcional.

**Entregas:** visão/MVP, arquitetura, stack, requisitos, backlog, riscos, testes, ADRs,
roadmap e checkpoint; plano antigo marcado como superado.

**Aceite:** documentos ativos concordam sobre `webcam → contagem sem identificação → evento
agregado → Supabase → painel web`; incertezas estão explícitas; biometria e avaliação
individual não fazem parte do MVP; código, dependências, câmera e serviços não mudam.

---

## SE-02 — Câmera e detecção local de pessoas

**Status:** em andamento — autorizada em 2026-08-14
**Objetivo:** provar primeiro o fluxo visual local usando a webcam do próprio computador.

**Entregas:** contrato de câmera, fonte simulada, adaptador OpenCV com fallback de
backend, detector híbrido substituível para corpo inteiro/parte superior, caixas,
contagem, CLI local e encerramento seguro.

**Aceite:** testes simulados cobrem abertura/leitura/falha/liberação e detecção 0/1/N;
a webcam autorizada abre e fecha em ciclo limitado; a interface exibe caixas e contagem;
nenhum frame é gravado, enviado pela rede ou incluído em logs.

**Gate de pessoas:** teste real somente no ambiente controlado do próprio responsável,
com áudio ausente e sem terceiros incidentais.

**Fora:** classificação trabalhando/relaxando, identidade, Supabase, API, dashboard web,
armazenamento, várias câmeras e promessa de precisão.

---

## SE-03 — Domínio, dados e Supabase seguro

**Status:** planejada; não iniciada
**Objetivo:** definir e provar contratos de dados com conteúdo sintético após o PoC local.

**Entregas:** entidades organização/local/ambiente/câmera; eventos agregados e
idempotentes; migrações; Auth/RBAC/RLS; configuração e PoC isolada do Supabase.

**Aceite:** integridade e isolamento positivos/negativos testados; evento não contém
identidade nem pixels; `service_role` só no backend; upgrade/downgrade, retenção inicial
e rollback demonstrados.

**Fora:** dados reais de colaboradores e histórico individual identificado.

---

## SE-04 — Ocupação e atividade observável

**Status:** planejada
**Objetivo:** transformar detecções em ocupação e estimativas observáveis de atividade.

**Entregas:** tracking curto efêmero; agregação por janela; estados `trabalho aparente`,
`pausa aparente` e `inconclusivo`; regras configuráveis; métricas de qualidade e limites.

**Aceite:** testes sintéticos/autorizados cobrem cenários normais e adversos; a UI deixa
claro que o resultado é estimativa; ambiguidade produz `inconclusivo`; nenhuma identidade
persiste; falsos positivos/negativos e CPU têm baseline medido.

**Fora:** rosto/nome, emoção, intenção, produtividade real, controle de ponto, ranking e
punição automatizada.

---

## SE-05 — API, outbox e sincronização

**Status:** planejada
**Objetivo:** transportar eventos agregados com segurança e tolerância à internet instável.

**Entregas:** API Python versionada, identidade do dispositivo, outbox SQLite limitada,
retry/backoff, idempotência, validação, auditoria e observabilidade.

**Aceite:** borda→API→Supabase funciona; replay não duplica; queda de rede não bloqueia
captura; payload inválido é recusado; segredos não chegam a cliente/log.

---

## SE-06 — Dashboard web MVP

**Status:** protótipo visual com dados simulados antecipado em 2026-08-14; integração planejada
**Objetivo:** exibir ocupação atual e histórica de forma simples, responsiva e autorizada.

**Entregas:** shell HTML/CSS/JS, login, cards de ocupação/saúde, histórico, gráficos,
filtros, estados loading/empty/error e acessibilidade básica.

**Aceite:** navegador mostra somente ambientes permitidos; desktop e mobile funcionam;
sessão/erros são seguros; nenhum stream ou URL de câmera é exposto.

**Checkpoint antecipado:** shell navegável em React/TypeScript com visão geral, lista
de câmeras, detalhe da webcam, ambientes, indicadores e alertas. Não possui Auth, API,
Supabase ou dados reais e não encerra os critérios de aceite da SE-06.

---

## SE-07 — Vertical ponta a ponta e piloto controlado

**Status:** planejada
**Objetivo:** validar uma webcam, um ambiente e um painel em cenário autorizado.

**Entregas:** fluxo E2E, runbook, métricas, teste de retenção/exclusão, backup/restore
inicial e relatório de limitações.

**Aceite:** latência, disponibilidade, erro de contagem e replay são medidos; zero pixel
ou identidade persiste; piloto possui aviso, responsável e critérios de interrupção.

**Fora:** rollout comercial e mais de uma câmera.

---

## SE-08 — Sustentabilidade

**Status:** planejada
**Objetivo:** converter ocupação em indicadores operacionais e oportunidades estimadas.

**Entregas:** horas-ocupação, períodos vazios, picos, fórmulas versionadas, premissas,
gráficos e relatórios.

**Aceite:** timezone e fórmulas são testados; estimativa é distinguida de medição real;
recomendação não aciona equipamento e requer interpretação humana.

---

## SE-09 — Recursos e patrimônio

**Status:** planejada
**Objetivo:** organizar ativos, zonas, estados e movimentações autorizadas.

**Entregas:** inventário, CRUD, RBAC, auditoria e eventos manuais/sintéticos; PoC visual
de objetos só após dataset, licença e métrica aprovados.

**Aceite:** acesso e mudanças são auditados; eventos não são vinculados automaticamente
a pessoas. A política não acusatória é implementada com o ciclo de alertas em SE-10.

---

## SE-10 — Alertas e relatórios operacionais

**Status:** planejada
**Objetivo:** detectar situações configuradas e apoiar resposta rastreável.

**Entregas:** regras de lotação, vazio prolongado, fora de horário, dispositivo offline
e patrimônio; deduplicação; confirmação/resolução; canais opt-in; exportações.

**Aceite:** limiar, janela e escopo são configuráveis; payload é minimizado; falha de
canal não bloqueia ingestão; ciclo completo deixa auditoria.

---

## SE-11 — Múltiplas câmeras e ESP32

**Status:** planejada
**Objetivo:** expandir somente depois da capacidade medida no piloto.

**Entregas:** registro/revogação de dispositivos, worker isolado por fonte, heartbeat,
limites, backpressure e gateway autenticado para ESP32/IP.

**Aceite:** falha de uma fonte não derruba as demais; credencial é individual; nenhum
stream fica público; capacidade e custo são medidos.

---

## SE-12 — Automação controlada, hardening e release

**Status:** planejada
**Objetivo:** preparar demonstração final e eventual evolução comercial com segurança.

**Entregas:** modo sugestão, adaptadores físicos opcionais, override/fail-safe, CI,
SAST/SCA/segredos/SBOM, observabilidade, restore, empacotamento e documentação TCC.

**Aceite:** automação começa desativada e segura; rollback/restore passam; gates ficam
verdes; riscos residuais, licenças e limitações são documentados.

## Rastreabilidade resumida

| Etapa | Requisitos principais |
|---|---|
| SE-01 | GOV-001, PRIV-001 |
| SE-02 | CAM-001 a CAM-004, OCC-001, OCC-003, PRIV-002, PRIV-004, OPS-001, TEST-002, TEST-003 |
| SE-03 | GOV-002 a GOV-004, DATA-001 a DATA-004, AUTH-001 a AUTH-003, SEC-001, SEC-002, PRIV-003, OPS-002 |
| SE-04 | OCC-002 a OCC-004, ACT-001 a ACT-004, PRIV-002, PRIV-003, TEST-003 |
| SE-05 | API-001 a API-004, SEC-003, SEC-004 |
| SE-06 | WEB-001 a WEB-004 |
| SE-07 | DATA-004, PRIV-004, PRIV-005, OPS-002, OPS-004, OPS-005, TEST-003, TEST-004 |
| SE-08 | SUS-001 a SUS-003 |
| SE-09 | AST-001, AST-002 |
| SE-10 | AST-003, ALT-001 a ALT-004 |
| SE-11 | DEV-001 a DEV-004, OPS-005 |
| SE-12 | GOV-005, PRIV-005, SEC-005, OPS-002 a OPS-005 |

`TEST-001` é transversal e permanece obrigatório em todas as etapas com mudança de código.

## Próximo gate

Continuar somente na SE-02 por SEB-017: comparar um detector de corpo parcial com
licença compatível em material sintético/autorizado e medir acerto, falso positivo,
latência e CPU. Não iniciar domínio/Supabase nem atividade observável nesse incremento.
