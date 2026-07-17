# Pesquisa inicial — segurança, privacidade e arquitetura

**Projeto:** sistema autorizado de câmeras inteligentes com reconhecimento facial
**Data de referência:** 2026-07-17
**Estado:** pesquisa de arquitetura (`design-only`); não substitui RIPD, parecer jurídico, teste de segurança nem homologação biométrica
**Nível de segurança adotado:** alto
**Escopo operacional assumido:** instalação privada e autorizada, com inferência local, clientes eventualmente offline e servidor central
**Testes ativos:** não autorizados e não executados nesta etapa

## 1. Limite entre orientação técnica e aconselhamento jurídico

Este documento define controles técnicos, premissas de arquitetura e perguntas de governança. Ele **não é aconselhamento jurídico** e não conclui qual hipótese legal autoriza cada operação. Essa decisão cabe ao controlador, com participação do encarregado e de assessoria jurídica que conheça o contexto concreto, os titulares, o local das câmeras, as consequências do reconhecimento e os contratos aplicáveis.

A [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) classifica dado biométrico vinculado a pessoa natural como dado pessoal sensível. A própria ANPD confirma essa classificação e mantém o tema biometria em sua agenda regulatória.[^anpd-faq][^anpd-agenda] A [lista oficial de regulamentações da ANPD](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd), consultada na data acima, não registra resolução específica para tratamento biométrico; isso é uma constatação temporal, não uma garantia de estabilidade normativa. A conformidade deve ser revalidada antes do piloto com pessoas reais e novamente antes da produção.

## 2. Resumo executivo

1. Fotos faciais, recortes, frames, embeddings, resultados de vivacidade e vínculos entre presença, horário e local devem ser tratados como dados restritos. Um embedding **não deve ser considerado anônimo** só porque não é uma fotografia.
2. O caso reúne fatores típicos de alto risco: dado sensível, monitoramento sistemático, possível vigilância de zona acessível ao público, tratamento automatizado, múltiplos dispositivos e eventual presença de crianças ou adolescentes. A recomendação é elaborar um RIPD antes do primeiro tratamento real; a ANPD recomenda o RIPD antes do início de operações de alto risco.[^anpd-ripd]
3. A base legal deve ser definida **por finalidade e por operação**, sob o art. 11 da LGPD. Consentimento específico e destacado pode ser uma hipótese em certos contextos, mas não deve ser presumido como livre em relações com assimetria de poder, nem reaproveitado para finalidade incompatível. “Segurança” ou uma placa informativa, isoladamente, não constituem hipótese legal.
4. A arquitetura preferida mantém captura e reconhecimento no dispositivo de borda, envia ao servidor somente eventos mínimos e distribui a cada dispositivo apenas a galeria que ele está autorizado a usar. Imagens completas e recortes de desconhecidos ficam desativados até aprovação explícita da finalidade, da base legal, da retenção e do RIPD.
5. Autenticação humana e identidade de dispositivo são domínios separados: usuários usam sessão/OIDC e MFA conforme risco; dispositivos usam certificado individual, idealmente mTLS, credenciais revogáveis e escopo restrito à sincronização.
6. URL RTSP é simultaneamente segredo e entrada de rede. Ela precisa de campos separados, segredo fora da URL persistida, allowlist de câmera/sub-rede, egress restrito e proteção contra SSRF. `rtsps` com validação de certificado é preferível, mas é preciso confirmar também a proteção do canal de mídia: TLS no sinal de controle não garante, por si só, que RTP esteja cifrado. Câmeras que só suportam RTSP inseguro exigem VLAN/VPN isolada e aceitação formal do risco.[^rfc-rtsp][^owasp-ssrf]
7. Upload de foto deve ignorar o nome fornecido, usar identificador gerado, validar conteúdo por decodificação, limitar bytes/pixels/frames, remover metadados e reencodar em formato canônico. O arquivo fica em quarentena fora da área pública; caminhos nunca são montados a partir de input do usuário.[^owasp-upload][^owasp-traversal]
8. Vivacidade/PAD reduz, mas não elimina, ataques. Ela não detecta necessariamente injeção de frames, câmera comprometida, deepfake ou replay no canal. Um resultado “aprovado” não prova identidade. O sistema deve separar `match_status`, `pad_status` e decisão humana.[^nist-63b]
9. Nenhuma consequência adversa relevante — bloqueio, acusação, disciplina ou acionamento externo — deve ocorrer apenas por uma correspondência facial. A ANPD reconhece o direito de solicitar revisão de decisões unicamente automatizadas que afetem interesses do titular.[^anpd-rights]
10. O risco residual continuará alto para vazamento biométrico, abuso interno, falso positivo, bypass de vivacidade, revogação durante offline e câmera legada sem transporte seguro. Esses riscos precisam de aceite explícito do responsável, limites operacionais e revisão periódica.

## 3. Entradas normalizadas, fatos e lacunas

### 3.1 Entradas normalizadas

| Campo | Estado desta pesquisa |
|---|---|
| `repo_url_ou_snapshot` | workspace sem implementação no momento da pesquisa |
| `stack_tecnologica` | Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL/Supabase, OpenCV, ONNX Runtime, PySide6; decisão biométrica ainda em pesquisa |
| `nivel_seguranca` | `high` |
| `alvos_compliance` | LGPD e atos vigentes da ANPD; demais normas setoriais `unspecified` |
| `entregaveis_desejados` | threat model, arquitetura segura, minimização/retenção, controles e riscos residuais |
| `fontes_prioritarias` | LGPD/ANPD, OWASP, NIST, FastAPI, SQLAlchemy, PostgreSQL e RFC/IETF |
| `escopo_funcional` | cadastro, reconhecimento 1:N, desconhecidos, histórico, alertas, múltiplas câmeras, offline e sincronização |
| `restricoes_operacionais` | sem varredura ativa; sem uso ofensivo; dados reais ainda não autorizados |
| `ambiente_execucao` | Windows e Linux, local e distribuído; topologia final `unspecified` |
| `alvo_dast` | `unspecified` |
| `autorizacao_para_testes_ativos` | `no` nesta etapa |

### 3.2 Fatos verificados

- Biometria vinculada a uma pessoa natural é dado pessoal sensível.[^lgpd][^anpd-faq]
- A ANPD recomenda RIPD antes do tratamento quando a operação puder gerar alto risco; uso de dado sensível e vigilância/controle de zona acessível ao público são fatores relevantes na avaliação.[^anpd-ripd]
- O tema “dados pessoais sensíveis — dados biométricos” segue na agenda regulatória da ANPD; a regulamentação deve ser monitorada.[^anpd-agenda][^anpd-regulations]
- Incidente confirmado com dados pessoais que possa gerar risco ou dano relevante deve ser avaliado para comunicação. Pelo regulamento vigente, a comunicação à ANPD e aos titulares é, em regra, em três dias úteis, e registros de incidentes devem ser preservados pelo período regulamentar vigente.[^anpd-incident]
- Reconhecimento facial é probabilístico e pode apresentar diferenças de erro por grupo e por condição de captura. Qualidade de imagem, iluminação e ângulo afetam resultados.[^nist-demographics]
- Para autenticação facial, o NIST SP 800-63B exige PAD, trata biometria como informação pessoal sensível e não aceita biometria isolada como único fator. Esse padrão é uma referência de engenharia; não transforma vigilância ou identificação 1:N neste projeto em autenticação NIST.[^nist-63b]

### 3.3 Premissas de projeto

- O uso será autorizado pelo controlador e limitado a locais, câmeras, pessoas e finalidades cadastrados.
- O reconhecimento ocorrerá localmente; o servidor não será consultado a cada frame.
- O sistema oferecerá revisão humana e não aplicará decisão de alto impacto somente pelo algoritmo.
- Dados reais não serão usados em desenvolvimento sem conjunto aprovado, finalidade documentada e controles mínimos.
- Integrações externas de alerta ficarão desativadas por padrão.

