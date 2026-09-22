# Histórico de versões — Smart Environment

Este arquivo registra marcos nomeados do código. O histórico técnico anterior está
em `.planning/CHANGELOG.md`; o estado e as pendências estão em `.planning/STATE.md`.
O processo para preservar e publicar versões está em [docs/versioning.md](docs/versioning.md).

## 0.3.0a1 — migração Django (20/09/2026, local/não publicada)

- Aplicação principal Django com templates HTML/CSS e JavaScript puro, sem build npm.
- Login Supabase, sessões server-side, refresh/logout, CSRF, limite de tentativas,
  permissões e vínculo existente; nenhuma duplicação de organização ou conta.
- Visão geral, perfil, câmeras/ambientes e seus detalhes, cadastros com controle de
  versão, regras, alertas revisáveis, histórico, indicadores por câmera e CSV.
- WebRTC/WHEP via sinalização same-origin, mídia separada da inferência, conexão
  manual, caixas transitórias e estados desconhecidos em falhas. Ponte local opt-in.
- Logos preservadas, relógio Brasília, menu responsivo e UUID para configurar câmeras.
- Configuração privada e SQLite local de sessões preparados nesta máquina; nenhum
  banco remoto, câmera, foto, modelo ou VM alterado por esta migração.
- Guia novo PC/VM, ambiente web Conda, Waitress/Caddy e CI principal Django. Legado
  preservado com workflow manual; vulnerabilidades antigas não declaradas resolvidas.
- 714 testes Python + 478 subtestes e 17 testes JS aprovados; QA sintético no navegador,
  não validação de autenticação/ingestão/vídeo reais ou instalação Linux.
- Tag candidata **v0.3.0-alpha.1**: revisar o snapshot e consultar tags remotas antes
  de criar. Nenhum commit/tag/push executado; v0.1.0/v0.2.0 não foram movidas.

## Histórico não publicado — DJ-01 / fundação Django (19/09/2026)

- Destino confirmado: Django + templates HTML/CSS/JavaScript puro, sem TypeScript.
- Estrutura web em `app/web/`, `manage.py` e Django 5.2.17 no extra opcional `web`.
- Tela de entrada com as logos/cores existentes; sem login simulado ou coleta de
  credenciais. Autenticação, cadastros, streaming e relatórios aguardam migração.
- Rotas somente GET/HEAD, CSP sem rede/form-action, health limitado a liveness.
- Novo runtime não usa npm/Node/TypeScript; legado `dashboard/` preservado até paridade.
- Ambiente Conda/CI e guia atualizados, sem banco/câmera/VM, bootstrap ou publicação.
- Testes e QA locais registrados em `.planning/phases/se-13-django-migration/VERIFICATION.md`.
  Nenhuma nova tag criada. Configuração de desenvolvimento não deve ser exposta.

## Não publicado — avaliação pública de estação (15/09/2026)

- Incremento de 16/09: editor HTML offline de caixas e rascunhos, fontes/relatórios
  vinculados por hash e comparação TP/FP/FN/precision/recall/F1 a IoU 0,50, somente
  após revisão explícita. Sem anotações humanas produzidas, treino ou mudança ao vivo.
  547 testes Python + 252 subtestes e 54 testes Node; QA visual/browser pendente.
- Letterbox opt-in com proporções preservadas e inversão de retângulos; default
  stretch mantido nas câmeras. Pesos Intel/OpenVINO permanecem os mesmos.
- Seis referências Commons com licença/autoria/hash e download explícito limitado.
- Evidência geométrica conservadora e comparação offline reproduzível com prévias,
  créditos e testes; não é classificador de produtividade nem treinamento concluído.
- Continuidade em AGENTS.md e docs/workstation-evaluation.md.
- Etapa 5: modo offline opcional de detalhe com até cinco inferências, consolidação
  por classe e preservação de pessoas do quadro inteiro; duas referências amplas
  adicionais, comparação visual e testes. Ganhos pontuais com falsos positivos e
  custo aproximado 5,1x; candidato não promovido, pesos e câmeras inalterados.

Estado local: tags v0.1.0 e v0.2.0 já apontam para f5b1f18. Elas não representam
automaticamente as mudanças posteriores ainda no worktree. Não mover ou recriar.

## Incremento de 09/09/2026 — pendente de marco correspondente

Nota de 15/09: o nome v0.2.0 proposto originalmente abaixo já existe, apontando para
o commit anterior f5b1f18. Preservar essa tag e escolher outro nome ao publicar.

Incremento local de 09/09/2026. Preserva `v0.1.0` e prepara a operação sem acesso à
VM. Manifests Python/dashboard e lock atualizados; nenhuma publicação automática.

- Captura com `readinto`, slot bruto e consulta de sequência antes da cópia; regressões
  de propriedade do buffer, frames parciais, falta de sinal e revogação preservadas.
