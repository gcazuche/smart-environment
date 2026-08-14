# SE-02 — Contexto da câmera e detecção local

Data: 2026-08-14
Status: em andamento

## Objetivo autorizado

Usar a webcam do próprio computador para capturar frames em memória, detectar pessoas,
desenhar caixas e mostrar a contagem em uma janela local.

## Entradas normalizadas

- **Repositório:** snapshot local em `C:\Users\angel\OneDrive\Documents\Multicam`.
- **Stack:** Python 3.11/3.12, OpenCV, NumPy e CLI local.
- **Nível de segurança:** alto por envolver câmera e ambiente de trabalho.
- **Compliance:** LGPD relevante; PoC limitado ao próprio responsável autorizado.
- **Entregável:** protótipo local executável e testado.
- **Ambiente:** Windows; webcam integrada índice 0; DirectShow funcionou no spike anterior.
- **Testes ativos:** webcam local autorizada em 2026-08-14; nenhum DAST autorizado.

## Dentro do escopo

- fonte simulada para testes;
- lifecycle abrir/ler/liberar com fallback seguro de backend;
- detector substituível e CPU-first;
- caixas, contagem, instrução de saída e resumo sanitizado;
- modo limitado sem janela para smoke automatizado;
- nenhuma escrita de imagem, banco ou rede.

## Fora do escopo

- classificar trabalhando/relaxando nesta etapa;
- identidade, rosto, emoção, intenção ou tracking persistente;
- Supabase, API, dashboard web, arquivos de vídeo ou snapshots;
- múltiplas câmeras, RTSP/ESP32, GPU e alegação de precisão.

## Invariantes

1. Frame existe apenas em memória e não aparece em log/erro.
2. A câmera é liberada em sucesso, falha, `q`, Esc ou interrupção.
3. Modo sem janela exige limite de frames para não rodar invisivelmente sem fim.
4. Falha de câmera/detector não é interpretada como ambiente vazio.
5. Teste real não envolve terceiros incidentais.

## Critérios de conclusão

- testes simulados cobrem 0/1/N, abertura, leitura, erro e liberação;
- CLI possui comando documentado e erros públicos seguros;
- smoke real limitado abre, lê e libera a webcam sem persistência;
- janela local pode exibir caixas/contagem e fechar por `q`/Esc;
- gates Python passam e limitações do detector são documentadas.
