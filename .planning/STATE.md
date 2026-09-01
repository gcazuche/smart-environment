# Estado GSD — Smart Environment

Atualizado em: 2026-08-27

- **Repositório:** `C:\Users\angel\OneDrive\Documents\Multicam`
- **Branch no início de SE-01:** `main`
- **Fundação técnica histórica:** concluída; código preservado
- **Checkpoint funcional atual:** dataset autorizado pré-rotulado; revisão humana pendente

## Posição atual

- **Etapa concluída:** SE-01 — Rebaseline Smart Environment
- **Etapa atual:** SE-04 — Ocupação e atividade observável
- **Plano atual:** `.planning/phases/se-04-activity-observation/STEP-03-AUTHORIZED-DATASET-SPEC.md`
- **Tarefa atual:** Etapa 3D gerou o piloto sem celular; corrigir as 33 anotações é o próximo gate
- **Autorização:** webcam e detecção local autorizadas pelo usuário em 2026-08-14
- **Plano antigo:** `.planning/phases/02-database/` superado e somente histórico

## Resultado de SE-01

- Produto redefinido como gestão inteligente de ambientes.
- MVP fixado em uma webcam, frames transitórios, contagem sem identificação, evento
  agregado, Supabase e dashboard web.
- “Desempenho” limitado ao ambiente; distração/produtividade individual excluídas.
- Reconhecimento facial, embeddings, pgvector, vivacidade e PySide6 retirados do baseline.
- Roadmap incremental, requisitos, riscos, testes, stack e ADRs realinhados.
- Nenhum código funcional, dependência, banco, câmera ou serviço externo foi alterado.

## Mudança de direção em 2026-08-14

- O usuário esclareceu que “desempenho” inclui estimar se a pessoa aparenta estar
  trabalhando ou relaxando.
- A primeira implementação foi antecipada para webcam e detecção de pessoas antes de
  Supabase; atividade observável permanece para SE-04.
- A classificação terá estado `inconclusivo`, regras por contexto e uso não punitivo.
- Por decisão do usuário, a melhoria do detector foi pausada após o primeiro protótipo;
  o dashboard visual foi antecipado e a detecção será retomada depois.

## O que funciona hoje

- Ambiente Conda isolado `smart-environment` com Python 3.12.13 e `environment.yml`;
  nenhum comando de instalação desta migração foi direcionado ao `base`.
- Configuração mínima, comando `doctor`, logging JSON seguro e tratamento de exceções.
- OpenCV/NumPy fixados; câmera com fallback, CLI e detectores NanoDet/Intel substituíveis.
- 115 testes e 11 subtestes aprovados em Python 3.12, junto com Ruff e mypy strict.
- O smoke NanoDet via DirectShow processou 30 frames em memória, observou máximo de uma
  pessoa e liberou a câmera; qualidade ampla e estabilidade temporal seguem pendentes.
- A contagem inspecionada em `data/` permaneceu 5 antes e depois.
- Intel YOLO26n FP16/OpenVINO detectou duas pessoas na amostra indicada pela Intel, com
  média de 32,1 ms; NanoDet retornou três caixas e média de 90,1 ms na mesma imagem.
- Contrato Python imutável define os cinco estados observáveis e os limiares iniciais
  do cenário `office-computer`, sem abrir câmera, identificar pessoas ou classificar frames.
- Cada câmera aceita uma área retangular normalizada independente; a prévia local desenha
  a região e a API mantém apenas geometria e contagem espacial agregada em memória.
- Três imagens reais de escritórios ocupados foram revisadas visualmente e preparadas com
  origem, licença CC-BY-NC-SA-4.0, metadados e hashes fixados, fora do Git.
- O YOLO26/OpenVINO foi restringido a laptop, mouse, teclado e celular e executado somente
  nessas referências: dois laptops corretos, zero celulares e média de 43,2 ms por imagem.
  O diagnóstico em limiar 0,10 também não encontrou o celular; nenhuma atividade foi criada.
- Seis cenas sintéticas provisórias, sem rostos ou pessoas reais, foram fixadas por hash.
  No limiar 0,25, laptop apareceu nas 4 cenas esperadas e celular em 3/4; a cena ambígua
  perdeu o celular e criou uma caixa duplicada/falsa de laptop. Média: 41,4 ms por imagem.
  Em 0,10 o quarto celular apareceu junto de novos falsos sinais; o limiar não foi reduzido.
- As 62 fotos autorizadas foram reencodadas com nomes neutros, metadados removidos,
  66 regiões faciais, 166 zonas de cabeça e 64 telas redigidas; não há celular real nem
  classe de celular nesta versão. O original permaneceu intocado.