### 3.4 Lacunas bloqueantes antes de dados reais

1. Identidade e contato do controlador, operadores, suboperadores e encarregado.
2. Finalidade concreta de cada câmera e consequência de uma identificação.
3. Natureza do local: privado, ambiente de trabalho, escola, condomínio, evento, área acessível ao público ou órgão público.
4. Categorias e quantidade de titulares; presença de crianças, adolescentes, idosos, empregados, visitantes ou público incidental.
5. Hipótese legal do art. 11 para cadastro, busca 1:N, desconhecidos, vivacidade, histórico, alerta e compartilhamento.
6. País/região de hospedagem, operadores de nuvem e eventual transferência internacional.
7. Quantidade de câmeras/dispositivos, modelo de rede, suporte a `rtsps`, firmware e capacidade de armazenamento seguro.
8. Prazo de retenção por classe de dado e fundamento de cada prazo.
9. Processo para aviso, exercício de direitos, contestação e revisão humana.
10. Política para dispositivo perdido, revogação offline e tempo máximo que uma galeria pode permanecer válida sem contato com o servidor.

## 4. Governança LGPD a validar

### 4.1 Registro de operações e base legal

O controlador deve manter inventário que relacione cada operação à sua finalidade, necessidade, titulares, dado, origem, destino, retenção, compartilhamento, risco e hipótese legal. A tabela abaixo é um roteiro; a coluna “decisão jurídica” permanece aberta de propósito.

| Operação | Dados | Risco principal | Decisão jurídica necessária | Default técnico até aprovação |
|---|---|---|---|---|
| Cadastro/enrollment | identidade, fotos, embeddings, qualidade, responsável | biometria permanente e coerção | hipótese do art. 11; liberdade e destaque do consentimento se escolhido; alternativa não biométrica | apenas dados sintéticos ou de voluntários de teste com autorização específica |
| Reconhecimento de cadastrados | frame efêmero, embedding de consulta, galeria, score, câmera/local/hora | vigilância e falso positivo | finalidade própria, necessidade e proporcionalidade; não presumir que a base do cadastro cobre busca contínua | frame em memória; sem gravação; evento mínimo |
| Detecção de desconhecidos | recorte/frame, embedding temporário, trilha de presença | coleta de não cadastrados e agrupamento | hipótese específica, transparência e necessidade; avaliar proibição/limites do contexto | armazenamento desativado; apenas contador agregado quando possível |
| Vivacidade/PAD | sequência de frames, movimento, score e decisão | inferências adicionais e falsa segurança | compatibilidade com a finalidade biométrica e transparência | guardar apenas estado e versão do método, não a sequência |
| Histórico e alertas | identidade/inferência, local, hora, decisão humana | perfil comportamental e consequência adversa | propósito, destinatários, revisão e prazo | alertas externos desativados; acesso mínimo |
| Correção/revisão | evento original, decisão do revisor, justificativa | exposição e manipulação indevida | canal de contestação e deveres de transparência | anexar correção; não apagar silenciosamente o evento original de auditoria |
| Suporte/diagnóstico | logs, metadados do dispositivo, possível imagem | acesso privilegiado remoto | operador/suboperador, contrato e instruções do controlador | sem imagem e sem acesso remoto por padrão |
| Backup/restore | cópia das classes acima | retenção indireta e vazamento em massa | prazo, finalidade, operadores, transferência e eliminação | criptografado, acesso separado e restauração testada |

### 4.2 Consentimento, quando aplicável

Se a hipótese escolhida for consentimento para dado sensível, o fluxo deve registrar de forma verificável:

- identidade do controlador e contato do encarregado;
- finalidade específica, locais/câmeras abrangidos e consequências do tratamento;
- categorias de dados, inclusive fotos, embeddings, desconhecidos e vivacidade;
- destinatários/operadores, transferências e prazo de retenção;
- versão do aviso, idioma, data, hora, meio e identidade de quem consentiu;
- informação clara sobre revogação e canal simples para exercê-la;
- alternativa real quando recusar não puder gerar prejuízo indevido;
- responsável legal e prova de representação quando cabível;
- novo consentimento para finalidade materialmente nova, sem caixas pré-marcadas ou consentimento genérico.

O sistema deve guardar prova de consentimento separada da biometria. Revogação cria tombstone de exclusão, suspende novas correspondências e propaga a remoção aos caches; ela não deve depender de o dispositivo estar online naquele instante para ser registrada pelo servidor.

### 4.3 Outras hipóteses do art. 11

- Obrigação legal/regulatória só pode ser usada quando houver norma concreta aplicável, registrada no inventário; política interna não basta.
- Proteção da vida ou da incolumidade física, exercício regular de direitos e prevenção à fraude/segurança do titular possuem textos e limites próprios. Não devem ser convertidos em autorização genérica para vigilância.
- A hipótese de prevenção à fraude e segurança do titular referida no art. 11 está ligada a processos de identificação e autenticação eletrônica; seu uso fora desse contexto exige análise jurídica específica.
- Órgãos públicos, escolas, relações de trabalho, condomínios, saúde e segurança pública podem ter normas adicionais. A exclusão do art. 4º da LGPD para certos tratamentos de segurança pública não autoriza automaticamente um sistema privado.
- Se PostgreSQL/Supabase ou storage forem hospedados, registrar região, operador, suboperadores, suporte e fluxo de backup. Hospedagem fora do Brasil ou acesso internacional deve ser avaliado sob a LGPD e o Regulamento de Transferência Internacional da Resolução CD/ANPD nº 19/2024; não presumir que “nuvem” implica ou exclui transferência internacional.[^anpd-regulations]

### 4.4 Crianças e adolescentes

Se houver menores, o melhor interesse é critério obrigatório. A ANPD entende que podem existir hipóteses dos arts. 7º ou 11 além do consentimento, desde que o melhor interesse prevaleça; portanto, não se deve nem presumir consentimento como solução única, nem dispensar a análise específica.[^anpd-children] Antes de incluir menores:

- elaborar seção própria do RIPD;
- justificar por que alternativa menos intrusiva não atende;
- usar linguagem adequada por faixa etária e informar responsáveis;
- reduzir galeria, câmeras, duração e consequências;
- oferecer revisão humana e alternativa prática;
- validar LGPD art. 14 e normas setoriais atuais com assessoria jurídica.

### 4.5 Direitos do titular e decisões automatizadas

O produto deve suportar confirmação de tratamento, acesso, correção, informação sobre compartilhamento, bloqueio/eliminação quando cabível, revogação e contestação/revisão.[^anpd-rights] O fluxo precisa:

- autenticar o solicitante sem exigir nova biometria como única opção;
- localizar dados por `person_id`, eventos, objetos, caches e backups;
- exportar informação inteligível, sem expor dados de terceiros nem segredos do modelo;
- registrar prazo, decisão, fundamento e executor;
- propagar correção/exclusão a dispositivos autorizados;
- manter tombstones para impedir ressurreição por cliente atrasado ou restauração de backup;
- documentar critérios do reconhecimento, limites, taxa de erro e papel da revisão humana em linguagem clara.

## 5. Ativos, classificação e minimização

