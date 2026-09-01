# Registro de riscos — Smart Environment

Atualizado em: 2026-08-23
Postura: alto risco por câmeras em ambiente de trabalho; redução antes de expansão

| ID | Risco | Nível | Tratamento/gate | Estado |
|---|---|---|---|---|
| R-001 | Ocupação ser convertida em vigilância comportamental ou punição | crítico | estados estritamente observáveis; sem rótulo automático de distração, score ou punição; GOV-002/GOV-004; revisão humana | contrato inicial mitigado; controles de UI/API pendentes |
| R-002 | Biometria ser reintroduzida sem necessidade | crítico | schema sem identidade; novo projeto/RIPD/aprovação para qualquer mudança | mitigado no plano |
| R-003 | Eventos agregados permitirem reidentificação por horário/zona vazia | alto | granularidade mínima, limiar de grupo, restrição de consulta/exportação | aberto; parâmetros unspecified |
| R-004 | Frames vazarem por arquivo, log, cache, trace ou internet | crítico | um JPEG volátil por câmera; loopback/origem local/no-store; regressões de zero persistência | visualização local implementada; backend remoto e auditoria ampla pendentes |
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
| R-025 | Celular, pausa, leitura ou reflexão legítimos serem classificados como mau desempenho | crítico | descrever apenas sinais aparentes, manter `inconclusivo`, regras por contexto, janela temporal, validação e revisão humana | contrato inicial mitigado; classificador ainda inexistente |
| R-026 | Área mal calibrada excluir pessoas ou produzir contagem espacial enganosa | alto | coordenadas normalizadas validadas, padrão neutro de frame inteiro, sobreposição explícita, prévia visível e calibração por câmera | controles técnicos implementados; calibração física pendente |
| R-027 | Conjunto pequeno/não comercial ser tratado como base representativa | alto | limitar a referência a smoke qualitativo; exibir licença/limitações; exigir dados próprios autorizados e dataset maior para métricas | três imagens revisadas e manifestadas; avaliação representativa continua aberta |
| R-028 | Celular pequeno/ocluído não ser detectado e gerar falsa conclusão de trabalho | crítico | objeto ausente na saída significa `sem evidência`, nunca ausência real; testar aproximação/negativos e manter `inconclusivo` | falha nas imagens reais e em 1/4 cenas sintéticas no limiar 0,25; sinal ainda não aprovado |
| R-029 | Imagens sintéticas superestimarem qualidade em câmeras reais | alto | separar resultados sintéticos, testar compressão/distância/movimento e substituir por material real autorizado antes de métricas | 6 cenas sintéticas servem apenas de ponte; 3/4 celulares em 0,25 e erro na cena ambígua |

## Riscos aceitos na Etapa SE-01

- O nome do pacote, variáveis `MULTICAM_*` e CLI permanecem legados; renomear agora
  alteraria código e está fora da etapa documental.
- Supabase é a direção preferencial, mas ainda não foi tecnicamente validado.
- Retenção, responsáveis, base legal, região, detector, precisão e metas de capacidade
  permanecem `unspecified`; isso bloqueia dados reais, não o planejamento.
- A webcam foi validada apenas por um frame autorizado; captura contínua não existe.

Aceitação de risco nesta lista não substitui aprovação jurídica, de segurança,
privacidade ou operação na organização que eventualmente realizar o piloto.
