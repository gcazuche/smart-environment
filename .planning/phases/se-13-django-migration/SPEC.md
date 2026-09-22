# SE-13 — migração web para Django

Data: 2026-09-19. Decisão confirmada: Django + templates HTML/CSS/JavaScript puro,
sem TypeScript no destino. Repositório local, Windows, Conda smart-environment.
Segurança/compliance: unspecified; sem autorização para DAST ou implantação.

## Ampliação autorizada em 20/09/2026

Pedido: terminar a transição. Executar DJ-02 a DJ-06 localmente: autenticação
Supabase existente, sessão DB server-side (cookie só identificador), views/templates
SSR, formulários e concorrência, consultas/CSV e WHEP via proxy same-origin apenas
para sinalização/telemetria. Mídia não passa pelo Django. Sem login fictício.
Credenciais carregadas somente no servidor; produção exige chave persistente,
HTTPS/hosts explícitos. Sessões e limitação de login usam SQLite local isolado de
cadastros Supabase; migrações Django nunca alteram tabelas/organizações remotas.
Inicialmente um processo web com threads e lock de refresh por sessão; expansão
multiprocesso requer coordenação distribuída, não ligar múltiplos workers.

Aceite: funções do legado portadas ou diferenças explicitamente registradas,
testes positivos/negativos offline, CSRF/isolamento/papéis/expiração/conflito, browser
com dados sintéticos identificados sem remoto, guia novo PC/VM e CI Django principal.
Não remover arquivos de trabalho do usuário: legado preservado, mas aposentado do
fluxo principal. Não executar login/cadastros remotos, câmeras, treino, implantação,
commit/tag/push. Aceite de hardware/Supabase real é distinto do código pronto.

## Escopo e arquitetura

Migrar incrementalmente a interface existente sem redesenhar a marca nem apagar
`dashboard/` durante a transição. Django é um framework Python, não uma linguagem
substituta de TypeScript: os componentes React serão convertidos em templates e
interações JavaScript. Supabase, organizações, papéis, banco e processamento Python
serão preservados. Não repetir bootstrap nem criar uma segunda base de usuários.

- Novo código em `app/web/`, entrada `manage.py`, dependência opcional `web`.
- Templates, CSS, JS e as duas logos fornecidas pelo usuário, sem build Node.
- URLs reais para as seções no destino; hoje tudo está em uma SPA na rota `/`.
- MediaMTX/gateway continuam entregando vídeo; Django não decodifica frames nas views.
- Inferência permanece fora do servidor web. Migração não promete aumento de FPS.

## DJ-01 — escopo histórico de 19/09 (superado pela ampliação acima)

Somente fundação executável e tela de entrada visual. Campos de acesso desabilitados,
nenhuma senha coletada, nenhum login simulado, sem sessão ou conexão a Supabase.
`/` redireciona a `/login/`; `/health/` confirma somente o processo web, declarando
que autenticação/dados não estão conectados. Não existem rotas de painel nesta etapa.
Configuração estritamente de desenvolvimento em loopback; não liberar na VM/internet.

Critérios de aceite:

1. Rodar no ambiente Conda existente, sem `.venv`, npm, TypeScript ou modelos de IA.
2. Preservar cores, logos e composição do login atual, responsivo e acessível.
3. Templates autoescaped, assets locais, sem chamadas externas, banco ou upload.
4. Recusar POST/entradas de login; não aceitar uma credencial apenas para simulação.
5. Testes de rotas, renderização, ausência de coleta, headers e empacotamento de assets.
6. Registrar evidências, limites, comandos e próxima etapa. Não alterar detector,
   dados privados, `.env.local`, banco, VM, câmera, commits ou tags.

## Plano e arquivos