| Ativo | Classificação recomendada | Localização permitida | Minimização/default |
|---|---|---|---|
| Fotos de cadastro | restrito — biométrico | cofre de objetos criptografado, se necessárias | preferir exclusão após validação do template, salvo justificativa documentada |
| Embeddings/templates | restrito — biométrico | cofre central e cache de borda criptografados | somente pessoas ativas e autorizadas para o dispositivo/local |
| Frames/recortes de evento | restrito — biométrico/contextual | objeto separado do evento | desativado para conhecidos; desconhecidos sob feature gate e TTL curto aprovado |
| Score e resultado de match | restrito | evento mínimo | guardar valor/intervalo necessário, threshold e versão para auditoria; não exibir amplamente |
| Resultado de vivacidade | restrito | evento mínimo | estado, confiança, versão e motivo; não guardar sequência por padrão |
| Identidade/categoria/observação | confidencial | banco central | campos livres limitados; proibir dados excessivos em “observações” |
| Localização, câmera e horário | confidencial/contextual | evento central e fila local temporária | granularidade necessária à finalidade; evitar perfil permanente |
| Credenciais RTSP, chaves, tokens, certificados | segredo | secret manager/keystore | nunca em URL exibida, log, export, `.env` real ou banco em claro |
| Senhas | verificador de autenticação | banco de identidade | hash Argon2id com salt; senha nunca recuperável[^owasp-password] |
| Logs de auditoria | confidencial, integridade crítica | serviço/partição separada | IDs pseudônimos; sem imagem, embedding, token, senha ou URL RTSP completa |
| Métricas operacionais | interno | telemetria | agregadas; sem nomes, fotos ou payloads |
| Backups | mesma classificação do dado de origem | repositório criptografado e isolado | escopo mínimo, prazo próprio e teste de restauração |

### 5.1 Embedding não é anonimização

O embedding continua ligado ou razoavelmente vinculável a uma pessoa e foi criado para reconhecê-la. Ele deve receber os mesmos controles essenciais de uma foto facial. Não se deve usar hash simples do vetor: busca por similaridade exige outra arquitetura e hash não remove o risco de associação.

Arquitetura preferida para a primeira versão distribuída:

- servidor guarda templates com criptografia por envelope e metadados de versão;
- dispositivo baixa somente o subconjunto autorizado, em pacote assinado e criptografado;
- chave de dados é protegida pelo keystore/TPM/DPAPI/Keychain do dispositivo quando disponível;
- índice vetorial é montado em memória e descartado no encerramento;
- cache persistente é criptografado e possui expiração;
- banco relacional guarda metadados e referências, não uma cópia redundante da face.

Se a decisão arquitetural for usar `pgvector` para busca central, o vetor precisa estar disponível ao processo do banco para indexação. Nesse caso, aceitar e registrar o trade-off: criptografia de disco/backup e TLS protegem fora do processo, mas não contra administrador ou processo PostgreSQL comprometido. Compensar com instância/role dedicadas, rede privada, RLS, acesso just-in-time, auditoria e galeria particionada. Como a inferência prevista é local, busca 1:N central não é requisito da primeira versão e não justifica por si só ampliar a exposição.

## 6. Arquitetura de referência e trust boundaries

```mermaid
flowchart LR
    S["Cena e titulares"] -->|"luz/imagem"| C["Câmera autorizada"]
    C -->|"USB ou RTSP/RTP"| CAP["Worker de captura isolado"]
    CAP --> Q1["Fila limitada de frames"]
    Q1 --> INF["Detecção, embedding e PAD local"]
    INF --> IDX["Índice autorizado em memória"]
    INF --> EVT["Fila local criptografada de eventos mínimos"]
    UI["PySide6 / operador"] -->|"sessão humana"| EDGE["Serviço local"]
    EDGE --> CAP
    EDGE --> EVT
    EVT -->|"mTLS + idempotência"| API["FastAPI central"]
    API --> AUTH["Identidade, sessão e autorização"]
    API --> DB["PostgreSQL: metadados e auditoria"]
    API --> OBJ["Cofre de objetos biométricos"]
    API --> KMS["KMS / secret manager"]
    API --> PKG["Manifestos assinados de configuração e galeria"]
    PKG -->|"sync verificado e atômico"| EDGE
    API --> EXT["Alertas externos desativados por padrão"]
    BCK["Backup isolado e criptografado"] <-->|"backup / restore controlado"| DB
    BCK <-->|"backup / restore controlado"| OBJ
```

### 6.1 Fronteiras de confiança

| ID | Fronteira | Dados que cruzam | Controle obrigatório |
|---|---|---|---|
| TB-01 | mundo físico → sensor | rosto, contexto, apresentação falsa | câmera autorizada, posicionamento, aviso, qualidade, PAD e proteção física |
| TB-02 | câmera/USB/RTSP → edge | frames, áudio potencial, credenciais/canal | nenhuma captura de áudio por padrão; allowlist, rtsps/VLAN, timeout e processo isolado |
| TB-03 | worker → pipeline de ML | arrays e metadados não confiáveis | filas limitadas, validação de dimensão/tipo, descarte do mais antigo, limites de memória |
| TB-04 | usuário → UI/API | credenciais, uploads, consultas, exports | autenticação, MFA por risco, autorização por recurso, rate limit e auditoria |
| TB-05 | edge → servidor | eventos, heartbeat, sync | mTLS, identidade por dispositivo, assinatura/hash, idempotência, anti-replay e schema estrito |
| TB-06 | API → DB/objeto/KMS | dados pessoais e segredos | roles separadas, TLS, criptografia por envelope, transação e menor privilégio |
| TB-07 | servidor → edge | galeria/config/tombstone/update | manifesto assinado, versão monotônica, expiração e instalação atômica |
| TB-08 | sistema → alertas/webhooks | possível identidade/local | allowlist, minimização, opt-in, assinatura e proibição de biometria no payload |
| TB-09 | produção → backup/suporte | base em massa e logs | credencial distinta, repositório isolado, criptografia, acesso dual e trilha de auditoria |

### 6.2 Invariantes de segurança

1. Nenhuma câmera, pessoa ou finalidade entra em operação sem autorização registrada.
2. Um dispositivo só recebe pessoas e configurações do seu escopo; ele não escolhe `tenant_id`, local ou câmera no payload.
3. Todo acesso é negado por padrão e verificado no servidor em cada requisição.[^owasp-authz]
4. Biometria, segredo e token nunca aparecem em log, trace, mensagem de erro ou export comum.
5. Nome de arquivo, caminho e URL fornecidos por usuário nunca se tornam diretamente operação de filesystem ou rede.
6. Eventos são idempotentes; replay não duplica alerta ou histórico.
7. Tombstone e revogação têm precedência sobre cadastro antigo e sobrevivem a restore/sync atrasado.
8. Falha de câmera fica isolada; falha de segurança fica fechada. Queue cheia descarta frame, não ignora autenticação nem amplia permissão.
9. `pad_status=inconclusive` nunca é convertido em `approved` por timeout, erro ou ausência do módulo.
10. Correspondência biométrica não produz sozinha decisão de alto impacto.
11. Exclusão alcança objeto, metadado, índice, cache e fila; backup segue política documentada e reaplica tombstones após restore.
12. Integração externa e diagnóstico remoto são `off` por padrão e exigem autorização explícita.

## 7. Ciclo de vida, retenção e eliminação

### 7.1 Fluxo mínimo por classe

**Cadastro**

1. Capturar frames em memória.
2. Rejeitar baixa qualidade e múltiplos rostos sem persistir.
3. Reencodar somente imagens aceitas e remover EXIF/GPS.
4. Gerar templates e validar duplicidade com acesso restrito.
5. Manter fotos aceitas somente se houver necessidade documentada (por exemplo, correção/recadastramento); caso contrário, eliminar após janela de validação aprovada.
6. Registrar finalidade, base legal, aviso/consentimento quando aplicável, modelo, versão, responsável e retenção.

**Reconhecimento contínuo**

