# Histórico de versões — Smart Environment

Este arquivo registra marcos nomeados do código. O histórico técnico anterior está
em `.planning/CHANGELOG.md`; o estado e as pendências estão em `.planning/STATE.md`.
O processo para preservar e publicar versões está em [docs/versioning.md](docs/versioning.md).

## v0.1.0 — preparado, não publicado

Preparação registrada em 08/09/2026. Não há tag ou GitHub Release criada por esta
entrega. A tag proposta deverá apontar para um novo commit depois da revisão final.

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