- Fechamento periódico de minutos a 1 Hz, mais fechamento final no shutdown, sem
  adiar persistência das observações e sem transformar lacunas em ocupação zero.
- Polls web serializados, pausa em aba oculta, timeout/backoff, reconciliação de
  leituras idênticas e expiração independente de requisições lentas.
- Vídeo remoto preservado em falhas transitórias de telemetria; leituras/retângulos
  vencidos são removidos. Recusa de acesso continua retirando o player.
- JPEGs locais com uma busca/decodificação por vez e descarte de blobs transitórios.
- CLI offline de backup, verificação e restore da outbox completa, incluindo WAL;
  destino novo protegido, sem sobrescrita nem ativação automática de restauração.
- Workflow GitHub Actions com Conda isolado, testes, lint/tipos e audit completo;
  SHAs das actions fixados. Preparado, ainda não executado no GitHub.
- Benchmark sintético reproduzível e guias de operação/versionamento atualizados.

Validação final Windows/Conda: **399 testes Python + 11 subtestes**, incluindo 42 de
backup sem skips; **build + 66 testes do dashboard**; TypeScript, ESLint, Ruff e Mypy
(10 módulos de servidor) aprovados. Árvore npm válida, YAML CI/perfil parseado com
invariantes básicos verificados. Instalação limpa/CI Linux ainda não executadas.

Audit completo em 09/09: **2 altas residuais image-size/vinext**, sem supressão.
O build passou pelo comando nativo do projeto após falha no shim npm do auxiliar
Sites/Windows. Pytest usou pasta temporária nova; saída Node precisou de
`conda run --no-capture-output` para evitar erro de codificação do wrapper.

Microbenchmark repetido: 0,716041 → 0,397766 ms/montagem e 1.405.787 → 692.353 bytes
de pico Python, em 640×360/chunks 4 KiB. Não mede FPS real, codec, inferência, navegador ou VM.
Ver [desempenho e aceite](docs/performance-and-readiness.md).

## v0.1.0 — tag local existente; publicação remota não verificada

Preparação registrada em 08/09/2026. Em 09/09/2026, HEAD local `f5b1f18` e tag
`v0.1.0` foram encontrados, criados pelo usuário. Nenhuma tag foi movida ou recriada.
Não foi verificada publicação remota ou GitHub Release nesta rodada.

### Conteúdo do marco

- Dashboard com identidade visual, login Supabase, permissões por organização,
  ambientes, cadastro de câmeras, regras, histórico, relatórios e revisão de alertas.
- Processamento Ubuntu/Hyper-V sem GPU: modelo Intel/OpenVINO compartilhado por
  até quatro câmeras, slot de quadro mais recente e frequência de análise configurável.
- Vídeo MediaMTX/WebRTC separado da IA, acesso autenticado no dashboard e caixas
  recentes com expiração; modo local anterior preservado quando o servidor não está configurado.
- Minutos de ocupação e alertas persistidos em fila SQLite, com tentativas posteriores,
  deduplicação e preservação de erros permanentes; sem gravação dos quadros pela análise.
- Perfil Conda do servidor, exemplos de serviços e rede privada, guia de instalação
  e procedimento de versionamento sem sobrescrever marcos anteriores.
- Diagnóstico `--preflight` em texto/JSON sem rede/câmera/execução de vídeo, com checagens
  de instalação e mensagens sanitizadas; erros de configuração e início tratados sem traceback.
- Backlog reconciliado com o código atual, separando testes locais do aceite na VM.
- sharp atualizado para 0.35.4 por override delimitado ao Miniflare instalado, com
  testes de versões nativas, formatos de imagem e compatibilidade do binding Images.

### Evidência e limites

- Revalidação de 08/09/2026 após OPS-01: 341 testes Python e 11 subtestes; build e
  60 testes do dashboard; Ruff e Mypy dos módulos do servidor aprovados. O marco
  anterior SRV-01 tinha 322 testes Python. Nenhum commit foi criado nesta rodada.
- Preflight executado no Conda Windows: dependências e artefatos encontrados,
  configuração remota não verificada. Não foram abertas câmeras ou conexões de vídeo.
- Modelo CPU carregado e inferência sintética em memória concluída no checkpoint;
  isso não comprova precisão do detector nem desempenho das câmeras físicas.
- Instalação na VM, configuração de TLS/firewall, ingestão real, recuperação operacional
  e transmissão simultânea 720p/30 FPS ainda precisam de aceite no ambiente de destino.
- Audit completo após correção de sharp: 2 entradas altas residuais image-size/vinext,
  contra 6 no baseline. Gate de segurança não aprovado; ver `docs/dependency-hardening.md`.
  Este marco interno não autoriza exposição pública. Treinamento com fotos permanece pausado.

Nenhuma versão anterior foi inventada ou renomeada retroativamente. Novas correções
e funcionalidades terão suas próprias entradas e tags após revisão e validação.