1. Frame permanece na RAM e em fila limitada.
2. Embedding de consulta é efêmero.
3. Evento guarda o mínimo necessário: ID interno, câmera, horários, status, threshold/modelo, score necessário, PAD e origem.
4. Para conhecido, recorte/frame fica desativado por padrão.
5. Para desconhecido, armazenamento e agrupamento só são habilitados após aprovação jurídica/RIPD e possuem TTL curto, deduplicação e acesso mais restrito.

**Exportação**

- exigir permissão específica, justificativa, filtro, MFA/step-up para export sensível, marca d'água ou identificação do export, expiração do arquivo e auditoria;
- aplicar limite de volume e evitar exportar embedding, segredo ou URL RTSP;
- CSV deve neutralizar fórmulas iniciadas por `=`, `+`, `-` ou `@` quando aberto em planilhas;
- PDF/JSON devem ser gerados em worker limitado, sem carregar caminhos informados pelo usuário.

### 7.2 Política de retenção

Não há prazo universal seguro ou juridicamente correto. O sistema deve exigir política por classe, finalidade e local, com os campos:

```text
retention_policy_id
data_class
purpose_id
legal_basis_record_id
starts_at_event
retention_duration
review_interval
delete_mode
backup_expiry
legal_hold_rule
owner
approved_at
policy_version
```

Princípios:

- “indefinido” é inválido para biometria e imagens;
- eventos, imagens, embeddings, auditoria e backup têm prazos separados;
- inatividade ou fim da autorização interrompe reconhecimento e inicia eliminação conforme base/política;
- legal hold é excepcional, fundamentado, com escopo e expiração;
- job de limpeza gera relatório de contagem, não copia o conteúdo eliminado;
- restauração de backup reaplica imediatamente tombstones e políticas antes de reabrir o serviço;
- criptografia por chave de conjunto/pessoa pode apoiar criptoapagamento, sem dispensar a remoção lógica/física possível;
- métricas agregadas não devem permitir reidentificação.

## 8. Threat model inicial

### 8.1 Atores e capacidades

- usuário externo sem conta tentando API, upload ou URL de câmera;
- usuário autenticado fora do seu papel/local/câmera;
- administrador ou operador malicioso/curioso;
- atacante com senha/token roubado;
- dispositivo de borda perdido, adulterado ou comprometido;
- câmera/firmware/stream RTSP comprometido;
- invasor na rede entre câmera, edge e servidor;
- fornecedor, biblioteca, modelo ou pacote de atualização comprometido;
- erro humano de configuração, retenção, export ou backup;
- pessoa tentando spoof por foto, tela, vídeo, máscara ou injeção de frame.

### 8.2 Superfície de ataque

- endpoints de login, recuperação, sessão, cadastro, upload, câmera, teste de conexão, histórico, export, sync, heartbeat, alertas e administração;
- multipart, imagens, vídeos de teste, codecs/decoders e metadados;
- URL RTSP, DNS, redirects, protocolos e credenciais da câmera;
- processos OpenCV/ONNX/FFmpeg eventualmente usados;
- filas locais, cache de embeddings, SQLite/arquivos e keystore;
- API FastAPI, documentação OpenAPI, CORS, proxy e limites de request;
- PostgreSQL, storage de objetos, KMS/secret manager e backups;
- tokens humanos, certificados de dispositivo e bootstrap inicial;
- manifestos de galeria/configuração, pacote do modelo e atualizações;
- logs, traces, crash dumps, métricas, exports, suporte e diagnóstico remoto;
- webhooks/e-mail e demais integrações externas.

### 8.3 Registro de ameaças

Escala: probabilidade e impacto `B/M/A`; risco inerente e residual `B/M/A/C` (baixo, médio, alto, crítico). Como não há implementação, a coluna residual é **meta de arquitetura**, não evidência de eficácia.

| ID | Ameaça | P | I | Inerente | Controles principais | Residual-meta |
|---|---|---:|---:|---:|---|---:|
| TM-01 | vazamento de fotos/embeddings no banco, storage ou backup | M | A | C | envelope encryption, KMS separado, roles, rede privada, backup isolado, acesso JIT, auditoria | M |
| TM-02 | tomada de conta, força bruta ou recuperação abusiva | A | A | C | Argon2id, MFA admin, rate limit, detecção, sessão curta, refresh rotativo, recuperação forte | M |
| TM-03 | IDOR/BOLA permite ver câmera, pessoa, evento ou export de outro local | A | A | C | deny-by-default, ABAC por local/câmera, checagem por requisição, RLS, testes negativos | M |
| TM-04 | upload malicioso, decompression bomb, parser exploit ou path traversal | A | A | C | UUID, quarentena, allowlist, limite bytes/pixels, decode+reencode, sandbox, caminho canônico | M |
| TM-05 | URL RTSP causa SSRF, scan interno, acesso a metadata ou leitura de arquivo | A | A | C | campos separados, schemes/hosts/ports permitidos, DNS/IP revalidado, sem redirect, egress/VLAN | M |
| TM-06 | segredo RTSP vaza em banco, UI, log, erro ou export | A | A | C | secret manager, referência opaca, mascaramento, sanitização central e rotação individual | M |
| TM-07 | foto/tela/vídeo/máscara engana vivacidade | A | A | C | PAD em camadas, qualidade, desafio no cadastro, teste por câmera, estado inconclusivo, revisão | A |
| TM-08 | injeção/replay substitui frames antes do PAD | M | A | C | origem autorizada, canal protegido, isolamento, detecção de loop, timestamps, sensor/endpoint confiável | A |
| TM-09 | falso positivo, falso negativo ou diferença demográfica gera dano | A | A | C | validação representativa, threshold por caso, qualidade, top-k/unknown, revisão e métricas | A |
| TM-10 | edge falsifica, altera ou repete eventos de sync | M | A | A | certificado por dispositivo, mTLS, evento canônico assinado/hasheado, seq, idempotência e schema | M |
| TM-11 | sync atrasado ressuscita pessoa excluída ou usa galeria obsoleta | M | A | A | versão monotônica, tombstone prioritário, manifesto assinado, validade offline e apply atômico | M |
| TM-12 | furto do edge expõe galeria/fila offline | M | A | C | full-disk + envelope encryption, chave no keystore/TPM, cache mínimo, expiração, revogação | A |
| TM-13 | flood de frames/eventos esgota RAM, CPU, disco ou rede | A | M | A | filas limitadas, backpressure, quotas, circuit breaker, TTL, alerta de disco e isolamento por câmera | M |
| TM-14 | insider consulta/exporta biometria sem necessidade | M | A | C | separação de função, ABAC, step-up, aprovação para bulk, auditoria externa e revisão periódica | A |
| TM-15 | auditoria é apagada, forjada ou contém segredo | M | A | A | sink separado append-only, role só-insert, hash encadeado opcional, redaction e acesso restrito | M |
| TM-16 | pacote/modelo/dependência comprometido executa código ou altera resultado | M | A | C | lock/hash, SBOM, assinatura, SCA/SAST, provenance, atualização canário e rollback | M |
| TM-17 | backup não restaura ou restaura dados revogados | M | A | A | restore periódico em ambiente isolado, tombstones, reconciliação e relatório | M |
| TM-18 | desvio de finalidade, retenção excessiva ou vigilância secreta | M | A | C | RIPD, registro de operação, feature gate, aviso, política versionada, auditoria e revisão do encarregado | A |
| TM-19 | integração externa exfiltra identidade/local | M | A | A | off por padrão, payload mínimo, destination allowlist, assinatura, DPA/contrato e egress restrito | M |
| TM-20 | resposta a incidente tardia ou incompleta amplia dano | M | A | A | playbook, inventário, detecção, responsável, evidência, relógio confiável e exercícios de mesa | M |

