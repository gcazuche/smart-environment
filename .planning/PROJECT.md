# Smart Environment

Atualizado em: 2026-08-11
Estado: visão revalidada na Etapa SE-01

## Visão

O Smart Environment é uma plataforma para compreender e melhorar o uso de ambientes
de trabalho. O sistema combina uma câmera autorizada, processamento local com visão
computacional, uma API Python, Supabase e uma interface web para apresentar ocupação,
sustentabilidade, recursos, patrimônio e alertas operacionais.

O projeto nasce como TCC, mas será planejado como produto comercial: dependências,
segurança, privacidade, operação e licenças precisam suportar esse cenário, sem alegar
que um piloto acadêmico já está pronto para produção.

## Problema

Empresas, escolas, escritórios e laboratórios frequentemente não possuem dados
confiáveis sobre horários de maior movimento, períodos de ociosidade dos espaços,
estado de equipamentos e situações fora do padrão. Isso dificulta decisões sobre
energia, capacidade, manutenção, segurança patrimonial e organização dos ambientes.

## Objetivo

Entregar, de forma incremental, um sistema que:

- informe ocupação atual e histórica por ambiente;
- produza indicadores operacionais e de sustentabilidade compreensíveis;
- permita cadastrar ambientes, câmeras e patrimônios autorizados;
- emita alertas configuráveis, auditáveis e sujeitos a revisão humana;
- ofereça acesso web autenticado por diferentes dispositivos;
- opere com minimização de dados, segurança por padrão e evidência de testes;
- evolua de uma webcam para múltiplas fontes sem reescrever o domínio central.

## Significado de desempenho

Neste projeto, **desempenho** inclui duas camadas diferentes:

1. desempenho operacional do ambiente: ocupação, disponibilidade, uso do espaço e
   oportunidades estimadas de redução de desperdício;
2. estado de atividade observável: estimativa visual de que uma pessoa aparenta estar
   em atividade compatível com trabalho, em pausa/relaxamento ou em estado inconclusivo.

A segunda camada não mede intenção, qualidade, produtividade real ou estado mental.
Usar celular, conversar ou permanecer parado pode ser trabalho dependendo do contexto.
As regras serão configuráveis por ambiente, os resultados serão estimativas e nenhuma
decisão disciplinar poderá ser tomada automaticamente.

## Público e partes afetadas

- **Administrador:** configura organização, ambientes, usuários e políticas.
- **Operador do sistema:** acompanha ocupação, dispositivos, alertas e patrimônio permitido.
- **Visualizador:** consulta painéis e relatórios dentro do próprio escopo.
- **Colaboradores e visitantes:** pessoas potencialmente observadas; são titulares de
  dados e não devem ser transformadas implicitamente em usuários ou suspeitos.
- **Gestores:** usam indicadores agregados para decisões operacionais, nunca como
  única base para decisões disciplinares ou efeitos relevantes sobre uma pessoa.

## MVP vertical

O primeiro produto utilizável terá este fluxo:

```text
1 webcam autorizada
  -> frames transitórios no computador
  -> detecção e contagem de pessoas sem identificação
  -> evento agregado de ocupação
  -> API Python e sincronização idempotente
  -> Supabase
  -> painel web HTML/CSS/JavaScript autenticado
```

Antes dessa vertical completa, a primeira prova local será menor: abrir a webcam,
detectar pessoas, desenhar caixas e exibir a contagem em tempo real, sem persistência.

O evento agregado descreve ambiente, câmera, janela de tempo, contagem ou estado de
ocupação e confiança técnica. Ele não contém nome, `person_id`, imagem, recorte de
rosto, embedding biométrico, áudio ou identificador persistente de trajetória.

## Pilares funcionais

1. **Ocupação:** situação atual, histórico, picos, períodos vazios e qualidade do
   dispositivo.
2. **Sustentabilidade:** horas-ocupação e oportunidades estimadas de reduzir consumo,
   com premissas visíveis e revisão humana.
3. **Recursos e patrimônio:** inventário, zonas, estados e movimentações autorizadas;
   alertas são indicativos e não acusatórios.
4. **Alertas e relatórios:** regras configuráveis, deduplicação, ciclo de vida,
   gráficos, filtros e exportações permitidas.
5. **Expansão:** múltiplas webcams, câmeras IP ou ESP32 por gateway autenticado depois
   que o MVP de uma câmera estiver medido e estável.

## Escopo da primeira versão

