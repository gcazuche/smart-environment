# UI-02 — controles e relógio do dashboard

Checkpoint histórico: 2026-09-04. **Superado parcialmente por DB-01 em 06/09/2026**:
cadastros, autenticação, RLS, consultas e revisão agora estão implementados e preparados
para ativação posterior. Consulte [estado e instruções atuais](supabase-setup.md).
As descrições abaixo registram os limites da entrega de 04/09, não o código atual.
O trabalho permanece local, seguindo o contexto ST-01. Não houve deploy nem mudança
de acesso do site publicado.

## Implementado

- Relógio pt-BR com fuso `America/Sao_Paulo`, atualizado a cada segundo, inclusive
  após a aba voltar ao primeiro plano. Formata dia da semana, dia, mês, ano e hora.
  O relógio é um componente isolado e não remonta o player de vídeo.
- Adicionar câmera (nos dois modos), editar configurações, novo ambiente e criar outro
  ambiente abrem diálogos de formulário. Escolha de origem muda campos e validações.
- Validação de nomes, nomes de ambiente duplicados, índice de webcam e protocolos
  HTTP(S)/RTSP. Endereço RTSP precisa de servidor. Senhas/tokens embutidos são recusados.
  Validação de formato **não** comprova conectividade ou autorização da origem.
- Cancelar, fechar, Escape e restauração de foco usam diálogo modal nativo.
- Histórico tem página, seleção de ambiente e período; indicadores também têm período.
  A seleção muda o intervalo, mas ainda não faz consulta remota.
- Configurar regras abre o estado de integração pendente. Alertas fictícios e seus
  controles Revisar/Detalhes foram removidos, não implementados como alertas reais.
- Percentuais, saúde 98/100, eventos e tempos fixos removidos. Ausência de banco/serviço
  aparece como indisponível, não ausência confirmada de ocorrências.
- Erro no monitor invalida o estado online; não exibe contagem velha como atual nem
  indisponibilidade como zero pessoas. Contagens de câmeras sobrepostas não são somadas
  como ocupação única do ambiente.
- Navegação móvel deixa todas as seções acessíveis; botões têm nomes acessíveis.

## O que falta — não confundir formulário com cadastro

**Salvar câmera e Salvar ambiente estão desabilitados.** Não há escrita em memória,
sessionStorage, localStorage, arquivo ou banco feita pelos formulários. Validar campos
não fecha a janela nem cria registros. Rascunhos são descartados ao fechar.

A pergunta sobre existência/URL do projeto Supabase foi enviada ao usuário. Nenhuma
URL/chave foi inventada, nenhum projeto foi criado e nenhuma credencial foi solicitada
no chat. Após essa decisão, ainda será necessário implementar:

1. Schema/migrações, autenticação real e permissões de acesso verificadas.
2. API de ambientes/câmeras e salvamento/consulta com erros e conflito de atualização.
3. Coleção persistente de ambientes, inclusive vazios, separada da telemetria do monitor.
4. Gestão das fontes no servidor: registro salvo não implica câmera conectada.
5. Eventos reais, regras de alertas, revisão, consultas e exportação de relatórios.

Configurar `.env` sozinho não ativa os botões: ainda não há adaptador Supabase no código.
Login existente continua sendo somente uma sessão local; não concede permissões reais
no servidor. O perfil agora deixa essa limitação explícita.

## Evidência e limites

- `npm test`: build e 32 testes aprovados, incluindo 8 novos testes de formatação,
  virada do dia/ano, períodos, validações e ligação estrutural dos controles.
- `npm run lint` aprovado; type-check do conjunto de componentes alterados aprovado.
- Testes estruturais e de funções não equivalem a teste de cliques/teclado no navegador.
  Essa validação visual/interativa não foi executada nesta entrega.
- Testes e comandos executados no Conda `smart-environment`; base/.venv preservados.
- Nenhuma câmera/microfone foi aberta. Stream ST-01 e modelo/dataset não foram alterados.

Próxima validação após integrar persistência: criar ambiente vazio, salvar câmera,
recarregar o site, editar sem duplicar, receber nova telemetria sem perder configuração
e negar leitura/escrita de usuário sem autorização.