## 9. Controles técnicos detalhados

### 9.1 Autenticação humana, sessão e autorização

**Decisão recomendada**

- Preferir OIDC/OAuth 2.0 com provedor mantido quando houver infraestrutura. Para autenticação interna, usar biblioteca madura e o padrão do FastAPI apenas como ponto de integração, não como prova de segurança.[^fastapi-auth]
- Hash de senha: Argon2id com salt automático e parâmetros calibrados no hardware; OWASP recomenda Argon2id para novos sistemas. Pepper opcional fica no KMS, nunca no banco.[^owasp-password]
- MFA obrigatório para administradores e para ações como export em massa, gestão de usuários, alteração de retenção, exclusão em massa, revelação/rotação de segredo e diagnóstico remoto.
- Rate limit por conta, origem e dispositivo; atrasos progressivos; não revelar se a conta existe; alerta de password spraying. Bloqueio não pode permitir DoS trivial contra uma conta.
- Recuperação de conta com tokens de uso único, curta validade, canal verificado e invalidação de sessões; administrador não recebe nem define senha conhecida do usuário.

**Sessões/tokens**

- Access token curto com `iss`, `aud`, `sub`, `exp`, `nbf`, `jti`, algoritmo fixo e `kid`; rejeitar algoritmo não esperado.
- Refresh token opaco, rotativo, armazenado como hash no servidor e revogável por sessão/dispositivo.
- PySide guarda segredo persistente no keystore do sistema, não em arquivo de configuração. Interface web, se existir, prefere cookie `Secure`, `HttpOnly`, `SameSite` e proteção CSRF.
- Logout, desativação, troca de senha sensível e redução de privilégio revogam refresh tokens.
- Nunca colocar papel/permissão mutável de longa duração apenas no JWT; permissões de alto risco são reavaliadas no servidor.
- Registrar criação, renovação, revogação e falha de sessão sem registrar o token; OWASP sugere correlação por hash salgado do identificador de sessão.[^owasp-session]

**Autorização**

- RBAC (`admin`, `operator`, `viewer`) combinado com ABAC: `site_id`, `camera_id`, categoria de dado, operação, horário/estado e finalidade.
- Negar por padrão e verificar permissão em toda requisição, inclusive download, thumbnail, export, WebSocket e endpoint de sync.[^owasp-authz]
- IDs opacos não substituem autorização.
- PostgreSQL RLS é defesa em profundidade. O role da aplicação não deve ser owner/superuser/BYPASSRLS; habilitar políticas e avaliar `FORCE ROW LEVEL SECURITY`. Sem política aplicável, o PostgreSQL usa default deny.[^postgres-rls]
- Separar roles de migração, runtime API, auditoria, backup e limpeza. Runtime não cria tabela/extensão nem altera política.

### 9.2 Identidade do dispositivo

- Dispositivo recebe UUID e certificado/chave exclusivos durante enrollment administrativo com token de bootstrap de uso único.
- Chave privada é não exportável no TPM/keystore quando possível; nunca é compartilhada entre máquinas.
- mTLS autentica o dispositivo e TLS protege transporte; token de dispositivo adicional pode representar escopos curtos, mas não substitui o certificado.
- Certificado possui expiração, rotação, revogação e estado (`pending`, `active`, `quarantined`, `revoked`).
- Dispositivo revogado não sincroniza, não recebe galeria e seus eventos ficam em quarentena para investigação.
- Heartbeat não aceita que o cliente declare seu próprio escopo; o servidor deriva site/câmeras do certificado/inventário.
- Diagnóstico remoto usa canal separado, opt-in temporário, aprovação, comando allowlisted e auditoria. Nunca executar shell arbitrário.

### 9.3 FastAPI, SQLAlchemy e PostgreSQL

- API atrás de proxy TLS configurado; confiar em `X-Forwarded-*` apenas de proxies conhecidos; HSTS no deployment web e CORS por allowlist exata, nunca `*` com credenciais.
- Desabilitar ou proteger documentação OpenAPI em produção conforme necessidade; ela não substitui inventário de endpoints.
- Modelos Pydantic com limites de tamanho, enum, formato e rejeição de campos inesperados em payloads sensíveis.
- Limitar corpo no proxy **e** na aplicação/stream; timeout, concorrência e rate limit por operação.
- SQLAlchemy Core/ORM com parâmetros vinculados. Nunca interpolar input em `text()`, nome de tabela, `ORDER BY` ou fragmento SQL; a documentação recomenda sempre bound parameters para dado não confiável.[^sqlalchemy-params]
- Transações explícitas para cadastro+template+consentimento, correção, promoção de desconhecido e aplicação de sync.
- Constraints e índices: UUID único, `(device_id,event_id)` único, sequência/versão, FKs, checks de status, dimensão/modelo de embedding e soft delete/tombstone coerentes.
- PostgreSQL acessível somente pela API/migração/backup em rede privada. Cliente edge nunca conecta diretamente ao banco.
- TLS PostgreSQL com validação de identidade (`sslmode=verify-full` quando libpq for usado); `prefer` é default de compatibilidade e não é apropriado para ambiente sensível.[^postgres-tls]
- Criptografar volume, WAL, réplica e backup; separar chave do dado; testar restauração e rotação.

### 9.4 Upload, importação e path traversal

O `UploadFile` do FastAPI facilita o recebimento multipart, mas autenticação, autorização, limites e validação do conteúdo continuam responsabilidade da aplicação.[^fastapi-upload]

Pipeline obrigatório:

1. Endpoint autenticado e autorizado para cadastro/importação; CSRF se cookie.
2. Limite de request no proxy e leitura streaming com contador; abortar antes de encher disco.
3. Quarentena em diretório/volume não executável, fora do webroot e sem exposição direta.
4. Ignorar `filename`, extensão e `Content-Type` do cliente para decisão de confiança.
5. Gerar nome/chave aleatório (UUID) e manter nome original somente se houver necessidade, sanitizado e separado.
6. Allowlist mínima de formatos raster realmente suportados; inicialmente JPEG e PNG. Rejeitar SVG, HTML, PDF, ZIP e formatos animados/multipágina.
7. Verificar assinatura/magic, decodificar com biblioteca mantida, limitar largura, altura, pixels totais, canais e frames antes de processamento pesado.
8. Reencodar em formato canônico, removendo EXIF/GPS, perfis e payloads extras; nunca apenas renomear extensão.
9. Scanner local/sandbox pode complementar, mas não enviar biometria a serviço público de análise.
10. Persistir objeto somente após validação; download por ID opaco com autorização, não por caminho fornecido.

Regra de filesystem:

- aplicação escolhe `base_dir` fixo e chave gerada;
- resolver/canonicalizar o destino e confirmar que permanece sob `base_dir` antes de abrir;
- criar arquivo novo sem seguir link e com permissão mínima;
- proibir caminho absoluto, `..`, separadores alternativos, nomes reservados do Windows, ADS (`:`), link simbólico/hardlink e dupla decodificação;
- não aceitar path em endpoint de download/exclusão; resolver ID no banco.

Casos de regressão: traversal Unix/Windows codificado e duplamente codificado, `%00`, ADS, nome reservado, symlink race, MIME/extensão divergentes, arquivo truncado, polyglot, imagem com pixels gigantes, muitos frames, EXIF/GPS e quota excedida.[^owasp-upload][^owasp-traversal]

### 9.5 RTSP, SSRF e segredos de câmera

**Modelo de configuração**

Persistir separadamente:

```text
scheme: rtsp | rtsps
host
port
path
username_secret_ref
password_secret_ref
expected_certificate_or_ca_ref
allowed_device_id
network_zone
```

