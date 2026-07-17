# Registro de riscos

Escala: probabilidade e impacto `baixa`, `média`, `alta`. Status inicial `aberto`.

| ID | Risco | Prob. | Impacto | Mitigação/detecção | Recuperação | Status |
|---|---|---:|---:|---|---|---|
| R-001 | falso positivo | média | alta | limiar+margem, calibração, testes negativos, revisão humana | corrigir evento e recalibrar | aberto |
| R-002 | falso negativo ou viés entre grupos | média | alta | métricas estratificadas e dataset autorizado representativo | recadastro/modelo/limiar | aberto |
| R-003 | uso sem base legal/autorização | média | alta | governança, finalidade, avisos, RBAC, auditoria | suspender processamento e eliminar conforme política | aberto |
| R-004 | vazamento de biometria/imagens | média | alta | minimização, criptografia, segregação, retenção, logs seguros | revogar acessos, conter, notificar conforme obrigação | aberto |
| R-005 | spoof por foto/tela/vídeo | alta | alta | vivacidade em camadas e estado inconclusivo | exigir verificação humana/segundo fator | aberto |
| R-006 | licença inadequada de pesos/modelos | média | alta | revisão antes do download/distribuição | trocar provider e re-embedding | aberto |
| R-007 | queda de servidor/internet | alta | média | cache local e fila idempotente | sincronizar com backoff | aberto |
| R-008 | evento duplicado/conflito | média | média | UUID, unicidade, hash e versões | conciliação auditada | aberto |
| R-009 | sobrecarga de CPU/RAM | alta | alta | filas limitadas, FPS/resolução adaptativos, métricas | reduzir carga/desativar câmera | aberto |
| R-010 | interface travada | média | alta | afinidade Qt e workers | reiniciar worker sem perder fila | aberto |
| R-011 | RTSP instável/credencial exposta | alta | média | timeout, backoff+jitter, secrets externos, URL mascarada | rotacionar credencial/reconectar | aberto |
| R-012 | corrupção do banco/fila | baixa | alta | transações, checks, backups e restore testado | restauração e replay idempotente | aberto |
| R-013 | disco cheio por snapshots | alta | alta | quota, retenção, deduplicação e alertas | pausar imagens, preservar metadados, limpeza segura | aberto |
| R-014 | upload/path traversal | média | alta | limite, magic bytes, nome gerado, diretório isolado | quarentena/remoção e auditoria | aberto |
| R-015 | brute force/sequestro de sessão | média | alta | Argon2id, rate limit, bloqueio, sessões curtas | revogar sessões e investigar | aberto |
| R-016 | dependência vulnerável/supply chain | média | alta | lock, hashes, SCA, fontes oficiais, revisão de update | rollback/upgrade e advisory | aberto |
| R-017 | incompatibilidade Python/GPU/driver | alta | média | matriz e smoke tests, CPU fallback | desativar GPU/voltar versão | aberto |
| R-018 | exclusão incompleta em cache/backups | média | alta | mapa de dados, tombstone, expiração, procedimento verificável | job de remediação e evidência | aberto |

## Riscos aceitos nesta etapa

Nenhum risco alto foi aceito. Vários permanecem abertos porque não há biometria,
modelo, rede ou banco implementado na Fase 1.
