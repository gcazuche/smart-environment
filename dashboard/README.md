# Dashboard Smart Environment

Interface web responsiva para visualizar câmeras, ambientes, ocupação, indicadores e
alertas do Smart Environment.

Esta primeira versão usa somente dados simulados. Ela não acessa a webcam, não envia
frames e não se conecta ao Supabase.

## Executar localmente

```powershell
npm install
npm run dev
```

Acesse `http://localhost:3000`.

## Validar

```powershell
npm run lint
npm test
```

O build de produção é executado pelo próprio `npm test`.

## Áreas disponíveis

- visão geral com indicadores e atividade recente;
- lista de todas as câmeras e detalhes da webcam principal;
- cadastro visual de webcam, câmera IP e gateway ESP32;
- ambientes monitorados;
- ocupação e sustentabilidade;
- alertas com linguagem de revisão humana.