- Não persistir `rtsp://usuario:senha@host/...` como string comum.
- Segredo fica no secret manager/keystore, com referência opaca no banco, acesso somente do worker da câmera, rotação e auditoria.[^owasp-secrets]
- UI mostra host/câmera, não senha; “revelar” deve ser evitado. Export e log sempre redigem userinfo, query, `Authorization` e token.
- Credencial única por câmera, sem reutilizar senha administrativa da câmera. Rotacionar após técnico desligado, perda de dispositivo ou suspeita.

**Proteção de rede/SSRF**

- Permitir apenas `rtsp`/`rtsps`; rejeitar `file`, `http`, `https`, `ftp`, `gopher`, UNC e esquema ausente.
- Parsear uma vez com biblioteca conhecida; rejeitar userinfo inesperado, Unicode ambíguo, host vazio, porta fora da allowlist e fragment/query não necessários.
- Câmera é cadastrada por inventário aprovado. Resolver A/AAAA, comparar todos os IPs à sub-rede da câmera e revalidar no momento da conexão para reduzir DNS rebinding.
- Bloquear loopback, link-local, multicast, broadcast, metadata de nuvem e redes internas que não sejam a zona de câmera explicitamente aprovada.
- Não seguir redirect para host/scheme diferente; idealmente não seguir redirect.
- Worker possui egress no firewall apenas para IP/porta da câmera e DNS/NTP necessários. A OWASP recomenda combinar validação de aplicação com restrição na camada de rede.[^owasp-ssrf]
- “Testar conexão” é job assíncrono autenticado, auditado, rate-limited, com timeout curto, limite de bytes/frames e resposta sanitizada. Nunca retorna frame ou banner a usuário sem permissão.
- Câmeras ficam em VLAN própria, sem acesso ao banco/KMS/rede administrativa; desabilitar P2P/cloud/UPnP não usados e manter firmware controlado.
- Preferir `rtsps` e validar certificado/hostname. O RFC 7826 diferencia `rtsp` inseguro de `rtsps` sobre TLS e alerta que autenticação HTTP isolada não fornece segurança completa.[^rfc-rtsp] Verificar separadamente o transporte da mídia: usar RTP intercalado no canal TLS ou SRTP/mecanismo equivalente quando suportado; `rtsps` pode proteger apenas o controle enquanto áudio/vídeo seguem por canal distinto.
- Quando câmera legada não oferece TLS, usar rede fisicamente/lógicamente isolada ou VPN entre zona de câmera e edge. Registrar que mídia e credencial podem continuar expostas dentro do segmento legado.

### 9.6 Isolamento, filas e disponibilidade

- Um worker/processo por câmera ou grupo controlado; falha/codec travado não derruba UI/API.
- Decoder e processamento de mídia em processo sem privilégio, sem shell, com diretório temporário próprio, limites de memória/CPU/arquivo e, quando disponível, sandbox do SO.
- Fila de frames tem tamanho pequeno e política explícita `drop_oldest`; o pipeline processa o frame mais recente.
- Fila de eventos é persistente, criptografada, limitada por bytes/idade e nunca contém frame por padrão.
- Circuit breaker e backoff com jitter para RTSP e servidor; reconexão não cria busy loop.
- Quotas separadas por câmera/dispositivo/usuário; health check não expõe segredo ou detalhes internos.
- Alerta de disco antes da quota crítica. Sob pressão: parar novas imagens, preservar evento mínimo/auditoria e sinalizar degradação.
- Encerramento limpa buffers, fecha stream, invalida material descriptografado em memória quando possível e confirma persistência transacional da fila.

### 9.7 Offline e sincronização

**Dados locais**

- Full-disk encryption é camada adicional, não substituta. Galeria e fila recebem criptografia por envelope com chave protegida no keystore/TPM/DPAPI/Keychain.
- SQLite puro não deve ser chamado de “criptografado”; escolher mecanismo real e validar licença/integração, ou criptografar payloads antes de persistir.
- Guardar somente galeria do escopo, eventos pendentes e tombstones; sem conta administrativa ou segredo humano no edge.
- Cache e manifesto possuem `not_before`, `expires_at`, versão, modelo, dimensão e escopo. Definir tempo máximo offline conforme risco.

**Eventos edge → central**

```text
event_id
device_id (derivado da identidade autenticada)
device_sequence
captured_at
monotonic_offset / clock_quality
event_type
schema_version
payload_minimo
payload_hash
created_with_gallery_version
created_with_model_version
```

- UUID/ULID e unique constraint `(device_id,event_id)` garantem idempotência; `device_sequence` detecta lacuna/replay, mas não deve descartar eventos válidos fora de ordem sem janela documentada.
- Servidor registra `received_at` próprio e não confia cegamente no relógio do edge.
- mTLS protege trânsito; assinatura do evento/manifesta melhora prova de origem, mas não impede falsificação se o próprio edge e sua chave forem comprometidos.
- Lote tem limite, transação e resposta por item. Ack só após commit; edge apaga payload local somente após ack e política de retenção.
- Reenvio do mesmo evento devolve o mesmo resultado e não refaz alerta.

**Servidor → edge**

- Pessoas/configurações são autoridade central. Evento de detecção é append-only; correção é novo registro vinculado, não reescrita silenciosa.
- Pacote de galeria/config possui manifesto assinado, hash de cada artefato, versão monotônica e escopo.
- Download em staging, verificação de assinatura/hash/versão, abertura controlada, transação local e troca atômica. Falha mantém versão anterior válida e gera alerta.
- Tombstone de pessoa/câmera/dispositivo tem precedência sobre versão anterior e nunca é revertido por backup/pacote atrasado.
- Revogação urgente reduz validade dos pacotes/chaves; não existe garantia de remote wipe enquanto o edge estiver desligado. Esse é risco residual explícito.
- Após offline máximo, escolher política aprovada: bloquear reconhecimento, operar somente com resultado local não acionável ou exigir reconexão. Não continuar indefinidamente com galeria vencida.

### 9.8 Reconhecimento, anti-spoofing e revisão humana

**Separação de estados**

```text
match_status: matched | unknown | ambiguous | error
pad_status: approved | rejected | inconclusive | disabled | error
decision_status: no_action | pending_review | confirmed | corrected | rejected
```

- `matched + approved` ainda não equivale a verdade; é evidência probabilística.
- Falha/timeout/modelo ausente produz `error` ou `inconclusive`, nunca `approved`.
- Desativação de PAD fica visível, auditada e não pode ser ocultada do decisor.

**PAD em camadas**

- cadastro controlado: desafio aleatório, mudança de pose, sequência temporal, qualidade e, se houver, sensor de profundidade;
- vigilância passiva: textura/reflexo/movimento e coerência temporal, sabendo que desempenho é inferior a desafio ativo;
- origem: câmera autorizada, canal protegido, detecção de frame congelado/loop, timestamp e sequência;
- processo: proteger ponto entre captura e modelo contra virtual camera, arquivo substituído e injeção IPC;
- modelo: versão assinada, threshold congelado por release e regressão com ataques de apresentação representativos.

O NIST observa que PAD mitiga apresentações, mas requer confiança adicional no sensor e no processamento; também recomenda comparação local porque um verificador central amplia o impacto de ataques.[^nist-63b] Para este projeto, os valores do NIST voltados a autenticação são referência de teste, não critério jurídico nem garantia universal para identificação 1:N.

**Acurácia e equidade**

