# Roadmap GSD — Smart Environment

Versão: 1.0
Atualizado em: 2026-08-11
Status global: Etapa SE-01 concluída; nenhuma funcionalidade Smart Environment implementada

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

## SE-02 — Domínio, dados e Supabase seguro

**Status:** próxima; não iniciada
**Objetivo:** definir e provar o contrato mínimo com dados sintéticos antes da câmera.

**Entregas:** entidades organização/local/ambiente/câmera; evento agregado e idempotente;
migrações; Auth/RBAC/RLS; configuração e PoC isolada do Supabase.

**Aceite:** integridade e isolamento positivos/negativos testados; evento não contém
identidade, pixels ou biometria; `service_role` só no backend; upgrade/downgrade,
retenção inicial e caminho de rollback demonstrados.

**Fora:** OpenCV, câmera real, detector, dashboard e dados de pessoas.

---

## SE-03 — Captura confiável de uma webcam

**Status:** planejada
**Objetivo:** integrar a primeira fonte real com lifecycle previsível e testes simulados.

**Entregas:** `CameraSource`, fonte simulada, adaptador OpenCV, fila limitada, health,
timeouts, start/stop/restart e liberação segura.

**Aceite:** simulação passa em automação; webcam autorizada abre/lê/libera em ciclos;
falhas são tipadas; memória permanece limitada; nenhum frame é salvo ou enviado.

**Gate de pessoas:** o smoke real ocorre em cenário controlado, vazio ou somente com o
próprio responsável informado, áudio desligado e sem terceiros. Qualquer outra pessoa
observada aguarda o gate completo de transparência/piloto em SE-07.

**Fora:** visão computacional, múltiplas fontes, RTSP e ESP32.

---

## SE-04 — Detecção e ocupação sem identificação

**Status:** planejada
**Objetivo:** transformar frames transitórios em eventos agregados sem identidade.

**Entregas:** escolha licenciada do detector; detecção 0/1/N; tracking curto efêmero;
agregação por janela; deduplicação; métricas de qualidade e desempenho.

**Aceite:** testes sintéticos/autorizados cobrem cenários normais e adversos; somente
eventos agregados persistem; falha produz `unknown`; CPU atende baseline medido.

**Fora:** rosto, nome, emoção, olhar, atenção, produtividade e punição automatizada.

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

**Status:** planejada
**Objetivo:** exibir ocupação atual e histórica de forma simples, responsiva e autorizada.

**Entregas:** shell HTML/CSS/JS, login, cards de ocupação/saúde, histórico, gráficos,
filtros, estados loading/empty/error e acessibilidade básica.

**Aceite:** navegador mostra somente ambientes permitidos; desktop e mobile funcionam;
sessão/erros são seguros; nenhum stream ou URL de câmera é exposto.

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
| SE-02 | GOV-002 a GOV-004, DATA-001 a DATA-004, AUTH-001 a AUTH-003, SEC-001, SEC-002, PRIV-003, OPS-002 |
| SE-03 | CAM-001 a CAM-004, PRIV-002, PRIV-004, OPS-001, TEST-002 |
| SE-04 | OCC-001 a OCC-004, PRIV-002, PRIV-003, TEST-003 |
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

Não iniciar SE-02 automaticamente. Antes, o usuário deve autorizar a etapa; então será
criado o plano atômico do domínio/Supabase e confirmados projeto de teste, credenciais,
região, retenção e limites do que pode ser exercitado.
