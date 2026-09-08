# Configuração Supabase (DB-01)

Estado em 08/09/2026: projeto remoto existente conferido pelo painel autenticado do
Supabase; UUID real da organização preenchido em `dashboard/.env.local`. Foi confirmado
um vínculo de administrador e a conta Auth com e-mail confirmado. Não houve criação de
organizações, reaplicação de bootstrap/migração, alteração de permissões ou gravação de
dados de negócio nesta conferência.

A consulta de leitura confirmou as oito tabelas esperadas com RLS, bloqueio de SELECT
para anon, concessão de SELECT para authenticated e as duas funções públicas esperadas.
Configuração local validada, build e 51 testes aprovados no Conda smart-environment,
e servidor local respondendo HTTP 200. **O primeiro login e a persistência pelo dashboard
com uma sessão real ainda precisam ser validados.** Os testes automatizados usam PGlite
e requisições simuladas do SDK; não substituem essa validação de Auth/PostgREST/JWT/CORS.

## O que já está ligado no código

- Login com e-mail/senha pelo Supabase Auth quando configurado; renovação e saída da
  sessão pelo SDK. O acesso local anterior continua só em localhost/127.0.0.1 quando
  todas as variáveis estão vazias. Ele **não autentica uma conta** nem libera o banco.
  Configuração parcial/inválida bloqueia o acesso, sem cair no modo local.
- Ambientes independentes, inclusive vazios; criação e edição de nome.
- Cadastro e edição de webcam, MJPEG e RTSP: ambiente por UUID, nome, endereço sem
  credenciais, habilitação e identificador opcional do monitor (`pc`/`phone`). Uma
  resposta nova do monitor não substitui os nomes e vínculos persistidos.
- Regras de indisponibilidade/ocupação fora do horário, com edição e habilitação.
- Histórico paginado (50 registros), filtros de ambiente/período, atualização explícita
  e exportação **da página consultada** em CSV; não é exportação integral de todo o banco.
- Indicadores e CSV por câmera/ambiente: minutos ocupados, vazios, desconhecidos e pico.
  Não somam pessoas de câmeras sobrepostas. Não inferem energia, emoções ou produtividade.
- Detalhes de alertas e transição humana `aberto → revisado → resolvido`; conflito de
  versão exige recarregar. Revisão e resolução preservam autoria/horário separados.
- Datas atuais e consultas no fuso de Brasília. O fuso está fixado também na organização;
  suporte a outras regiões será um incremento próprio.

Sem configuração remota, formulários continuam acessíveis, mas não salvam e mostram
o motivo. Depois da ativação, administradores salvam; visualizadores consultam. Não há
persistência de cadastro escondida em localStorage. Não há gestão/exclusão de usuários,
recuperação de senha, exclusão de câmeras ou política de retenção implementadas nesta UI.

## Ativação em um projeto novo

O projeto atual já tem organização e administrador: **não repita os passos de criação
ou bootstrap nele**. A sequência abaixo serve para um projeto realmente novo. Ao trocar
apenas de computador, configure o arquivo local com os dados da organização existente.

1. Crie seu projeto Supabase, escolhendo região/plano conforme orçamento e requisitos
   de dados. Não é necessário fazer isso para compilar ou testar agora.
2. No SQL Editor do projeto novo, execute **uma vez** o conteúdo de
   `supabase/migrations/202609060001_smart_environment.sql`. Não execute sobre tabelas
   homônimas existentes sem revisão: a migração inicial não é um script de atualização
   destrutiva nem foi desenhada para ser reaplicada.
3. Crie e confirme sua primeira conta em Authentication. Não publique senhas no código.
   Desabilite o cadastro público se não quiser inscrições abertas. Uma conta sem vínculo
   em `organization_members` não lê os dados da organização.
4. Abra `supabase/bootstrap.sql.example`, substitua apenas o e-mail pela conta criada e
   execute o conteúdo no SQL Editor. Guarde o UUID da organização emitido. O script
   recusa usuário já vinculado para evitar organizações duplicadas por reexecução.
5. Copie `dashboard/.env.example` para `dashboard/.env.local` e preencha:

   ```dotenv
   VITE_SUPABASE_URL=https://SEU_PROJETO.supabase.co
   VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_SUA_CHAVE_PUBLICAVEL
   VITE_ORGANIZATION_ID=UUID_DA_ORGANIZACAO
   ```

   Esta versão usa a chave **publicável nova** (`sb_publishable_`), não a chave secreta
   nem chaves JWT legadas. Variáveis VITE são incorporadas ao frontend e são públicas.
   Nunca coloque `service_role`, `sb_secret_`, senha de banco/câmera ou token privado nelas.
   `.env.local` é ignorado pelo Git; não precisa enviar as chaves pelo chat.
6. Reinicie o servidor de desenvolvimento ou refaça o build para aplicar as variáveis:

   ```powershell
   conda activate smart-environment
   cd C:\Users\angel\OneDrive\Documents\Multicam\dashboard
   npm.cmd ci
   npm.cmd run dev -- --hostname localhost
   ```

7. Entre com a conta real, crie um ambiente vazio, cadastre a câmera, recarregue e confirme
   a persistência. Edite-a em duas abas: a segunda gravação desatualizada deve pedir
   atualização. Teste também usuário viewer, não membro e outra organização.