- Calibrar threshold no cenário real por câmera, distância, iluminação, pose, tamanho de galeria e consequência; não usar score de biblioteca como “porcentagem de certeza”.
- Medir FMR/FNMR, precisão/recall de desconhecidos, taxa de ambíguos e erros de PAD; para 1:N, medir o sistema completo, não extrapolar apenas benchmark 1:1.
- Testar grupos e condições representativos de forma lícita e minimizada. Não coletar novo atributo sensível apenas para métrica sem avaliação de necessidade/base.
- NIST registra que iluminação/qualidade podem elevar falsos negativos e que falsos positivos variam entre grupos/algoritmos; por isso, validação local e monitoramento são obrigatórios.[^nist-demographics]
- Resultados ambíguos ficam como desconhecido/pending review. Nunca escolher o “melhor” candidato se nenhum supera o threshold e a margem mínima para o segundo candidato.
- Revisores veem contexto mínimo e duas etapas para ações críticas; correções alimentam avaliação, não treinamento automático silencioso.

### 9.9 Logs, auditoria e monitoramento

Registrar:

- login, logout, falha, lockout, recuperação, MFA e revogação;
- leitura e alteração de pessoa/câmera/configuração/permissão/retenção;
- cadastro, atualização, desativação, exclusão e propagação de tombstone;
- consulta e export sensível, com filtro, volume e justificativa;
- teste RTSP, rotação/revogação de segredo e diagnóstico remoto;
- sync, replay, lacuna, conflito, pacote inválido e galeria vencida;
- mudança de threshold/modelo/PAD e decisão/revisão humana;
- incidente, acesso de suporte, backup e restore.

Não registrar:

- senha, token, cookie, certificado privado, chave, pepper;
- URL RTSP completa, userinfo, header Authorization;
- imagem, embedding ou payload de upload;
- nome completo quando ID pseudônimo for suficiente;
- stack trace com dados do request em produção.

Controles:

- schema estruturado, encoding e neutralização de CR/LF para impedir log injection;
- timestamps UTC e monitoramento de clock skew;
- trilha append-only em sink separado, role de aplicação sem update/delete;
- hash encadeado/assinatura opcional detecta adulteração, mas não substitui ACL/backup;
- retenção e acesso próprios; alerta de leitura em massa e de tentativa de apagar auditoria;
- revisão periódica de usuários privilegiados e eventos de alto risco. A OWASP recomenda registrar falhas de validação, autenticação, autorização, sessão e ações de alto risco sem incluir segredos.[^owasp-logging]

### 9.10 Backup, incidente e continuidade

- Backup cifrado com chave separada da produção, credencial distinta, immutability quando apropriado e acesso dual para export/restauração em massa.
- Teste de restauração periódico em ambiente isolado, com reconciliação de tombstones e prova de que o serviço não abre antes da limpeza.
- RPO/RTO e responsáveis ainda precisam ser definidos; não afirmar recuperabilidade sem teste.
- Inventário permite identificar pessoas, dados, câmeras, dispositivos, objetos, backups e operadores afetados.
- Playbook cobre contenção, isolamento de edge/câmera, revogação de certificado/token/segredo, preservação de evidência, avaliação de risco aos titulares e comunicação.
- O controlador avalia comunicação sob a Resolução CD/ANPD nº 15/2024; operadores informam o controlador sem demora injustificada. A página oficial vigente indica, quando aplicável, prazo de três dias úteis para ANPD e titulares.[^anpd-incident]
- Manter registro de incidentes pelo prazo regulamentar vigente (a ANPD informa ao menos cinco anos no RCIS) e revisar o prazo antes da produção.[^anpd-incident-reg]
- Exercício de mesa deve incluir: banco/backup vazado, edge furtado offline, segredo RTSP exposto, falso positivo com dano, pacote de modelo comprometido e falha de eliminação.

### 9.11 Supply chain e ciclo de desenvolvimento

- Dependências com lock e hash; origem oficial; SBOM; política de atualização e EOL.
- Modelo ONNX, pesos, plugins e binários nativos tratados como artefatos executáveis: hash, assinatura/provenance, origem/licença e armazenamento imutável.
- Pipeline sem segredos longos; credenciais curtas/por ambiente; artefato promovido, não recompilado em produção.
- Gates planejados: testes, lint/type-check, SAST, SCA, detecção de segredo, análise de IaC/container e licença; suppressions com justificativa/revisor/expiração.
- ASVS 5.0.0 como catálogo de requisitos de verificação da API; usar nível 2 como baseline e selecionar requisitos de maior rigor para biometria, administração, export e dispositivos.[^owasp-asvs]
- NIST SSDF pode estruturar preparação, proteção do software, produção segura e resposta a vulnerabilidades.[^nist-ssdf]
- DAST, fuzzing, pentest e teste de câmeras reais somente em ambiente autorizado, alvo explícito e janela aprovada. **Nada disso foi executado nesta pesquisa.**

## 10. Plano de validação de segurança e privacidade

### 10.1 Testes automatizados mínimos

**Autenticação/autorização**

- matriz papel × ação × site × câmera × classe de dado;
- todo endpoint com testes sem token, token expirado, audience/issuer incorretos, usuário desativado e papel insuficiente;
- BOLA/IDOR trocando IDs, inclusive download, thumbnail, export e WebSocket;
- revogação de refresh/certificado e redução de privilégio.

**Uploads/filesystem**

- conjunto de regressão descrito na seção 9.4;
- quota concorrente, cleanup após erro e ausência de arquivo parcial público;
- propriedade: todo path resolvido permanece dentro da raiz autorizada;
- metadados removidos e formato canônico verificado.

**RTSP/SSRF**

- parser unitário com esquemas/hosts/IPv4/IPv6/Unicode/userinfo/portas inválidos;
- DNS que muda entre público/privado, loopback/link-local/metadata, redirect e timeout;
- worker não alcança DB/KMS/admin por teste de política de rede em ambiente controlado;
- redaction de URL/credencial em toda exceção e log.

**Sync/offline**

- duplicata, lote parcial, reorder, sequence gap, clock errado, conflito e reconexão;
- pacote adulterado, assinatura/hash inválido, downgrade e versão incompatível;
- exclusão enquanto edge está offline, restore de backup antigo e tombstone prioritário;
- quota/TTL e falha durante troca atômica.

**Biometria/PAD**

- positivos, negativos, ambíguos, nenhum rosto, múltiplos rostos e baixa qualidade;
- foto impressa, tela, vídeo e ataques de apresentação autorizados, sem alegar cobertura total;
- replay/injeção em harness simulado separado de PAD visual;
- métricas por câmera/condição e regressão por versão de modelo/threshold.

**Privacidade**

- inventário e registro de finalidade/base/retenção obrigatórios antes de ativar feature;
- export do titular sem dados de terceiros;
- eliminação atravessando DB, objeto, índice, cache e fila;
- restauração reaplica tombstones;
- logs/traces/crash dumps sem biometria ou segredo.

### 10.2 Critérios de aceite antes do piloto real

- [ ] Controlador, operadores, encarregado e contratos identificados.
- [ ] Finalidade e hipótese legal aprovadas por operação, inclusive desconhecidos/PAD.
- [ ] RIPD concluído e aprovado; versão pública avaliada quando pertinente.
- [ ] Avisos e canal de direitos ativos; processo de revisão humana treinado.
- [ ] Retenção e eliminação configuradas e testadas ponta a ponta.
- [ ] Upload/path traversal/SSRF cobertos por regressão.
- [ ] MFA para privilegiados; RBAC+ABAC e RLS testados negativamente.
- [ ] Segredos fora do código/log/banco em claro; rotação exercitada.
- [ ] TLS/mTLS e segmentação de câmera/DB/KMS verificadas.
- [ ] Cache/fila offline realmente criptografados e revogação/expiração documentadas.
- [ ] Threshold/PAD validados no hardware e ambiente alvo com conjunto autorizado.
- [ ] Nenhuma decisão de alto impacto é totalmente automatizada.
- [ ] Backup restaurado com sucesso e tombstones reaplicados.
- [ ] Playbook de incidente e responsáveis testados em exercício de mesa.
- [ ] Regulamentação ANPD e normas setoriais rechecadas na data do piloto.