- Um computador Windows e exatamente uma webcam integrada como hardware real.
- Fonte simulada obrigatória para testes automatizados futuros.
- Processamento de vídeo na borda; a rede não participa de cada frame.
- Supabase como serviço central preferencial, sujeito a PoC de Auth, RLS, custo,
  região, backup e restauração.
- Painel responsivo no navegador; não haverá interface desktop PySide6 no baseline.
- Sugestões de sustentabilidade antes de qualquer automação física.
- Dados sintéticos até existir ambiente autorizado, aviso, política de retenção e
  decisão documentada sobre base legal.

## Fora do MVP

- Reconhecimento facial, cadastro de pessoas, embeddings, pgvector e vivacidade.
- Inferência de emoção, intenção, qualidade do trabalho ou produtividade real.
- Classificação de atividade usada como controle de ponto, ranking ou punição automática.
- Ranking de colaboradores ou decisão disciplinar automatizada.
- Áudio, gravação contínua, transmissão pública ao vivo ou armazenamento de frames.
- Declaração automática de furto ou culpa a partir de visão computacional.
- Acionamento autônomo de iluminação, ventilação, climatização ou sistema crítico.
- Múltiplas câmeras, RTSP, ESP32 e escala comercial antes do piloto de uma webcam.

Uma futura função de identificação individual só poderá entrar em uma fase opcional
se houver necessidade demonstrada, alternativa menos invasiva insuficiente, revisão
jurídica, transparência, governança, validação representativa, retenção definida,
controle de acesso, contestação e aprovação humana. Ela não é presumida pelo roadmap.

A classificação de atividade inicialmente usa apenas rastreamento temporário dentro da
sessão. Histórico associado a um colaborador identificado continua fora do MVP e exige
o mesmo gate reforçado de identificação individual.

## Privacidade e segurança

- Frames são efêmeros: permanecem em memória pelo tempo mínimo do processamento e não
  são enviados ao Supabase no baseline.
- Persistem apenas eventos agregados e minimizados.
- Acesso é negado por padrão e limitado por organização, local e papel.
- Credenciais privilegiadas permanecem somente no backend confiável.
- Retenção, exclusão, auditoria e direitos dos titulares devem ser verificáveis.
- Alertas exigem interpretação humana e contexto; ausência de detecção não prova
  ausência de uma pessoa e uma detecção não prova identidade ou conduta.
- LGPD é relevante ao contexto brasileiro. Base legal, controlador, operador, RIPD,
  avisos, retenção e encarregado permanecem decisões organizacionais `unspecified`;
  este projeto não substitui avaliação jurídica.

## Restrições e premissas

- Python 3.11 ou 3.12; CPU precisa ser suportada; GPU é opcional e não validada.
- HTML, CSS e JavaScript formam a interface; o protótipo usa React/TypeScript e Vinext.
- Python, OpenCV e banco de dados compõem o backend; o baseline híbrido HOG/upper-body
  ainda será comparado por desempenho e qualidade em dados autorizados.
- Internet é o meio preferencial, mas captura e agregação não podem parar por uma
  indisponibilidade transitória; a estratégia offline será implementada em fase própria.
- Modelos de câmera futuros, protocolos ESP32, volume, metas de FPS/latência, número
  de ambientes, retenção e orçamento do Supabase permanecem `unspecified`.
- O pacote e a CLI ainda usam o nome técnico legado `multicam`; renomear código,
  variáveis e caminhos será uma migração separada, não parte da Etapa SE-01.

## Definição de sucesso do MVP

- Uma webcam autorizada abre, entrega frames e é liberada repetidamente sem gravá-los.
- Cenários 0, 1 e N pessoas produzem eventos agregados com limitações documentadas.
- Queda de rede não bloqueia a captura e o reenvio não duplica eventos.
- Um usuário autenticado visualiza ocupação atual e histórica somente no seu escopo.
- Retenção e exclusão de eventos são demonstradas; nenhum pixel ou identidade persiste.
- Latência, disponibilidade e erro de contagem são medidos em piloto autorizado.
- Nenhum finding crítico conhecido fica sem contenção ou decisão explícita.

## Evidência preservada do projeto anterior

A fundação Python, configuração, logging seguro, lockfile, gates de qualidade e smoke
autorizado da webcam continuam válidos. O antigo planejamento de reconhecimento facial
é mantido apenas como histórico em Git e nos documentos de pesquisa identificados como
legado; ele não representa mais o produto ativo.