8. Para uma segunda conta, crie-a no Auth e associe seu UUID a `organization_members`
   como `viewer` ou `admin`, exclusivamente pelo SQL Editor de um responsável. Nunca
   determine a permissão por metadados que o próprio usuário possa editar.

O cadastro salva configuração, **não abre uma câmera, instala o gateway nem altera
automaticamente o monitor Python**. O player de transmissão continua o ST-01 local de
uma fonte; não virou um gerenciador remoto de quatro streams nesta etapa.

## Contrato do banco e do futuro servidor Ubuntu

`organizations` e `organization_members` definem o isolamento. `environments`, `cameras`
e `alert_rules` são os cadastros. `occupancy_samples` contém somente metadados agregados;
`alerts` guarda ocorrências; `audit_events` registra autoria e ações, somente para admins.
Não há tabelas de rostos, identidade, fotos, vídeo ou embeddings.

RLS verifica a organização real da sessão. Anônimos não têm acesso às tabelas. Contas
autenticadas não podem se promover, fabricar leituras/alertas, alterar auditoria ou apagar
histórico. O frontend também filtra por organização, mas isso não substitui a RLS. O SDK
mantém tokens de sessão no navegador; isso exige cuidado com XSS e dispositivo compartilhado.
A associação é revalidada ao recuperar foco/conexão e a cada 60 s em aba visível; revogação
bloqueia novas consultas imediatamente no banco, mas não apaga dados já exportados.

A futura ingestão deve rodar **apenas no servidor**, com segredo fora do dashboard/Git,
associando o dispositivo autorizado à organização; não aceitar `organization_id` arbitrário
de um cliente. Chaves privilegiadas ignoram RLS, então essa checagem é responsabilidade
do serviço. O navegador não envia observações. O envio, armazenamento durável offline,
retry, geração automática de alertas e integração do monitor **ainda não foram feitos**.

Cada amostra é um bucket UTC de um minuto completo, único por câmera/minuto, com:

- `occupied`: contagem maior que zero;
- `empty`: contagem zero confirmada;
- `unknown`: contagem nula quando não há leitura confiável.

O servidor deverá definir uma regra de agregação consistente (por exemplo, pico no minuto)
e só enviar buckets encerrados. Ausência de amostra não vira vazio. SQL e histórico
excluem minutos parciais do recorte. Os gatilhos verificam câmera/regra no ambiente atual
ao inserir e preservam o ambiente histórico se a câmera for movida; envio atrasado de uma
atribuição anterior exige modelar vigências antes, não contornar o gatilho.

Relatórios aceitam até 31 dias; a UI oferece hoje, 7 e 30 dias. Catálogos e relatórios
recusam respostas de 500 linhas para não apresentar truncamento silencioso. Preserve
o limite padrão de linhas do projeto (pelo menos 500). O histórico usa paginação por
offset e mantém o fim do recorte durante a navegação; backfills concorrentes podem mudar
posições. Recarregue após ingestão tardia. Exportação contábil exata de um grande histórico
exigirá snapshot/paginação por cursor no servidor.

## Validação local e pendências

Atualização SEC-01 posterior: dependências corrigidas onde há versão disponível;
audit reduziu de 19 para **2 entradas altas residuais** (image-size/Vinext), e o
dashboard passou em 51 testes. Não houve supressão dos avisos nem aprovação de produção.
Consulte [hardening de dependências](dependency-hardening.md) para os riscos e controles.
Os números abaixo registram o checkpoint DB-01 anterior à atualização.

Resultado da rodada de 07/09/2026: **48 testes do dashboard**, **127 testes Python e
11 subtestes**, build, ESLint e TypeScript global aprovados, todos no Conda
`smart-environment`. A auditoria completa registrou 19 avisos preexistentes no framework
e ferramentas (16 altos, 1 moderado, 2 baixos); correção e novo audit são pré-requisitos
para exposição em rede/publicação, inclusive para pacotes marcados como devDependencies
que entram no servidor. Não houve atualização forçada de dependências.

```powershell
conda run -n smart-environment npm.cmd --prefix dashboard test
conda run -n smart-environment npm.cmd --prefix dashboard run lint
# Dentro de dashboard:
conda run -n smart-environment npx.cmd tsc --noEmit
```

`tests/database.test.mjs` aplica a migração em PostgreSQL/PGlite e assume explicitamente
os papéis authenticated/anon/service_role, com duas organizações. Verifica RLS, grants,
FKs, estados, duplicidade de buckets, conflitos de versão, revisão e revogação. O teste
do SDK intercepta fetch, sem rede, e verifica payloads/escopo/paginação. Os dados de teste
são sintéticos, transitórios e não entram no projeto remoto.

A estrutura do projeto remoto foi conferida por leitura em 08/09/2026. A validação
de login, sessão e gravação real pelo dashboard continua pendente; não confundir a sessão
administrativa do painel Supabase com uma sessão da aplicação. Não houve deploy, abertura
de câmeras, treinamento nem alteração das fotos. Antes de exposição pela internet:
revisar hospedagem, HTTPS, CSP, criação de contas,
retenção, backup/restore, limites de requisições, dependências e autorização do gateway.

Referências: [RLS do Supabase](https://supabase.com/docs/guides/database/postgres/row-level-security),
[Auth por senha](https://supabase.com/docs/reference/javascript/auth-signinwithpassword),
[eventos de sessão](https://supabase.com/docs/reference/javascript/auth-onauthstatechange),
[PGlite](https://pglite.dev/docs/).