## 11. Prioridades de implementação

### P0 — bloqueadores de qualquer dado biométrico real

1. Inventário de tratamento, definição do controlador/finalidades/hipóteses e RIPD.
2. Feature gates para fotos, desconhecidos, full frame, alertas externos e diagnóstico remoto.
3. Secret manager/keystore, criptografia por envelope e política de chave.
4. Autenticação, MFA privilegiado, RBAC+ABAC deny-by-default e identidade de dispositivo.
5. Upload canônico seguro, path por ID e proteção RTSP/SSRF/egress.
6. Retenção, tombstones, eliminação ponta a ponta e logs sem dados sensíveis.
7. Canal de direitos, revisão humana e política de decisão.

### P1 — antes do piloto distribuído

1. mTLS por dispositivo, enrollment/revogação e pacote de galeria assinado.
2. Fila local criptografada, idempotência, anti-replay, sync atômico e offline máximo.
3. Segmentação de câmeras e banco, PostgreSQL TLS `verify-full`, roles e RLS.
4. Métricas de reconhecimento/PAD e validação representativa no local autorizado.
5. Backup/restore com tombstone e playbook de incidente.
6. Gates de CI, SBOM, assinatura de modelo/artefato e ASVS 5.0.0.

### P2 — hardening contínuo

1. Auditoria separada e resistente a adulteração, alertas de abuso interno e revisão de privilégios.
2. KMS/HSM/TPM onde o risco justificar; credenciais dinâmicas e rotação automatizada.
3. Avaliação independente autorizada em staging e exercícios periódicos.
4. Recalibração por mudança de câmera, modelo, iluminação, galeria ou finalidade.
5. Revisão trimestral de retenção, operadores, integrações e atualização regulatória.

## 12. Risco residual e decisão de go-live

Mesmo com todos os controles, permanecem:

- **biometria não revogável:** troca de senha não corrige vazamento de característica facial;
- **endpoint comprometido:** o edge precisa descriptografar a galeria para reconhecer e pode expô-la durante uso;
- **PAD incompleto:** máscaras avançadas, deepfakes, injeção e sensor comprometido podem vencer controles;
- **erro e diferença de desempenho:** falsos positivos/negativos e variações entre grupos/ambientes não chegam a zero;
- **offline:** revogação e eliminação não alcançam imediatamente máquina desligada ou furtada;
- **RTSP legado:** VLAN/VPN reduz alcance, mas não torna câmera/protocolo inseguro intrinsecamente confiável;
- **insider:** acesso legítimo pode ser abusado, principalmente em export e administração;
- **backup:** eliminação física pode esperar expiração do backup, exigindo tombstone e restrição de restore;
- **mudança de finalidade:** capacidade técnica facilita function creep; governança e feature gate são indispensáveis;
- **incerteza jurídica/contextual:** base legal, proporcionalidade e regras setoriais dependem do uso real e podem mudar.

O go-live exige aceite formal desses riscos pelo responsável técnico, controlador, encarregado e, quando necessário, assessoria jurídica. Risco residual alto de falso reconhecimento, uso de desconhecidos, menor de idade ou ação adversa não pode ser aceito apenas por configuração de software; deve resultar em redução de escopo, alternativa menos intrusiva ou suspensão da função.

## 13. Evidência e limitações desta pesquisa

- Pesquisa baseada somente em documentação oficial/primária listada abaixo.
- Nenhum código, banco, rede, câmera, endpoint, pacote, imagem ou credencial foi analisado nesta etapa.
- Nenhum SAST, SCA, secret scan, DAST, fuzzing, pentest ou conexão RTSP foi executado.
- Os itens da matriz são ameaças de projeto, não vulnerabilidades confirmadas.
- Parâmetros de senha, token, threshold, retenção e offline precisam ser calibrados no ambiente e aprovados; números genéricos não foram transformados em política jurídica.
- A pesquisa deve ser atualizada ao escolher hospedagem, biblioteca biométrica, mecanismo de cache criptografado e topologia de produção.

## 14. Fontes oficiais e primárias

Todas as fontes foram consultadas em 2026-07-17.

[^lgpd]: Presidência da República — [Lei nº 13.709/2018 (LGPD), texto oficial](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).
[^anpd-faq]: ANPD — [Perguntas frequentes: conceito de dado pessoal sensível](https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes/perguntas-frequentes).
[^anpd-ripd]: ANPD — [Relatório de Impacto à Proteção de Dados Pessoais (RIPD): perguntas e respostas](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd).
[^anpd-agenda]: ANPD — [Agenda Regulatória 2025–2026](https://www.gov.br/anpd/pt-br/assuntos/processo_regulatorio/agenda-regulatoria-1/agenda-regulatoria-2025-2026) e [tomada de subsídios sobre dados biométricos](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-abre-tomada-de-subsidios-sobre-tratamento-de-dados-biometricos).
[^anpd-regulations]: ANPD — [Regulamentações da ANPD e status atual](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd).
[^anpd-rights]: ANPD — [Direitos dos titulares](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados-1/direito-dos-titulares).
[^anpd-children]: ANPD — [Enunciado sobre tratamento de dados pessoais de crianças e adolescentes](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes).
[^anpd-incident]: ANPD — [Comunicação de Incidente de Segurança: procedimento, critérios e prazos](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis).
[^anpd-incident-reg]: ANPD — [Resolução CD/ANPD nº 15/2024 e resumo do Regulamento de Comunicação de Incidente de Segurança](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-aprova-o-regulamento-de-comunicacao-de-incidente-de-seguranca).
[^owasp-upload]: OWASP — [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
[^owasp-traversal]: OWASP — [Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal).
[^owasp-ssrf]: OWASP — [Server-Side Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).
[^owasp-secrets]: OWASP — [Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).
[^owasp-password]: OWASP — [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
[^owasp-authz]: OWASP — [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).
[^owasp-session]: OWASP — [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
[^owasp-logging]: OWASP — [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).
[^owasp-asvs]: OWASP — [Application Security Verification Standard, versão estável 5.0.0](https://owasp.org/www-project-application-security-verification-standard/).
[^nist-63b]: NIST — [SP 800-63B, Digital Identity Guidelines: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html), especialmente requisitos e limitações de biometria/PAD.
[^nist-demographics]: NIST — [Face Recognition Technology Evaluation: Demographic Effects](https://pages.nist.gov/frvt/html/frvt_demographics.html).
[^nist-ssdf]: NIST — [SP 800-218, Secure Software Development Framework 1.1](https://csrc.nist.gov/pubs/sp/800/218/final).
[^fastapi-auth]: FastAPI — [OAuth2 com senha, hashing e JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).
[^fastapi-upload]: FastAPI — [Request Files / `UploadFile`](https://fastapi.tiangolo.com/tutorial/request-files/).
[^sqlalchemy-params]: SQLAlchemy — [Working with Transactions and the DBAPI: bound parameters](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html#sending-parameters).
[^postgres-tls]: PostgreSQL — [libpq SSL Support e `sslmode=verify-full`](https://www.postgresql.org/docs/current/libpq-ssl.html).
[^postgres-rls]: PostgreSQL — [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) e [`CREATE POLICY`](https://www.postgresql.org/docs/current/sql-createpolicy.html).
[^rfc-rtsp]: IETF/RFC Editor — [RFC 7826, Real-Time Streaming Protocol Version 2.0](https://www.rfc-editor.org/info/rfc7826/), seções 19 e 21 sobre TLS, autenticação e segurança.
