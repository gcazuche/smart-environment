# Smart Environment — continuidade do projeto

## Antes de trabalhar

- Leia `.planning/STATE.md`, `README.md` e a especificação da etapa em andamento.
  Confira `git status` e o código: checkpoints antigos não comprovam o estado atual.
- Responda em português e explique escopo/arquivos antes de alterações materiais.
- Use o ambiente Conda `smart-environment`; não use `.venv` nem instale no `base`.
  No PowerShell prefira `conda run --no-capture-output -n smart-environment ...`.
- Preserve alterações preexistentes. Não reverta, exclua ou inclua arquivos alheios
  à etapa. O arquivo não rastreado `h origin main` pertence ao usuário.

## Limites permanentes

- Não exponha credenciais, `.env.local`, tokens ou fotos em Git, chat ou logs.
- Não reinicie bootstrap do banco nem crie organização duplicada para instalar outro PC.
- Não abra câmeras, implante na VM ou altere dados remotos fora do pedido autorizado.
- Separe vídeo de análise: 720p/30 FPS é meta de transporte a medir; inferência CPU
  tem frequência própria. Teste local não comprova desempenho na VM Hyper-V.
- Não deduza intenção, emoção ou produtividade pela aparência. Presença/proximidade
  de computador não prova trabalho; falha/ambiguidade deve continuar desconhecida.
- Celular está fora da fase atual de dados/treinamento. Não treine nas fotos privadas
  antes da revisão humana de anotações, privacidade e autorização documentadas.
- Imagens da internet exigem origem/licença/hash registrados. Previsões do modelo
  e títulos das imagens não são rótulos verdadeiros nem medidas de acurácia.

## Validação e versões

- Prefira testes/lint/tipos existentes; relate exatamente o que executou e seus limites.
- Não crie commit/tag/push automaticamente. Avise quando houver marco adequado e
  ofereça comandos revisáveis; nunca mova/substitua uma tag existente.
- Consulte tags atuais antes de propor número de versão. Em 15/09/2026, as tags
  locais v0.1.0 e v0.2.0 apontavam para f5b1f18; mudanças posteriores estavam locais.
- Atualize o checkpoint ao encerrar. Estes arquivos levam contexto entre máquinas,
  mas não são uma exportação das mensagens ou memórias internas do aplicativo.
