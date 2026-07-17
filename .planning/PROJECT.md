# Multicam Inteligente

## Visão

Plataforma modular de câmeras autorizadas capaz de cadastrar pessoas, executar
reconhecimento facial local, registrar eventos auditáveis e sincronizar clientes
com um servidor central sem depender da rede a cada frame.

## Problema

Soluções monolíticas de vídeo costumam misturar captura, inferência, interface e
persistência. Isso aumenta o impacto de uma câmera defeituosa, dificulta testes e
torna perigoso o tratamento de biometria. Este projeto separa essas responsabilidades
e adota privacidade e segurança desde a especificação.

## Objetivo

Entregar um sistema real, executável e verificável que:

- isole falhas por câmera;
- reconheça somente acima de um limiar calibrado;
- trate correspondências incertas como desconhecidas;
- opere temporariamente offline com sincronização idempotente;
- aplique autenticação, autorização, auditoria e retenção;
- mantenha contexto GSD persistente e evidência dos testes.

## Público autorizado

Administradores, operadores e visualizadores previamente autorizados pela
organização controladora dos dados. O uso pressupõe finalidade legítima, base legal
avaliada, transparência e controles compatíveis com a LGPD.

## Escopo

- Fontes USB, webcam integrada, RTSP/IP, arquivos e câmeras simuladas.
- Cadastro guiado com 10 a 100 imagens e validação de qualidade.
- Motor facial substituível, CPU-first e GPU opcional.
- Eventos de conhecidos e desconhecidos com deduplicação temporal.
- Cliente local, API central, PostgreSQL/pgvector e cache/fila local.
- Interface PySide6 sem trabalho pesado na thread gráfica.
- RBAC, escopo por câmera/local, auditoria, alertas e exportação.
- Operação offline temporária e sincronização idempotente.

## Primeira versão

A primeira versão utilizável será uma vertical local e autorizada:

1. execução em um computador;
2. uma a quatro fontes simultâneas, incluindo fonte simulada;
3. cadastro, embeddings, reconhecimento e desconhecidos;
4. PostgreSQL central local e cache/fila SQLite no cliente;
5. login com papéis administrador, operador e visualizador;
6. painel PySide6 básico, histórico e auditoria;
7. API local segura e contratos preparados para distribuição;
8. testes automatizados sem exigir câmera física.

Escala, sistema operacional alvo, GPU, quantidade de identidades e retenção ainda
estão `unspecified`; os números acima são premissas provisórias, não limites finais.

## Funcionalidades futuras

- Vários computadores clientes e alta disponibilidade do servidor.
- Balanceamento de inferência entre dispositivos.
- Anti-spoofing por modelo especializado e sensores de profundidade.
- Notificações externas, sempre desativadas por padrão.
- Empacotamento e atualização assinada.

## Restrições

- Python 3.11 ou superior; Python 3.12 é a referência inicialmente validável.
- CPU deve ser suportada; GPU não pode ser requisito.
- Nenhuma consulta remota por frame.
- Nenhuma biometria real ou segredo entra no Git.
- Nenhuma alegação de acurácia ou vivacidade sem avaliação representativa.
- Teste em hardware real depende do usuário e será documentado separadamente.

## Premissas

- Uso inicial: 1–4 câmeras em rede local (`unspecified`, aguardando confirmação).
- Crescimento e volume de pessoas: `unspecified`.
- PostgreSQL local como padrão inicial; Supabase permanece alternativa.
- Modo offline é obrigatório e a fila local usa identificadores idempotentes.
- HTTPS é terminado em proxy confiável no ambiente distribuído.

## Privacidade

Biometria é dado pessoal sensível. A arquitetura prioriza minimização, separação de
identificadores, criptografia em trânsito, proteção em repouso conforme o ambiente,
retenção configurável, acesso mínimo, auditoria e eliminação verificável. A base legal,
o RIPD e os avisos aplicáveis devem ser confirmados pelo controlador e por assessoria
jurídica; este projeto não substitui aconselhamento jurídico.

## Definição de sucesso

- Critérios dos requisitos da versão são rastreados a testes/evidências.
- Uma câmera com falha não interrompe as demais nem a interface.
- Limiar rejeita correspondências insuficientes; testes positivos e negativos existem.
- Eventos offline são reenviados sem duplicação após reconexão.
- Ações privilegiadas e acessos sensíveis deixam trilha de auditoria.
- Não existem findings críticos conhecidos sem tratamento ou aceitação explícita.
- Instalação, operação, backup, restauração e exclusão são documentados.

## Fora do escopo

- Identificação secreta ou sem autorização.
- Busca em redes sociais ou bases obtidas irregularmente.
- Rastreamento fora das câmeras cadastradas.
- Compartilhamento automático de biometria com terceiros.
- Vigilância pública indiscriminada, decisões automatizadas punitivas ou garantia de
  vivacidade inviolável.