- Oito rajadas visuais foram mantidas inteiras por split e 33 frames representativos
  formam o piloto YOLO: 22 treino, 5 validação e 6 teste. Os pré-rótulos sugerem 27
  pessoas, 2 laptops, 12 mouses e 21 teclados, sempre com revisão obrigatória.
- Integridade confirmou 62/62 hashes de origem, 33/33 derivados, JPEGs sem segmentos de
  metadados sensíveis e somente IDs YOLO 0–3. O manifest permanece
  `ready_for_training=false` e `human_privacy_reviewed=false`.
- O smoke simultâneo abriu a webcam por DirectShow e o celular por MJPEG privado; as
  duas fontes ficaram online e o Intel/OpenVINO detectou uma pessoa em cada leitura
  observada, sem persistir frames.
- Agente local processa a webcam e uma URL MJPEG/RTSP privada do celular em workers
  isolados e expõe contagem, estado, backend, latência e um JPEG anotado volátil por
  câmera em `127.0.0.1:8765`, aceito somente da página local.
- Dashboard responsivo em `dashboard/`, com duas câmeras, estados agregados locais,
  ambientes, indicadores e alertas; a visão geral concentra indicadores e eventos,
  enquanto a lista e os detalhes das câmeras ficam na seção dedicada; os gráficos
  históricos seguem simulados.
- A aba **Ambientes** agrupa dinamicamente as câmeras pelo ambiente retornado pelo agente;
  **Ver ambiente** abre o resumo agregado e a grade com todas as prévias daquele local,
  com acesso aos detalhes de cada dispositivo.
- Acesso do dashboard protegido por uma tela de login local demonstrativa; o perfil do
  administrador permite consultar a sessão e sair, sem armazenar senhas. A consulta das
  câmeras só começa depois do login.
- A marca visual usa um espaço reservado para a logo definitiva, e a interface não exibe
  referências a protótipo, contexto acadêmico ou demonstração.
- Build Vinext, lint ESLint e dois testes de renderização aprovados.
- Interface privada publicada em
  `https://smart-environment-monitor.angel-of-the-night16.chatgpt.site`.

## O que não existe

- Schema, migrações, projeto Supabase, Auth, RLS ou conexão PostgreSQL.
- Outbox SQLite, API remota, sincronização ou autenticação de produção da aplicação.
- Dataset representativo, métricas de falso sinal/latência e detector aprovado para produção;
  as referências públicas, sintéticas e o piloto autorizado servem somente para preparação
  e avaliação qualitativa enquanto as caixas não forem revisadas.
- Ground truth humano das 33 imagens; `laptop` tem somente dois pré-rótulos em treino e
  nenhum em validação/teste, então essa classe ainda não pode ser avaliada.
- Backend remoto/Supabase, autenticação, vídeo remoto e dados persistentes no dashboard
  publicado.
- Supabase Auth, expiração/revogação de sessão e permissões reais; o login atual é somente
  um fluxo local de demonstração para UX do TCC.
- Avaliação representativa das duas câmeras, alertas reais, ESP32, automação ou piloto.
- Calibração física ou seleção da área pelo dashboard, tracking, pose, objetos nas câmeras,
  agregação temporal e classificador de atividade.

## Bloqueios antes de dados reais

- finalidade detalhada, controlador, operadores de tratamento, encarregado e local autorizado;
- base legal/RIPD/avisos aplicáveis e áreas/horários permitidos;
- retenção, granularidade contra reidentificação e processo de direitos;
- região/plano/quotas/custo/backup/restore do Supabase;
- detector/pesos/licença acadêmica aberta e critérios de qualidade.

## Decisões abertas

- framework web e biblioteca de gráficos;
- escolha entre NanoDet e Intel/OpenVINO após métricas representativas;
- granularidade temporal/espacial do evento;
- estratégia Realtime versus polling;
- metas de FPS, latência, capacidade e custo;
- protocolo/modelos de câmeras futuras/ESP32;
- momento e estratégia para migrar o nome técnico `multicam`.

## Como retomar

1. Ler `REQUIREMENTS.md`, `ROADMAP.md`, `DECISIONS.md`, este arquivo e a especificação da SE-04.
2. Revisar as 33 prévias em `data/datasets/workstation-prelabels-v1/previews/`, removendo
   falsos positivos e adicionando objetos omitidos, especialmente laptops.
3. Manter `cell_phone` fora do mapa até existir coleta própria com exemplos positivos.
4. Não executar fine-tuning enquanto `ready_for_training=false`; manter pose, tracking,
   classificação e persistência fora deste incremento.
5. Confirmar a sincronização do OneDrive antes de afirmar que os derivados não saíram do PC.

## Prompt de retomada sugerido

> Continue a Etapa 3D de SEB-016: revise comigo as 33 imagens pré-rotuladas de pessoa,
> laptop, mouse e teclado, sem adicionar celular e sem iniciar o treinamento antes de
> aprovar o ground truth.