| ID | Prioridade/tipo/risco | Dependência | Arquivos e resultado | Validação/segurança |
|---|---|---|---|---|
| DJ-01 | P1 / fundação / baixo | decisão de stack | manage.py, app/web, manifests, testes e guia; login visual sem acesso | testes/check/build; sem coleta ou rede |
| DJ-02 | P0 / autenticação / alto | DJ-01 | serviços de sessão Supabase, views/forms, settings; mesmos usuários e organização | falha fechada, papéis, CSRF, logout, expiração/refresh, rate limit; sem service-role no cliente |
| DJ-03 | P1 / navegação/leitura / médio | DJ-02 | templates/views de overview, câmeras, ambientes/detalhes, perfil | URLs reais, todas as câmeras do ambiente, escopo por organização, desconhecido não vira zero |
| DJ-04 | P1 / cadastros / alto | DJ-03 | forms/serviços de câmera, ambiente e regras | admin/viewer, validação, concorrência por version, erros sem salvar fictício |
| DJ-05 | P1 / streaming / alto | DJ-02/03 | receptor WHEP/JS, polling e overlay | preserve 401/403, expiração, cleanup, origins exatas, pausa em aba oculta; medir hardware separadamente |
| DJ-06 | P1 / relatórios e corte / alto | DJ-03/04/05 | indicadores/histórico/alertas/CSV, deploy/CI/docs | paridade, filtros/paginação, acessibilidade, segurança, versão revisável; só então retirar legado |

DJ-02 deve decidir armazenamento server-side de sessão, renovação e ponte segura para
o gateway antes de implementar forms. Não armazenar refresh tokens em cookies Django
apenas assinados (não criptografados). Não contornar RLS com service-role. Endpoint
Supabase/origins fixos por configuração, nunca aceitos de campos arbitrários do cliente.

## Invariantes a conservar

- Papéis admin/viewer, isolamento por organização e controle de versão dos cadastros.
- Ausência/falha/ambiguidade continua desconhecida; presença não prova produtividade.
- Relógio Brasília, exportação UTC e escopo real da página consultada no CSV.
- WHEP: bearer, validação de origem, timeout, renovação/DELETE e limpeza do player.
- Telemetria indisponível expira caixas sem reiniciar vídeo; 401/403 remove transmissão.
- Consultas sem sobreposição, suspensas em aba oculta; sem retenção desnecessária.
- Porta atual 3000 e allowlists do monitor/gateway: não trocar por 8000 sem revisão.
  DJ-01 usa 8000 isoladamente porque não conecta nenhuma câmera/gateway.

## Ameaças e limites históricos de DJ-01

Ativos: credenciais, sessões, vínculos de organização, câmera e relatórios. Fronteiras:
navegador → Django → Supabase e navegador → gateway/vídeo. Entradas deste incremento:
GET/HEAD e arquivos estáticos, sem upload, CRUD, processamento, modelos ou banco.
Controles: loopback, ALLOWED_HOSTS restrito, CSP sem inline/conexões/form-action,
CSRF/SecurityMiddleware/clickjacking, não coletar credenciais, health sem configuração.
Configuração local com DEBUG e chave efêmera não serve para produção/sessões reais.
TLS, sessão persistente, limite de tentativas e deploy seguro pertencem às próximas etapas.

Rollback: parar o novo processo e continuar no painel legado intocado. Não há migrações
de dados nem remoções a reverter. Remover TypeScript do repositório antes da paridade
apagaria funções ainda não migradas e não faz parte de DJ-01.

## Encerramento de código em 20/09 — DJ-02 a DJ-06

Implementados os seis itens da tabela. Django é o runtime principal, sem TypeScript;
legado permanece recuperável e separado. As afirmações acima sobre ausência de
sessão, CSP sem POST e proibição de migrate descrevem somente DJ-01, não o atual.

Fronteiras atuais: navegador → Django (sessão/CSRF), Django → Supabase (chave
publicável + token do usuário, RLS), Django → gateway (sinalização/telemetria),
navegador → MediaMTX (WebRTC). A ponte JPEG é opt-in e exclusivamente loopback.
Entradas: formulários limitados, UUIDs, versão, período, SDP e caminho de sessão
validado. Sem upload/decodificação/treinamento nas views e sem segredo no browser.

Controles: sessões no servidor, limites persistentes de tentativas, locks por sessão
num único processo, validação de permissão/organização/versão, CSRF e rotação,
Referrer-Policy same-origin (no-referrer quebra POST), origins remotas fixas, TLS
validado, limites de corpo/tempo/leitura, CSP same-origin, cookies seguros em produção.

Rollback web: parar o processo Django e escolher conscientemente o legado preservado,
considerando seus riscos conhecidos; não excluir bancos/credenciais. Nenhuma migração
remota foi feita. DB local de sessões só deve ser manipulado com backup e escopo claros.
Aceite remoto, Linux e hardware não substituído pelos testes offline; consultar
COMPLETION-VERIFICATION.md antes de publicar/implantar.
