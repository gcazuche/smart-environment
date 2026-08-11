# SE-01 — Contexto do rebaseline Smart Environment

Data: 2026-08-11
Tipo: documentação e planejamento
Risco do produto: alto, por câmeras em ambiente de trabalho

## Pedido confirmado

Reorientar o projeto para um ambiente inteligente com monitoramento de ocupação,
sustentabilidade, recursos e patrimônio; usar HTML, CSS, JavaScript, Python, OpenCV e
banco de dados, inicialmente Supabase. O trabalho deve ocorrer parte por parte e, nesta
entrada, somente a Etapa 1 foi autorizada.

## Resultado permitido nesta etapa

- inventariar o checkpoint anterior;
- preservar fundação técnica e evidência válida;
- redefinir visão, MVP, arquitetura, requisitos, riscos e roadmap;
- registrar limites de privacidade e segurança;
- marcar planos incompatíveis como históricos/superados;
- explicar o plano futuro sem iniciar outra etapa.

## Fora desta etapa

- alterar código Python, `pyproject.toml`, `uv.lock`, `.env.example` ou dados;
- abrir a webcam ou executar captura adicional;
- instalar OpenCV/modelo, criar schema ou banco;
- criar/conectar projeto Supabase ou usar credenciais;
- construir API, HTML, CSS, JavaScript, dashboard ou automação;
- testar pessoas, enviar mensagens ou publicar/deployar qualquer artefato.

## Base preservada

- Python 3.11/3.12, `uv.lock`, build e gates;
- configuração mínima, `doctor`, logging seguro e exceções;
- 28 testes no checkpoint anterior;
- smoke autorizado de um frame da webcam em memória;
- princípio de borda + serviço central, filas limitadas e idempotência.

## Base superada

- reconhecimento facial como produto central;
- cadastro de pessoas, embeddings, matching, desconhecidos e vivacidade;
- pgvector/FAISS e Storage de frames no baseline;
- PySide6 como interface;
- antiga Fase 2 SQLite/biometria como próxima execução.

## Premissas normalizadas

- **Repositório:** snapshot local em Windows.
- **Hardware inicial:** uma webcam integrada já identificada; não reaberta nesta etapa.
- **Stack desejada:** HTML/CSS/JavaScript, Python, OpenCV e Supabase.
- **Conectividade:** internet preferencial; resiliência local futura.
- **Entrega:** TCC planejado com postura de eventual uso comercial.
- **Privacidade:** LGPD relevante; base legal, controlador, operadores, encarregado,
  RIPD, retenção, granularidade e avisos permanecem `unspecified`.
- **Scans ativos/DAST:** não autorizados nem necessários para a etapa documental.

## Decisão central

“Desempenho” passa a significar desempenho operacional do ambiente. O MVP mede
ocupação sem identificar pessoas e não infere distração, atenção, emoção, produtividade,
jornada ou conduta. Frames são efêmeros; persistem somente eventos minimizados.

## Critérios de conclusão

1. Documentos ativos descrevem o mesmo MVP e a mesma sequência.
2. Requisitos possuem ID, fase, prioridade, dependência, aceite e estado.
3. Incertezas não são apresentadas como decisões ou validações.
4. Plano anterior está inequivocamente superado, sem apagar evidência histórica.
5. Nenhuma mudança funcional, dependência, dado, câmera ou serviço ocorre.
6. Links e rastreabilidade passam por revisão; gates da fundação continuam verdes.
