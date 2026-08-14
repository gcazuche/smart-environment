# Registro de riscos — Smart Environment

Atualizado em: 2026-08-11
Postura: alto risco por câmeras em ambiente de trabalho; redução antes de expansão

| ID | Risco | Nível | Tratamento/gate | Estado |
|---|---|---|---|---|
| R-001 | Ocupação ser convertida em vigilância comportamental ou punição | crítico | excluir distração/produtividade do MVP; GOV-002/GOV-004; revisão humana | mitigado no plano; controle técnico pendente |
| R-002 | Biometria ser reintroduzida sem necessidade | crítico | schema sem identidade; novo projeto/RIPD/aprovação para qualquer mudança | mitigado no plano |
| R-003 | Eventos agregados permitirem reidentificação por horário/zona vazia | alto | granularidade mínima, limiar de grupo, restrição de consulta/exportação | aberto; parâmetros unspecified |
| R-004 | Frames vazarem por arquivo, log, cache, trace ou rede | crítico | buffers limitados; invariant e regressões de zero persistência | caminho local sem writer/rede; auditoria ampla pendente |
| R-005 | Câmera falhar e sistema declarar ambiente vazio | alto | estado `unknown`, health e último sucesso; nunca inferir vazio da falha | aberto |
| R-006 | Contagem errada orientar decisões inadequadas | alto | medir FP/FN por cenário, confiança, aviso e revisão humana | aberto |
| R-007 | Alerta patrimonial gerar acusação injusta | alto | linguagem não acusatória, correção e revisão auditada | mitigado no escopo; implementação pendente |
| R-008 | Recomendação de energia desligar recurso necessário | crítico | sugestão apenas no MVP; automação com override, redundância e fail-safe | contido fora do MVP |
| R-009 | Acesso cruzado entre organizações/locais no Supabase | crítico | backend + RLS + testes negativos cross-tenant | aberto; PoC pendente |
| R-010 | Chave privilegiada chegar ao navegador/dispositivo/log | crítico | `service_role` somente no backend; rotação, redaction e secret scan | aberto; nenhum segredo criado |
| R-011 | Retenção indefinida reconstruir rotinas de pessoas | alto | prazo por classe, eliminação verificável, limitar granularidade | aberto; prazos unspecified |
| R-012 | Backup existir mas não restaurar ou não eliminar dado vencido | alto | restore descartável; RPO/RTO; política para réplicas e backups | aberto |
| R-013 | Monitoramento oculto ou em área sensível | crítico | aviso, autorização, zones permitidas; proibir áreas privadas e áudio | contido no plano; piloto bloqueado |
| R-014 | Captura incidental de visitantes ou menores | alto | sinalização, enquadramento, horários; escolas/menores fora do primeiro piloto | aberto |
| R-015 | Modelo/pesos incompatíveis com uso comercial | alto | validar licença de código, pesos e dataset antes de baixar/adotar | NanoDet Apache-2.0 com hash/revisão; direitos do dataset e produção abertos |
| R-016 | Viés/baixa qualidade por luz, oclusão ou densidade | alto | dataset representativo autorizado, métricas segmentadas e fallback `unknown` | aberto |
| R-017 | Dependência vulnerável ou atualização quebrar runtime nativo | alto | pin, lock, SCA, smoke e rollback; CPU baseline | baseline parcial |
| R-018 | Supabase exceder custo/quota ou região não atender requisitos | alto | PoC, orçamento, quotas, residência e alternativa documentada | aberto |
| R-019 | Internet interromper ingestão e gerar backlog ilimitado | alto | outbox limitada, retenção, backoff e idempotência | planejado |
| R-020 | ESP32/stream futuro ficar público ou sem revogação | crítico | conexão de saída, TLS, credencial por dispositivo, gateway e limites | contido fora do MVP |
| R-021 | Automação/multicâmera começar antes do piloto medido | alto | gates SE-07/SE-11 e autorização por etapa | controlado pelo roadmap |
| R-022 | Documentos antigos guiarem implementação facial acidental | alto | marcar antiga Fase 2 e pesquisas como legado; STATE aponta somente SE-* | tratado em SE-01 |
| R-023 | Nome técnico `multicam` causar confusão com a marca Smart Environment | médio | declarar legado; planejar migração sem quebrar CLI/configuração | aceito nesta etapa |
| R-024 | TCC ser apresentado como produto comercial validado | alto | separar protótipo, piloto e produção; registrar evidências e limitações | aberto até SE-12 |

## Riscos aceitos na Etapa SE-01

- O nome do pacote, variáveis `MULTICAM_*` e CLI permanecem legados; renomear agora
  alteraria código e está fora da etapa documental.
- Supabase é a direção preferencial, mas ainda não foi tecnicamente validado.
- Retenção, responsáveis, base legal, região, detector, precisão e metas de capacidade
  permanecem `unspecified`; isso bloqueia dados reais, não o planejamento.
- A webcam foi validada apenas por um frame autorizado; captura contínua não existe.

Aceitação de risco nesta lista não substitui aprovação jurídica, de segurança,
privacidade ou operação na organização que eventualmente realizar o piloto.
